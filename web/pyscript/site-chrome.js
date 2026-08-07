/*
 * PyDevices — shared site header + footer
 *
 * Injects identical chrome into pages that provide mount points:
 *   <div id="pydevices-site-header"></div>
 *   ...
 *   <div id="pydevices-site-footer"></div>
 *   <script src="https://pydevices.github.io/assets/js/site-chrome.js"></script>
 *   <script src="https://pydevices.github.io/assets/js/theme-toggle.js"></script>
 *
 * Load this script before theme-toggle.js so #theme-toggle exists when the
 * toggle binds. Canonical copy:
 *   https://pydevices.github.io/assets/js/site-chrome.js
 */
(function () {
  var LOGO = "https://pydevices.github.io/assets/img/logo.svg";
  var ROOT = "https://pydevices.github.io";

  var HEADER =
    '<header class="site-header">' +
    '<div class="wrap">' +
    '<a class="brand" href="' +
    ROOT +
    '/">' +
    '<span class="logo"><img src="' +
    LOGO +
    '" alt="" width="30" height="30"></span>' +
    "PyDevices" +
    "</a>" +
    '<nav class="nav">' +
    '<a href="' +
    ROOT +
    '/pydisplay/pyscript/">Gallery</a>' +
    '<a href="' +
    ROOT +
    '/pydisplay/">PyDisplay</a>' +
    '<a href="' +
    ROOT +
    '/displayif/">DisplayIF</a>' +
    '<a href="' +
    ROOT +
    '/micropython-hardware/">Drivers</a>' +
    '<a href="https://github.com/PyDevices">GitHub</a>' +
    "</nav>" +
    '<button type="button" class="theme-toggle" id="theme-toggle" aria-label="Toggle color theme" title="Toggle color theme">' +
    '<svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>' +
    '<svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>' +
    "</button>" +
    "</div>" +
    "</header>";

  var FOOTER =
    '<footer class="site-footer">' +
    '<div class="wrap">' +
    "<span>&copy; 2026 PyDevices &middot; MIT License</span>" +
    '<span><a href="https://github.com/PyDevices">github.com/PyDevices</a></span>' +
    "</div>" +
    "</footer>";

  function inject() {
    var headerMount = document.getElementById("pydevices-site-header");
    var footerMount = document.getElementById("pydevices-site-footer");
    if (headerMount) {
      headerMount.outerHTML = HEADER;
    }
    if (footerMount) {
      footerMount.outerHTML = FOOTER;
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inject);
  } else {
    inject();
  }
})();
