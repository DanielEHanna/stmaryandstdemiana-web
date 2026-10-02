// Progressive enhancement only: every page works with JavaScript disabled.
// The menu is a native <details>, so it already opens and closes without
// script; this adds what <details> lacks: Escape closes it and returns focus.
// Nothing here measures or reacts to the viewport size.
(function () {
  "use strict";

  function closeMenuOnEscape(menu) {
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && menu.open) {
        menu.open = false;
        menu.querySelector("summary").focus();
      }
    });
  }

  var menu = document.querySelector(".sm-menu");
  if (menu) {
    closeMenuOnEscape(menu);
  }
})();
