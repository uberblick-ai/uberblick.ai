// A screen recording comes as a light and a dark <video> (.l and .d in a
// .shot), and the stylesheet shows the one that matches the theme. Neither
// plays on its own. When the theme changes while one plays, this pauses the
// one that just went out of sight.
const videos = [...document.querySelectorAll(".shot video")];
const pauseHidden = () => {
	for (const v of videos) if (v.offsetParent === null) v.pause();
};

matchMedia("(prefers-color-scheme: dark)").addEventListener(
	"change",
	pauseHidden,
);
new MutationObserver(pauseHidden).observe(document.documentElement, {
	attributeFilter: ["data-theme"],
});
