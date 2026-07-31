/*! Keep the runtime console locked to the display card's dimensions. */
(function () {
  var device = document.querySelector(".play-area .device");
  var panel = document.querySelector(".play-area .console-panel");
  if (!device) {
    return;
  }

  var showConsole =
    new URLSearchParams(window.location.search).get("console") === "true";
  if (panel) {
    panel.hidden = !showConsole;
  }
  var standalone = window.parent === window;
  document.body.classList.add(standalone ? "runtime-standalone" : "runtime-embedded");
  document.body.classList.add(showConsole ? "runtime-with-console" : "runtime-without-console");

  var lastWidth = -1;
  var lastHeight = -1;

  function reportHeight() {
    requestAnimationFrame(function () {
      var main = document.querySelector(".loader-main");
      var height = Math.max(
        document.documentElement.scrollHeight,
        document.body.scrollHeight,
        main ? Math.ceil(main.getBoundingClientRect().bottom) : 0
      );
      if (window.parent !== window && height > 0) {
        var width = Math.ceil(device.getBoundingClientRect().width);
        window.parent.postMessage(
          { type: "pydisplay-runtime-size", height: height, width: width },
          window.location.origin
        );
      }
    });
  }

  function syncConsoleSize() {
    var rect = device.getBoundingClientRect();
    var width = Math.round(rect.width);
    var height = Math.round(rect.height);
    if (width <= 0 || height <= 0) {
      reportHeight();
      return;
    }
    if (!showConsole || !panel) {
      lastWidth = width;
      lastHeight = height;
      reportHeight();
      return;
    }
    if (standalone) {
      if (lastWidth < 0) {
        panel.style.width = width + "px";
        lastWidth = width;
      }
      if (height !== lastHeight) {
        panel.style.height = height + "px";
        lastHeight = height;
      }
      reportHeight();
      return;
    }
    if (width === lastWidth) {
      reportHeight();
      return;
    }
    lastWidth = width;
    lastHeight = height;
    panel.style.width = width + "px";
    panel.style.height = height + "px";
    reportHeight();
  }

  syncConsoleSize();
  window.addEventListener("resize", syncConsoleSize);
  window.addEventListener("load", reportHeight);
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(syncConsoleSize).observe(device);
  }
})();
