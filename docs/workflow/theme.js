(function () {
  let theme = null;
  try { theme = localStorage.getItem('theme'); } catch {}
  if (theme !== 'light' && theme !== 'dark') return;
  document.documentElement.dataset.theme = theme;
  document.querySelectorAll('meta[name="theme-color"]').forEach(meta => meta.content = theme === 'dark' ? '@DARK@' : '@LIGHT@');
})();
