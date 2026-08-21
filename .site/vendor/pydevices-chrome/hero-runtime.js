/**
 * hero-runtime.js — Pyodide background runtime for PyDevices hero canvas apps.
 *
 * Bootstraps Pyodide in the background, installs wheel dependencies from TestPyPI via micropip,
 * uses portable mip.py to fetch the standalone .py app from https://PyDevices.github.io/assets/apps/,
 * and mounts the app seamlessly into the 240x240 hero canvas.
 */

(function () {
  const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.5/full/";
  const INDEX_URLS = [
    "https://test.pypi.org/simple/{package_name}/",
    "https://pypi.org/simple/{package_name}/"
  ];

  let pyodidePromise = null;

  async function getPyodide(onStatus) {
    if (pyodidePromise) return pyodidePromise;

    pyodidePromise = (async () => {
      if (onStatus) onStatus("Booting Python engine…");

      const { loadPyodide } = await import(PYODIDE_URL + "pyodide.mjs");
      const pyodide = await loadPyodide({ indexURL: PYODIDE_URL });

      if (onStatus) onStatus("Loading package tools…");
      await pyodide.loadPackage("micropip");

      // Setup sys.path and PyScript/DOM shims
      await pyodide.runPythonAsync(`
import sys, os, types
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
if "." not in sys.path:
    sys.path.insert(0, ".")

# PyScript compatibility shims
if "pyscript" not in sys.modules:
    ps = types.ModuleType("pyscript")
    ps_ffi = types.ModuleType("pyscript.ffi")
    try:
        import pyodide.ffi
        ps_ffi.create_proxy = pyodide.ffi.create_proxy
    except ImportError:
        pass
    from js import document, window
    ps.document = document
    ps.window = window
    ps.ffi = ps_ffi
    sys.modules["pyscript"] = ps
    sys.modules["pyscript.ffi"] = ps_ffi
`);

      // Mount portable mip.py from vendor chrome if available
      try {
        const mipRes = await fetch("/vendor/pydevices-chrome/mip.py");
        if (mipRes.ok) {
          const mipCode = await mipRes.text();
          pyodide.FS.writeFile("mip.py", mipCode);
        }
      } catch (e) {
        console.warn("Could not preload local mip.py; using fallback:", e);
      }

      return pyodide;
    })();

    return pyodidePromise;
  }

  async function launchHeroCanvas(container) {
    const canvasId = container.getAttribute("data-hero-canvas") || "hero_canvas";
    const appName = container.getAttribute("data-hero-app") || "watch";
    const depsRaw = container.getAttribute("data-hero-deps") || "pydevices,pydevices-lvgl";
    const appUrl = container.getAttribute("data-hero-app-url") ||
      `https://PyDevices.github.io/assets/apps/${appName}.py`;
    const statusEl = container.querySelector(".hero-canvas-status");

    const setStatus = (msg) => {
      if (statusEl) statusEl.textContent = msg;
    };

    try {
      const pyodide = await getPyodide(setStatus);

      // 1. Install wheel dependencies from TestPyPI
      const deps = depsRaw.split(",").map(s => s.trim()).filter(Boolean);
      if (deps.length > 0) {
        setStatus("Installing hardware packages…");
        const micropip = pyodide.pyimport("micropip");
        micropip.set_index_urls(INDEX_URLS);
        for (const dep of deps) {
          try {
            await micropip.install(dep);
          } catch (err) {
            console.error(`micropip install ${dep} error:`, err);
          }
        }
      }

      // 2. Fetch standalone .py file via mip.py
      setStatus(`Loading ${appName}…`);
      const localAppUrl = `${window.location.origin}/assets/apps/${appName}.py`;
      await pyodide.runPythonAsync(`
import mip, os
_fetched = False
for _url in ("${appUrl}", "${localAppUrl}", "https://raw.githubusercontent.com/PyDevices/dotgithub/main/assets/apps/${appName}.py"):
    if not _url:
        continue
    try:
        mip.install(_url, target=".")
        if os.path.exists("${appName}.py"):
            _fetched = True
            break
    except Exception as _e:
        print(f"mip.install from {_url} error:", _e)

if not _fetched:
    raise RuntimeError("Could not fetch ${appName}.py from any location")
`);

      // 3. Launch App on Canvas
      setStatus("Starting…");
      const launchCode = `
import importlib
try:
    _app_mod = importlib.import_module("${appName}")
    if hasattr(_app_mod, "main"):
        _app_mod.main("${canvasId}")
    print("${appName} launched on ${canvasId}")
except Exception as _e:
    import traceback
    traceback.print_exc()
    raise
`;
      await pyodide.runPythonAsync(launchCode);

      // 4. Reveal Canvas smoothly
      container.classList.add("active");
      if (statusEl) statusEl.remove();

    } catch (err) {
      console.error("Hero canvas app failed to start:", err);
      if (statusEl) statusEl.textContent = "Live preview offline";
    }
  }

  function initHeroCanvases() {
    const containers = document.querySelectorAll("[data-hero-canvas]");
    containers.forEach(launchHeroCanvas);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initHeroCanvases);
  } else {
    initHeroCanvases();
  }
})();
