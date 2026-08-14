/*
 * PyDevices — shared dark/light theme toggle
 *
 * Pairs with the `data-theme` attribute in assets/css/site.css. Dark is the
 * default (no attribute); "light" is opt-in and persisted in localStorage.
 *
 * Pages that render a `#theme-toggle` button should also inline this
 * snippet at the very top of <head>, before any stylesheet, so a returning
 * light-theme visitor doesn't see a flash of dark on load:
 *
 *   <script>try{if(localStorage.getItem('pydevices-theme')==='light'){document.documentElement.setAttribute('data-theme','light');}}catch(e){}</script>
 *
 * Canonical copy: https://pydevices.github.io/assets/js/theme-toggle.js
 */
(function () {
  var STORAGE_KEY = "pydevices-theme";
  var root = document.documentElement;

  function currentTheme() {
    return root.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function applyTheme(theme) {
    if (theme === "light") {
      root.setAttribute("data-theme", "light");
    } else {
      root.removeAttribute("data-theme");
    }
  }

  function init() {
    var toggle = document.getElementById("theme-toggle");
    if (!toggle) {
      return;
    }
    toggle.addEventListener("click", function () {
      var next = currentTheme() === "light" ? "dark" : "light";
      applyTheme(next);
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch (e) {
        /* localStorage unavailable (private mode, etc.) — toggle still works this visit */
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
