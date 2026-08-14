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
  var LOGO = "https://pydevices.github.io/img/logo.svg";
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
    '<button type="button" class="btn js-open-tree-modal" style="padding: 5px 12px; font-size: 0.85rem;" title="Explore ecosystem tree navigation">' +
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg> Tree View' +
    '</button>' +
    '<a href="' +
    ROOT +
    '/pydevices/">Core Stack</a>' +
    '<a href="' +
    ROOT +
    '/pygraphics/">Toolkits</a>' +
    '<a href="' +
    ROOT +
    '/displayif/">Native C</a>' +
    '<a href="' +
    ROOT +
    '/pydevices-examples/pyscript/">Gallery</a>' +
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

  var TREE_MODAL_HTML =
    '<div class="tree-modal-backdrop" id="pydevices-tree-modal-backdrop">' +
    '<div class="tree-modal" role="dialog" aria-modal="true" aria-label="Ecosystem Tree Navigation">' +
    '<div class="tree-modal-header">' +
    '<h3>PyDevices Ecosystem Tree</h3>' +
    '<button type="button" class="tree-modal-close" id="pydevices-tree-modal-close" aria-label="Close modal">&times;</button>' +
    '</div>' +
    '<div class="tree-modal-body">' +
    '<div class="tree-container" style="border:none; box-shadow:none; padding:0; margin:0;">' +
    '<div class="tree-header">' +
    '<div class="tree-search-wrap" style="max-width:100%;">' +
    '<svg class="tree-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>' +
    '<input type="text" class="tree-search" placeholder="Filter repositories, runtimes, modules...">' +
    '</div>' +
    '</div>' +
    '<div class="tree-view">' +
    '<div class="tree-branch open">' +
    '<div class="tree-branch-header"><svg class="tree-toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg> 📁 1: Core Platform & Board Contract</div>' +
    '<div class="tree-branch-children">' +
    '<a class="tree-leaf" href="https://pydevices.github.io/pydevices/"><span class="tree-leaf-name">pydevices</span><span class="tag tag-tier-1">Core Board Contract</span></a>' +
    '<a class="tree-leaf" href="https://pydevices.github.io/displayif/"><span class="tree-leaf-name">displayif</span><span class="tag tag-tier-1">C Bus Interface</span></a>' +
    '<a class="tree-leaf" href="https://pydevices.github.io/pydevices-examples/"><span class="tree-leaf-name">pydevices-examples</span><span class="tag tag-tier-1">Showcase & Demos</span></a>' +
    '</div>' +
    '</div>' +
    '<div class="tree-branch open">' +
    '<div class="tree-branch-header"><svg class="tree-toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg> 📁 2: Pure-Python & Portable Toolkits</div>' +
    '<div class="tree-branch-children">' +
    '<a class="tree-leaf" href="https://pydevices.github.io/pygraphics/"><span class="tree-leaf-name">pygraphics</span><span class="tag tag-tier-2">2D FrameBuffer</span></a>' +
    '<a class="tree-leaf" href="https://pydevices.github.io/pdwidgets/"><span class="tree-leaf-name">pdwidgets</span><span class="tag tag-tier-2">UI Toolkit</span></a>' +
    '<a class="tree-leaf" href="https://pydevices.github.io/palettes/"><span class="tree-leaf-name">palettes</span><span class="tag tag-tier-2">Color Engine</span></a>' +
    '</div>' +
    '</div>' +
    '<div class="tree-branch open">' +
    '<div class="tree-branch-header"><svg class="tree-toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg> 📁 3: LVGL Native Extensions & Binding Generator</div>' +
    '<div class="tree-branch-children">' +
    '<a class="tree-leaf" href="https://pydevices.github.io/lvgl-bindings/"><span class="tree-leaf-name">lvgl-bindings</span><span class="tag tag-tier-3">LVGL Generator</span></a>' +
    '<a class="tree-leaf" href="https://pydevices.github.io/lvgl-micropython/"><span class="tree-leaf-name">lvgl-micropython</span><span class="tag tag-tier-3">MicroPython C</span></a>' +
    '<a class="tree-leaf" href="https://pydevices.github.io/lvgl-python/"><span class="tree-leaf-name">lvgl-python</span><span class="tag tag-tier-3">CPython / WASM</span></a>' +
    '<a class="tree-leaf" href="https://pydevices.github.io/lvgl-circuitpython/"><span class="tree-leaf-name">lvgl-circuitpython</span><span class="tag tag-tier-3">CircuitPython C</span></a>' +
    '</div>' +
    '</div>' +
    '<div class="tree-branch open">' +
    '<div class="tree-branch-header"><svg class="tree-toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg> 📁 4: Target App Hosts & PWAs</div>' +
    '<div class="tree-branch-children">' +
    '<a class="tree-leaf" href="https://pydevices.github.io/pydevices-pyscript-template/"><span class="tree-leaf-name">pyscript-template</span><span class="tag tag-tier-4">PWA Template</span></a>' +
    '<a class="tree-leaf" href="https://pydevices.github.io/pydevices-android-template/"><span class="tree-leaf-name">android-template</span><span class="tag tag-tier-4">Android APK</span></a>' +
    '</div>' +
    '</div>' +
    '<div class="tree-branch open">' +
    '<div class="tree-branch-header"><svg class="tree-toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg> 📁 5: Developer Tools & Infrastructure</div>' +
    '<div class="tree-branch-children">' +
    '<a class="tree-leaf" href="https://pydevices.github.io/micropython-lib/"><span class="tree-leaf-name">micropython-lib</span><span class="tag tag-tier-5">PyDevices MIP Index</span></a>' +
    '<a class="tree-leaf" href="https://pydevices.github.io/cmods/"><span class="tree-leaf-name">cmods</span><span class="tag tag-tier-5">Build Workspace</span></a>' +
    '<a class="tree-leaf" href="https://pydevices.github.io/mpftp/"><span class="tree-leaf-name">mpftp</span><span class="tag tag-tier-5">REPL / Transfer Tool</span></a>' +
    '</div>' +
    '</div>' +
    '</div>' +
    '</div>' +
    '</div>' +
    '</div>' +
    '</div>';

  function inject() {
    var headerMount = document.getElementById("pydevices-site-header");
    var footerMount = document.getElementById("pydevices-site-footer");
    if (headerMount) {
      headerMount.outerHTML = HEADER;
    }
    if (footerMount) {
      footerMount.outerHTML = FOOTER;
    }
    if (!document.getElementById("pydevices-tree-modal-backdrop")) {
      document.body.insertAdjacentHTML("beforeend", TREE_MODAL_HTML);
    }
    if (!document.querySelector('script[src*="tree-nav.js"]')) {
      var script = document.createElement('script');
      script.src = ROOT + '/vendor/pydevices-chrome/tree-nav.js';
      document.head.appendChild(script);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inject);
  } else {
    inject();
  }
})();
