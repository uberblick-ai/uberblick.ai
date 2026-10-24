// Plays the themed screen recordings on a page. A <video data-light data-dark>
// names one file per colour scheme; this loads the one that matches the page
// (the theme toggle, else the system preference), swaps it when the scheme
// changes and keeps the playback position. A video starts muted when it comes
// into view and pauses when it leaves, unless the reader prefers reduced motion,
// in which case it waits for the play button. Without this script the light
// file plays from the controls.
const videos = [...document.querySelectorAll("video[data-light][data-dark]")];
const dark = matchMedia("(prefers-color-scheme: dark)");
const calm = matchMedia("(prefers-reduced-motion: reduce)");
const scheme = () =>
	document.documentElement.dataset.theme || (dark.matches ? "dark" : "light");

function load(video) {
	const which = scheme();
	if (video.dataset.scheme === which) return;
	const at = video.currentTime;
	const playing = !video.paused;
	video.dataset.scheme = which;
	video.poster = video.dataset[`${which}Poster`] ?? video.poster;
	video.src = video.dataset[which];
	if (at)
		video.addEventListener(
			"loadedmetadata",
			() => {
				video.currentTime = at;
			},
			{ once: true },
		);
	if (playing) video.play().catch(() => {});
}
const swap = () => {
	for (const v of videos) load(v);
};

swap();
dark.addEventListener("change", swap);
new MutationObserver(swap).observe(document.documentElement, {
	attributeFilter: ["data-theme"],
});

const seen = new IntersectionObserver(
	(entries) => {
		for (const { target, isIntersecting } of entries) {
			if (isIntersecting && !calm.matches) target.play().catch(() => {});
			else if (!isIntersecting) target.pause();
		}
	},
	{ threshold: 0.5 },
);
for (const v of videos) seen.observe(v);
