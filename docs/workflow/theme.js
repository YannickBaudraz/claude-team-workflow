(function () {
  const papers = @PAPERS@, root = document.documentElement;
  let theme = null, palette = null;
  try { theme = localStorage.getItem('theme'); palette = localStorage.getItem('palette'); } catch {}
  if (theme === 'light' || theme === 'dark') root.dataset.theme = theme; else theme = null;
  if (palette !== 'reader' && Object.hasOwn(papers, palette)) root.dataset.palette = palette; else palette = 'reader';
  document.querySelectorAll('meta[name="theme-color"]').forEach(meta =>
    meta.content = papers[palette][(theme ? theme === 'dark' : meta.media.includes('dark')) ? 1 : 0]);
})();
