// Tooltips are shown on hover purely via CSS (see .tip / .tip-bubble).
// This script only adds tap/click support so the same tooltip markup works
// reasonably on trackpads/touchscreens without needing a hover state.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".tip").forEach(function (tip) {
    tip.addEventListener("click", function (e) {
      e.stopPropagation();
      var bubble = tip.querySelector(".tip-bubble");
      if (!bubble) return;
      var isOpen = bubble.style.display === "block";
      document.querySelectorAll(".tip-bubble").forEach(function (b) { b.style.display = "none"; });
      bubble.style.display = isOpen ? "none" : "block";
    });
  });
  document.addEventListener("click", function () {
    document.querySelectorAll(".tip-bubble").forEach(function (b) { b.style.display = "none"; });
  });
});
