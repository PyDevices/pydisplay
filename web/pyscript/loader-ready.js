/*! pydisplay gallery loaders — hide the loading row when PyScript is ready or failed */
(function () {
  var runtime = document.body && document.body.getAttribute('data-loader-runtime');
  if (runtime !== 'mpy' && runtime !== 'py') {
    return;
  }

  var btn = document.getElementById('run-btn');
  var spin = document.querySelector('#loading .spinner');
  var status = document.getElementById('status');
  var readyEvent = runtime === 'mpy' ? 'mpy:ready' : 'py:ready';
  var doneEvent = runtime === 'mpy' ? 'mpy:done' : 'py:done';
  var polls = 0;
  var maxPolls = 800; // ~120s at 150ms — slow WASM / first visit
  var timer = null;

  function hideSpinner() {
    if (spin) {
      spin.style.display = 'none';
    }
  }

  function runtimeFailed() {
    hideSpinner();
    if (!btn || !btn.disabled) {
      return;
    }
    if (status && /Loading/i.test(status.textContent)) {
      status.textContent = 'Runtime failed — see console output below.';
    }
  }

  function runtimeReady() {
    hideSpinner();
  }

  function stopPolling() {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  }

  addEventListener(readyEvent, function () {
    if (status && /Loading/i.test(status.textContent)) {
      status.textContent =
        runtime === 'mpy' ? 'Starting MicroPython…' : 'Starting Python…';
    }
  });

  addEventListener(doneEvent, function () {
    stopPolling();
    if (btn && !btn.disabled) {
      runtimeReady();
    } else {
      runtimeFailed();
    }
  });

  timer = setInterval(function () {
    polls += 1;
    if (btn && !btn.disabled) {
      stopPolling();
      runtimeReady();
    } else if (polls >= maxPolls) {
      stopPolling();
      runtimeFailed();
    }
  }, 150);
})();
