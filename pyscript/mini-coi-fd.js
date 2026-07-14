/*! coi-serviceworker v0.1.7 - Guido Zuidhof and contributors, licensed under MIT */
/*! mini-coi - Andrea Giammarchi and contributors, licensed under MIT */
/** Back-compat shim: pydisplay now registers ./sw.js via pwa.js (COI + offline cache). */
(({ document: d, navigator: { serviceWorker: s } }) => {
  if (!d) return;
  try { new SharedArrayBuffer(4, { maxByteLength: 8 }); }
  catch (_) {
    const { currentScript: c } = d;
    const scope = (c && c.getAttribute('scope')) || '.';
    s.register('./sw.js', { scope }).then(r => {
      r.addEventListener('updatefound', () => location.reload());
      if (r.active && !s.controller) location.reload();
    });
  }
})(typeof document !== 'undefined' ? globalThis : undefined);
