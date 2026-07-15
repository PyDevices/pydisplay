/*! pydisplay PWA bootstrap — COI service worker registration + install/update UI */
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
      '<span class="pwa-toast-actions">' +
      '<button type="button" id="pwa-toast-action" hidden></button>' +
      '<button type="button" id="pwa-toast-dismiss">OK</button>' +
      '</span>';
    document.body.appendChild(toast);
    toast.querySelector('#pwa-toast-dismiss').addEventListener('click', function () {
      toast.classList.remove('is-visible');
      toast.classList.remove('is-update');
    });
    return toast;
  }

  function showToast(message, options) {
    options = options || {};
    var toast = ensureToast();
    var msg = document.getElementById('pwa-message');
    var action = document.getElementById('pwa-toast-action');
    var dismiss = document.getElementById('pwa-toast-dismiss');
    if (msg) {
      msg.textContent = message;
    }
    if (action) {
      if (options.actionLabel && typeof options.onAction === 'function') {
        action.hidden = false;
        action.textContent = options.actionLabel;
        action.onclick = function () {
          options.onAction();
        };
        toast.classList.add('is-update');
      } else {
        action.hidden = true;
        action.onclick = null;
        toast.classList.remove('is-update');
      }
    }
    if (dismiss) {
      dismiss.textContent = options.dismissLabel || 'OK';
    }
    toast.classList.add('is-visible');
  }

  function showUpdateToast() {
    showToast('A new version of the app shell is ready.', {
      actionLabel: 'Reload',
      dismissLabel: 'Later',
      onAction: function () {
        location.reload();
      },
    });
  }

  function watchWorkerForUpdate(worker) {
    if (!worker) {
      return;
    }
    worker.addEventListener('statechange', function () {
      // With skipWaiting(), a waiting phase is brief; "installed" while we
      // already have a controller means a new shell revision is ready.
      if (
        (worker.state === 'installed' || worker.state === 'activated') &&
        navigator.serviceWorker.controller
      ) {
        showUpdateToast();
      }
    });
  }

  function wireUpdatePrompt(reg) {
    if (!reg || needsCoiReload()) {
      return;
    }
    if (reg.waiting && navigator.serviceWorker.controller) {
      showUpdateToast();
    }
    reg.addEventListener('updatefound', function () {
      watchWorkerForUpdate(reg.installing);
    });
    // Check when the PWA becomes visible again (browsers also check periodically).
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') {
        reg.update().catch(function () {});
      }
    });
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
        wireUpdatePrompt(reg);
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
