// Draws the diagram examples on a page in the browser from the source in
// their Source tab, so the drawing is always the renderer's current work and
// never a screenshot. A `.tabs.ex[data-diagram]` block names its format:
// "ablauf" draws with /js/ablauf.js (the renderer the editor uses, with the
// page's own monospace face measured on a canvas, as the editor does) and
// "mermaid" with Mermaid itself, loaded from its package on jsDelivr when the
// page has one. Both follow the colour scheme and redraw when it changes.
const MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@12.1.0/dist/mermaid.esm.min.mjs";
const MONO = "IBM Plex Mono";
const blocks = [...document.querySelectorAll(".tabs.ex[data-diagram]")];

const scheme = () =>
	document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
const source = (box) => box.querySelector("pre").textContent.replace(/^```\w*\n/, "").replace(/\n```\s*$/, "");
const adopt = (box, svg, asHtml = false) => {
	// ablauf escapes what comes from the source, so its drawing is parsed as SVG, never as HTML.
	// Mermaid's drawing carries HTML labels and is sanitised by Mermaid itself; it parses as HTML.
	const root = asHtml
		? Object.assign(document.createElement("template"), { innerHTML: svg }).content.querySelector("svg")
		: new DOMParser().parseFromString(svg, "image/svg+xml").documentElement;
	if (root?.localName !== "svg") throw new Error("not an SVG");
	box.querySelector(".pic").replaceChildren(document.importNode(root, true));
};
const failed = (box, why) => {
	const p = document.createElement("p");
	p.className = "small";
	p.textContent = why;
	box.querySelector(".pic").replaceChildren(p);
};

let ablauf;
let measure;
let mermaid;
async function drawAblauf(box, n) {
	ablauf ??= await import("/js/ablauf.js");
	if (!measure) {
		await document.fonts.load(`13px "${MONO}"`);
		await document.fonts.ready;
		const ctx = document.createElement("canvas").getContext("2d");
		measure = (text, style) => {
			ctx.font = `${style.fontWeight} ${style.fontSize}px "${MONO}"`;
			return ctx.measureText(text).width;
		};
	}
	const { svg, diagnostics } = ablauf.render(source(box), {
		idPrefix: `ab${n}`,
		scheme: scheme(),
		fonts: { mono: { family: MONO, measureText: measure } },
	});
	for (const d of diagnostics) console.warn(`ablauf line ${d.line}: ${d.message}`);
	adopt(box, svg);
}
async function drawMermaid(box, n) {
	mermaid ??= (await import(MERMAID)).default;
	mermaid.initialize({
		startOnLoad: false,
		securityLevel: "strict",
		theme: scheme() === "dark" ? "dark" : "default",
		fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
	});
	const { svg } = await mermaid.render(`mm${n}-${Date.now()}`, source(box));
	adopt(box, svg, true);
}

let pass = 0;
function draw() {
	const run = ++pass;
	blocks.forEach((box, n) => {
		const kind = box.dataset.diagram;
		const job = kind === "ablauf" ? drawAblauf(box, n) : kind === "mermaid" ? drawMermaid(box, n) : Promise.reject(new Error(kind));
		job.catch((e) => {
			if (run === pass) failed(box, `The drawing could not be made here (${e.message}). The source is in the next tab.`);
		});
	});
}
// Expand opens one drawing in a full-screen viewer at its natural size, as the editor's expanded block does.
const viewer = document.createElement("dialog");
viewer.className = "dviewer";
viewer.innerHTML = '<div class="dvbar"><span class="dvtitle"></span><button type="button" class="dvclose">Close</button></div><div class="dvport"></div>';
document.body.append(viewer);
viewer.querySelector(".dvclose").addEventListener("click", () => viewer.close());
viewer.addEventListener("click", (e) => { if (e.target === viewer) viewer.close(); });
for (const b of document.querySelectorAll(".tabs.ex .dexpand")) {
	b.addEventListener("click", () => {
		const box = b.closest(".tabs.ex");
		const svg = box.querySelector(".pic svg");
		if (!svg) return;
		viewer.querySelector(".dvtitle").textContent = box.querySelector('[role="tab"]').textContent;
		viewer.querySelector(".dvport").replaceChildren(svg.cloneNode(true));
		viewer.showModal();
	});
}
if (blocks.length) {
	draw();
	matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
	new MutationObserver(draw).observe(document.documentElement, { attributeFilter: ["data-theme"] });
}
