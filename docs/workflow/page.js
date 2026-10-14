const bar = document.querySelector('.bar');
const links = [...bar.querySelectorAll('a[href^="#"]:not([href="#top"])')];
const targets = links.map(link => document.querySelector(link.getAttribute('href')));
// Appearance: the mode (system, light or dark) and the palette, picked in the bar's menu.
// The head script already applied pinned ones; this keeps the button, the radios, the
// browser's theme colour and the remembered choices in step. Without the popover API the
// button stays hidden and the page follows the system in Reader.
const root = document.documentElement, papers = @PAPERS@;
const themeBtn = document.querySelector('.theme'), panel = document.querySelector('.appearance');
function paint() {
  const mode = root.dataset.theme || 'system', palette = root.dataset.palette || 'reader';
  document.querySelectorAll('meta[name="theme-color"]').forEach(meta => meta.content =
    papers[palette][(mode === 'system' ? meta.media.includes('dark') : mode === 'dark') ? 1 : 0]);
  const modeInput = panel.querySelector(`[name="mode"][value="${mode}"]`);
  const paletteInput = panel.querySelector(`[name="palette"][value="${palette}"]`);
  modeInput.checked = paletteInput.checked = true;
  themeBtn.dataset.mode = mode;
  const label = `Appearance: ${paletteInput.parentElement.textContent}, ${mode === 'system' ? 'matching the system' : mode}`;
  themeBtn.setAttribute('aria-label', label);
  themeBtn.title = label;
}
function remember(key, value, fallback) {
  try { value === fallback ? localStorage.removeItem(key) : localStorage.setItem(key, value); } catch {}
}
function setTheme(mode) {
  if (mode === 'system') delete root.dataset.theme; else root.dataset.theme = mode;
  remember('theme', mode, 'system');
  paint();
}
function setPalette(palette) {
  if (palette === 'reader') delete root.dataset.palette; else root.dataset.palette = palette;
  remember('palette', palette, 'reader');
  paint();
}
panel.addEventListener('change', e => (e.target.name === 'mode' ? setTheme : setPalette)(e.target.value));
// The panel sits in the top layer: it opens under its button, right edges aligned, and
// never closer than 16px to either side of the window; its width is page.css's
// min(264px, 100vw - 32px). A phone's address bar showing or hiding resizes the window,
// so it follows rather than closes.
function place() {
  const box = themeBtn.getBoundingClientRect(), width = root.clientWidth, panelWidth = Math.min(264, width - 32);
  panel.style.top = `${box.bottom + 8}px`;
  panel.style.right = `${Math.min(Math.max(16, width - box.right), width - 16 - panelWidth)}px`;
}
panel.addEventListener('beforetoggle', e => {
  themeBtn.classList.toggle('open', e.newState === 'open');
  if (e.newState === 'open') place();
});
addEventListener('resize', () => { if (panel.matches(':popover-open')) place(); });
paint();
themeBtn.hidden = !Object.hasOwn(HTMLElement.prototype, 'popover');

const tools = document.querySelector('.skill-tools'), rest = document.createElement('div');
tools.before(rest);  // marks where the tools sit when not stuck
const toTop = document.querySelector('.to-top');
function mark() {
  const scrolled = document.querySelector('h1').getBoundingClientRect().bottom < 0;
  bar.classList.toggle('scrolled', scrolled);
  toTop.classList.toggle('shown', scrolled);
  // The section in view is the last one whose top has passed under the bar, or the last
  // section once the page can scroll no further, though its top never reaches the bar.
  let current = -1;
  targets.forEach((target, index) => { if (target.getBoundingClientRect().top < 140) current = index; });
  if (innerHeight + scrollY >= document.documentElement.scrollHeight - 2) current = targets.length - 1;
  links.forEach((link, index) =>
    index === current ? link.setAttribute('aria-current', 'location') : link.removeAttribute('aria-current'));
  // The skill tools join the header only while they sit stuck right under it.
  const top = tools.getBoundingClientRect().top, under = parseFloat(getComputedStyle(tools).top);
  const stuck = Math.abs(top - under) < 1 && rest.getBoundingClientRect().top < under - 1;
  tools.classList.toggle('stuck', stuck);
  document.documentElement.classList.toggle('has-stuck-tools', stuck);
}
addEventListener('scroll', mark, {passive: true});
mark();

// Skills: group them by role (the default), moment or kind.
const byStep = document.getElementById('by-step'), byKind = document.getElementById('by-kind');
const blocks = [...byStep.querySelectorAll('section.group')];
const switcher = document.querySelector('.group-by');
function group(by) {
  byStep.dataset.by = by;
  byKind.hidden = by !== 'kind';
  byStep.hidden = by === 'kind';
  if (by !== 'kind') {
    const names = [...new Set(blocks.map(block => block.dataset[by]))];
    byStep.replaceChildren(...names.map(name => {
      const phase = document.createElement('div'), list = document.createElement('div');
      phase.className = 'phase'; list.className = 'groups';
      const title = document.createElement('h3');
      title.className = 'phase-title'; title.textContent = name;
      phase.append(title);
      list.append(...blocks.filter(block => block.dataset[by] === name));
      phase.append(list);
      return phase;
    }));
  }
  try { localStorage.setItem('group-by', by); } catch {}
}

// Each row opens from its heading; one button opens or closes them all, and a card's
// title opens the row of its step.
const status = document.getElementById('skills-status');
const all = document.querySelector('.all');
const groups = [...document.querySelectorAll('section.group')];
function setOpen(row, open) {
  row.classList.toggle('closed', !open);
  row.querySelector('.toggle').setAttribute('aria-expanded', open);
}
function label() {
  all.textContent = groups.some(row => row.classList.contains('closed')) ? 'Expand all' : 'Collapse all';
}
groups.forEach(row => {
  const heading = row.querySelector('h4'), toggle = document.createElement('button');
  toggle.type = 'button'; toggle.className = 'toggle';
  toggle.append(...heading.childNodes);
  heading.append(toggle);
  toggle.addEventListener('click', () => { setOpen(row, row.classList.contains('closed')); label(); });
  setOpen(row, false);
});
all.hidden = false;
all.addEventListener('click', () => {
  const open = groups.some(row => row.classList.contains('closed'));
  groups.forEach(row => setOpen(row, open));
  label();
  status.textContent = open ? 'Every group expanded.' : 'Every group collapsed.';
});
function openTarget() {
  const target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (target && target.matches('section.group')) { setOpen(target, true); label(); }
}
addEventListener('hashchange', openTarget);

switcher.hidden = false;
switcher.addEventListener('change', event => {
  group(event.target.value);
  status.textContent = 'Skills grouped by ' + event.target.parentElement.textContent.trim().toLowerCase() + '.';
});
let saved = 'role';
try { saved = localStorage.getItem('group-by') || 'role'; } catch {}
const choice = switcher.querySelector(`input[value="${saved}"]`);
if (choice) { choice.checked = true; group(saved); }
openTarget();
