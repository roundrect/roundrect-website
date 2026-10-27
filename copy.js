// copy.js — the site's only script (CLAUDE.md, DESIGN.md). It adds a Copy button to the caption bar of every code
// block (figure.code) on the page. Without it nothing is missing: one click still selects a whole block for ⌘C
// (site.css, user-select: all). Same host, no requests, nothing stored.
(function () {
  'use strict';
  if (!navigator.clipboard || !window.isSecureContext) return;
  document.querySelectorAll('figure.code').forEach(function (fig) {
    var cap = fig.querySelector('figcaption');
    var code = fig.querySelector('pre code');
    if (!cap || !code) return;
    var lang = cap.textContent;
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy';
    button.textContent = 'Copy';
    button.setAttribute('aria-label', 'Copy the ' + lang + ' code');
    var status = document.createElement('span');
    status.className = 'copy-status';
    status.setAttribute('role', 'status');
    var timer;
    function show(text, label) {
      button.textContent = text;
      status.textContent = label;
      clearTimeout(timer);
      timer = setTimeout(function () { button.textContent = 'Copy'; status.textContent = ''; }, 2000);
    }
    button.addEventListener('click', function () {
      navigator.clipboard.writeText(code.textContent).then(
        function () { show('Copied', 'Copied to the clipboard'); },
        function () { show('Press ⌘C', 'Could not copy: select the code and press Command C'); }
      );
    });
    cap.appendChild(button);
    cap.appendChild(status);
  });
})();
