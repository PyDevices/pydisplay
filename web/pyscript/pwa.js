/*! pydisplay PWA bootstrap — COI service worker registration + install UI */
(function () {
  var SW_URL = './sw.js';
  var SW_SCOPE = './';

  function needsCoiReload() {
    try {
      new SharedArrayBuffer(4, { maxByteLength: 8 });
      return false;
    } catch (_) {
      return !navigator.serviceWorker.controller;
    }
  }

  function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
      return Promise.resolve(null);
    }
    return navigator.serviceWorker.register(SW_URL, { scope: SW_SCOPE }).then(function (reg) {
      if (needsCoiReload()) {
        reg.addEventListener('updatefound', function () {
          var worker = reg.installing;
          if (!worker) {
            return;
          }
          worker.addEventListener('statechange', function () {
            if (worker.state === 'activated' && !navigator.serviceWorker.controller) {
              location.reload();
            }
          });
        });
        if (reg.installing) {
          reg.installing.addEventListener('statechange', function () {
            if (reg.installing.state === 'activated' && !navigator.serviceWorker.controller) {
              location.reload();
            }
          });
        }
      }
      return reg;
    });
  }

  function ensureToast() {
    var toast = document.getElementById('pwa-toast');
    if (toast) {
      return toast;
    }
    toast = document.createElement('div');
    toast.id = 'pwa-toast';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.innerHTML =
      '<span id="pwa-message"></span>' +
      '<button type="button" id="pwa-toast-dismiss">OK</button>';
    document.body.appendChild(toast);
    toast.querySelector('#pwa-toast-dismiss').addEventListener('click', function () {
      toast.classList.remove('is-visible');
    });
    return toast;
  }

  function showToast(message) {
    var toast = ensureToast();
    var msg = document.getElementById('pwa-message');
    if (msg) {
      msg.textContent = message;
    }
    toast.classList.add('is-visible');
  }

  function wireInstallPrompt() {
    var installBtn = document.getElementById('pwa-install-btn');
    if (!installBtn) {
      return;
    }
    var deferredPrompt = null;

    window.addEventListener('beforeinstallprompt', function (e) {
      e.preventDefault();
      deferredPrompt = e;
      installBtn.style.display = 'inline-block';
    });

    installBtn.addEventListener('click', function () {
      if (!deferredPrompt) {
        return;
      }
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function (choice) {
        console.log('PWA install choice:', choice.outcome);
        deferredPrompt = null;
        installBtn.style.display = 'none';
      });
    });

    window.addEventListener('appinstalled', function () {
      deferredPrompt = null;
      installBtn.style.display = 'none';
      showToast('pydisplay installed — launch it from your home screen.');
    });
  }

  function wireConnectivity() {
    window.addEventListener('online', function () {
      showToast('You are back online.');
    });
    window.addEventListener('offline', function () {
      showToast('You are offline. Cached demos may still run.');
    });
  }

  function wireActivationToast(reg) {
    if (!reg || needsCoiReload()) {
      return;
    }
    if (navigator.serviceWorker.controller) {
      return;
    }
    reg.addEventListener('updatefound', function () {
      var worker = reg.installing;
      if (!worker) {
        return;
      }
      worker.addEventListener('statechange', function () {
        if (worker.state === 'activated' && navigator.serviceWorker.controller) {
          showToast('App shell cached — demos work offline after one online visit.');
        }
      });
    });
  }

  var registration = registerServiceWorker();

  function onReady() {
    registration
      .then(function (reg) {
        wireActivationToast(reg);
      })
      .catch(function (err) {
        console.log('Service worker registration failed:', err);
      });
    wireInstallPrompt();
    wireConnectivity();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', onReady);
  } else {
    onReady();
  }
})();
