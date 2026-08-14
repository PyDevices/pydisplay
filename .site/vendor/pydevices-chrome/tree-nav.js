/*
 * PyDevices — Tree Navigation & Explorer JS
 * Provides collapsible node tree view and real-time search filtering.
 */

(function () {
  'use strict';

  function initTree(container) {
    if (!container) return;

    var branches = container.querySelectorAll('.tree-branch');
    branches.forEach(function (branch) {
      var header = branch.querySelector('.tree-branch-header');
      if (!header) return;
      header.addEventListener('click', function () {
        branch.classList.toggle('open');
      });
    });

    var searchInput = container.querySelector('.tree-search');
    if (searchInput) {
      searchInput.addEventListener('input', function (e) {
        var query = e.target.value.toLowerCase().trim();
        var leaves = container.querySelectorAll('.tree-leaf');

        if (!query) {
          leaves.forEach(function (leaf) {
            leaf.style.display = '';
          });
          branches.forEach(function (b) {
            b.style.display = '';
          });
          return;
        }

        branches.forEach(function (branch) {
          var branchLeaves = branch.querySelectorAll('.tree-leaf');
          var branchMatchCount = 0;

          branchLeaves.forEach(function (leaf) {
            var text = leaf.textContent.toLowerCase();
            if (text.indexOf(query) !== -1) {
              leaf.style.display = '';
              branchMatchCount++;
            } else {
              leaf.style.display = 'none';
            }
          });

          if (branchMatchCount > 0) {
            branch.style.display = '';
            branch.classList.add('open');
          } else {
            branch.style.display = 'none';
          }
        });
      });
    }
  }

  function setupModal() {
    var triggerBtns = document.querySelectorAll('.js-open-tree-modal');
    var modalBackdrop = document.getElementById('pydevices-tree-modal-backdrop');
    var closeBtn = document.getElementById('pydevices-tree-modal-close');

    if (!modalBackdrop) return;

    function openModal() {
      modalBackdrop.classList.add('active');
      document.body.style.overflow = 'hidden';
    }

    function closeModal() {
      modalBackdrop.classList.remove('active');
      document.body.style.overflow = '';
    }

    triggerBtns.forEach(function (btn) {
      btn.addEventListener('click', openModal);
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', closeModal);
    }

    modalBackdrop.addEventListener('click', function (e) {
      if (e.target === modalBackdrop) {
        closeModal();
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && modalBackdrop.classList.contains('active')) {
        closeModal();
      }
    });
  }

  function init() {
    var inlineTrees = document.querySelectorAll('.tree-container');
    inlineTrees.forEach(function (tree) {
      initTree(tree);
    });
    setupModal();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
