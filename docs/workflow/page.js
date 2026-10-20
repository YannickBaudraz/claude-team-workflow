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
// A new mode or palette crossfades in where the browser can (page.css times it).
panel.addEventListener('change', e => {
  const change = () => (e.target.name === 'mode' ? setTheme : setPalette)(e.target.value);
  document.startViewTransition ? document.startViewTransition(change) : change();
});
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
themeBtn.hidden = panel.hidden = !('popover' in HTMLElement.prototype);

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
// Regrouped, each row in view glides from where it was to its new place, so you can follow
// it; one coming from far off starts a window's height away. The new headings and the list
// by kind fade in. Without a reduced-motion preference only.
const still = matchMedia('(prefers-reduced-motion: reduce)');
function regroup(by) {
  const was = byStep.hidden ? null : new Map(blocks.map(block => [block, block.getBoundingClientRect().top]));
  group(by);
  if (still.matches) return;
  const settle = {duration: 450, easing: 'cubic-bezier(.16,1,.3,1)'};
  if (!was || byStep.hidden) {
    (byStep.hidden ? byKind : byStep).animate({opacity: [0, 1]}, {duration: 250});
    return;
  }
  byStep.querySelectorAll('.phase-title').forEach(title => title.animate({opacity: [0, 1]}, {duration: 250}));
  blocks.forEach(block => {
    const box = block.getBoundingClientRect();
    if (box.bottom < 0 || box.top > innerHeight) return;
    const shift = Math.max(-innerHeight, Math.min(innerHeight, was.get(block) - box.top));
    if (Math.abs(shift) > 1) block.animate({translate: [`0 ${shift}px`, '0 0']}, settle);
  });
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
const reached = hash => hash && document.getElementById(decodeURIComponent(hash.slice(1)));
// A card or a skills row reached from a link is marked .landed once the scroll has been
// still for a moment, so page.css fades its ring in where the eye arrives, not on the way.
let waiting, settled;
function land(target) {
  removeEventListener('scroll', waiting);
  document.querySelectorAll('.landed').forEach(el => el.classList.remove('landed'));
  if (!target || !target.matches('.card, section.group')) return;
  waiting = () => {
    clearTimeout(settled);
    settled = setTimeout(() => { removeEventListener('scroll', waiting); target.classList.add('landed'); }, 120);
  };
  addEventListener('scroll', waiting, {passive: true});
  waiting();
}
function openTarget() {
  const target = reached(location.hash);
  if (target && target.matches('section.group')) { setOpen(target, true); label(); }
  land(target);
}
addEventListener('hashchange', openTarget);
// The same link again changes no hash but still scrolls there.
document.addEventListener('click', event => {
  const link = event.target.closest('a[href^="#"]');
  if (link && link.hash === location.hash) land(reached(link.hash));
});

switcher.hidden = false;
switcher.addEventListener('change', event => {
  regroup(event.target.value);
  status.textContent = 'Skills grouped by ' + event.target.parentElement.textContent.trim().toLowerCase() + '.';
});
let saved = 'role';
try { saved = localStorage.getItem('group-by') || 'role'; } catch {}
const choice = switcher.querySelector(`input[value="${saved}"]`);
if (choice) { choice.checked = true; group(saved); }
openTarget();

// I'm on this step: a step's number, on its card or in the router's answer, says where you
// are, and the dock answers the way /ask-team would: the command, the session, the gate, and
// the ways on once the step is done. The steps before it settle back, a "You are here" tab
// sits on its card, and from step to step that tab travels, so a loop shows where it goes
// back to. Where you are is in the address (?at=7, or ?at=done once the last epic closes), so
// the browser's Back steps back, and it is remembered for the next visit.
const answers = JSON.parse(document.getElementById('answers').textContent);
const dock = document.getElementById('dock'), where = document.querySelector('.where');
const cards = new Map([...document.querySelectorAll('.card')].map(card => [+card.id.slice(5), card]));
const here = document.createElement('span');
here.className = 'here-mark';
here.textContent = 'You are here';
cards.forEach((card, number) => {
  const badge = card.querySelector('.num'), button = document.createElement('button');
  button.type = 'button';
  button.className = 'num';
  button.dataset.at = number;
  button.textContent = badge.textContent;
  button.setAttribute('aria-pressed', 'false');
  button.setAttribute('aria-label', `I'm on step ${number}, ${answers.steps[number].name}`);
  button.title = `I'm on step ${number}`;
  badge.replaceWith(button);
});
const picks = [...document.querySelectorAll('button[data-at]')];
// A set of buttons the arrow keys, Home and End move through. The router's step buttons and
// the cards' are each one stop for Tab, the step you are on or step 1; the dock's ways on
// stay a stop each.
const chips = [...where.querySelectorAll('button[data-at]')];
const badges = [...cards.values()].map(card => card.querySelector('button.num'));
function rove(set, button) { set.forEach(other => { other.tabIndex = other === button ? 0 : -1; }); }
function arrows(container, set, roving) {
  container.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const buttons = set(), index = buttons.indexOf(event.target), last = buttons.length - 1;
    const to = {ArrowRight: index + 1, ArrowDown: index + 1, ArrowLeft: index - 1, ArrowUp: index - 1, Home: 0, End: last}[event.key];
    if (index < 0 || to === undefined) return;
    event.preventDefault();
    const button = buttons[to < 0 ? last : to > last ? 0 : to];
    if (roving) rove(buttons, button);
    button.focus();
  });
}
arrows(where, () => chips, true);
arrows(document.querySelector('main'), () => badges, true);
arrows(dock, () => [...dock.querySelectorAll('.go')], false);
let at = null, via = '';
// The step button the dock was opened from with the keyboard: closing returns there.
let back = null;
function field(name, value) {
  dock.querySelector(`.dock-${name}`).hidden = !value;
  dock.querySelector(`.dock-${name} dd`).innerHTML = value;
}
function fill() {
  const done = at === 'done', step = done ? null : answers.steps[at];
  cards.forEach((card, number) => {
    card.classList.toggle('behind', at !== null && (done || number < at));
    card.classList.toggle('here', number === at);
  });
  picks.forEach(pick => pick.setAttribute('aria-pressed', String(+pick.dataset.at === at)));
  for (const set of [chips, badges]) {
    if (!set.includes(document.activeElement)) rove(set, set.find(button => +button.dataset.at === at) || set[0]);
  }
  root.classList.toggle('has-dock', at !== null);
  dock.hidden = at === null;
  if (at === null || done) here.remove(); else cards.get(at).querySelector('.card-head').append(here);
  if (at === null) return;
  const badge = dock.querySelector('.dock-head .num'), role = dock.querySelector('.dock-role');
  badge.hidden = done;
  if (!done) { badge.className = `num p-${step.role}`; badge.textContent = at; }
  const title = document.createElement('a');
  title.href = `#step-${at}`;
  title.textContent = `Step ${at}, ${step?.name}`;
  dock.querySelector('.dock-step').replaceChildren(done ? 'Every epic is closed' : title);
  role.textContent = done ? 'The roadmap is done' : step.label;
  role.className = `role dock-role p-${done ? 'you' : step.role}`;
  dock.querySelector('.dock-via').textContent = via;
  dock.querySelector('.dock-via').hidden = !via;
  const copy = text => text && navigator.clipboard ? '<button type="button" class="copy">Copy</button>' : '';
  if (done) {
    field('run', `For the next change: ${answers.end}${copy(answers.end_copy)}`);
    field('session', '');
    field('gate', '');
  } else {
    field('run', step.command + copy(step.copy));
    field('session', step.session);
    field('gate', step.gate ? `<span class="gate-mark"><span class="dia"></span>${step.gate}</span> ${step.gate_out}` : step.gate_out);
  }
  dock.querySelector('.dock-next').replaceChildren(...(done ? [] : step.next).map(({label, to}) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'go';
    button.dataset.to = to || 'done';
    button.dataset.label = label;
    const why = document.createElement('b'), where = document.createElement('span'), arrow = document.createElement('i');
    why.textContent = label;
    where.textContent = !to ? 'the roadmap is done' : to === at ? `step ${to} again`
      : `${to < at ? 'back to ' : ''}step ${to}, ${answers.steps[to].name}`;
    arrow.className = 'ai';
    button.append(why, where, arrow);
    return button;
  }));
}
function address() {
  const url = new URL(location.href);
  if (at === null) url.searchParams.delete('at'); else url.searchParams.set('at', at);
  return url;
}
function parse(value) {
  return value === 'done' ? 'done' : Object.hasOwn(answers.steps, value ?? '') ? +value : null;
}
// Out of view, the page first glides to the card, centred between the bar and the dock;
// then the tab moves.
function glide(card) {
  const box = card.getBoundingClientRect(), top = bar.offsetHeight;
  const bottom = innerHeight - (dock.hidden ? Math.min(240, innerHeight * .3) : dock.offsetHeight);
  if (box.top >= top + 8 && box.bottom <= bottom - 8) return Promise.resolve();
  scrollTo({top: scrollY + box.top - top - Math.max(16, (bottom - top - box.height) / 2), behavior: 'smooth'});
  return new Promise(resolve => {
    const timer = setTimeout(resolve, 900);
    addEventListener('scrollend', () => { clearTimeout(timer); resolve(); }, {once: true});
  });
}
// The tab travels from its old card to its new one, measured before and after; the dock
// rises when it opens and sinks when it closes. Plain animations, not a view transition:
// Chrome on Android blinks the dock in one.
const settle = {duration: 550, easing: 'cubic-bezier(.16,1,.3,1)'};
async function go(to, how = '', push = true) {
  if (to === at) return;
  const was = at;
  at = to;
  via = how;
  land(null);  // a card reached from a link loses its ring: the step you pick is the one marked
  if (push) history.pushState(null, '', address());
  try { to === null ? localStorage.removeItem('at') : localStorage.setItem('at', to); } catch {}
  const card = cards.get(to);
  if (still.matches) {
    fill();
    if (card) card.scrollIntoView({block: 'nearest'});
    return;
  }
  if (card) await glide(card);
  const from = here.isConnected ? here.getBoundingClientRect() : null;
  if (to === null) await dock.animate({translate: ['0 0', '0 100%']}, {duration: 250, easing: 'cubic-bezier(.7,0,.84,0)'}).finished;
  fill();
  if (was === null) dock.animate({translate: ['0 100%', '0 0']}, {duration: 350, easing: settle.easing});
  if (!here.isConnected) return;
  const now = here.getBoundingClientRect();
  here.animate(from ? {transform: [`translate(${from.left - now.left}px, ${from.top - now.top}px)`, 'none']}
    : {opacity: [0, 1], transform: ['translateY(-6px)', 'none']}, from ? settle : {duration: 300, easing: settle.easing});
}
// From the keyboard (a click with no pointer behind it), picking a step takes focus into the
// dock, so its answer is read and Tab reaches it at once; a way on keeps focus on the ways on,
// so Enter after Enter walks the flow; closing returns focus to where the dock was opened.
function close() {
  const from = back?.isConnected ? back : cards.get(at)?.querySelector('.num');
  const focused = dock.contains(document.activeElement);
  back = null;
  go(null).then(() => {
    if (!focused || !from) return;
    rove(chips.includes(from) ? chips : badges, from);
    from.focus();
  });
}
// For Tab, the dock sits right after the step button it answers, though it is drawn at the
// window's foot: Tab from that button enters it, and leaving it, either way, comes back to
// the page beside that button rather than at the page's start or end.
const focusable = 'a[href], button, input, select, textarea, summary, [tabindex]';
function tabbable(scope) {
  return [...scope.querySelectorAll(focusable)].filter(el => el.tabIndex >= 0 && !el.disabled
    && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
}
function anchor() {
  return back?.isConnected ? back : cards.get(at)?.querySelector('button.num') || null;
}
document.addEventListener('keydown', event => {
  if (event.key !== 'Tab' || at === null || event.altKey || event.ctrlKey || event.metaKey) return;
  const from = anchor(), active = document.activeElement, inside = tabbable(dock);
  if (!from || !inside.length) return;
  const page = tabbable(document.body).filter(el => !dock.contains(el));
  let target = null;
  if (dock.contains(active)) {
    if (event.shiftKey && (active === dock || active === inside[0])) target = from;
    else if (!event.shiftKey && active === inside.at(-1)) target = page[page.indexOf(from) + 1] || page[0];
  } else if (!event.shiftKey && active === from) target = inside[0];
  else if (event.shiftKey && page[page.indexOf(active) - 1] === from) target = inside.at(-1);
  if (!target) return;
  event.preventDefault();
  target.focus();
});
document.addEventListener('click', event => {
  const pick = event.target.closest('button[data-at]'), next = event.target.closest('.go');
  const copy = event.target.closest('.copy'), keyed = event.detail === 0;
  if (pick) {
    if (keyed) back = pick;
    go(+pick.dataset.at).then(() => { if (keyed && at !== null) dock.focus(); });
  } else if (next) {
    const to = parse(next.dataset.to), label = next.dataset.label;
    back = null;
    go(to, label === 'Done' || to === 'done' ? '' : `${label} at step ${at}`)
      .then(() => (dock.querySelector('.go') || dock).focus());
  }
  else if (copy) {
    navigator.clipboard.writeText(at === 'done' ? answers.end_copy : answers.steps[at].copy).then(() => {
      copy.textContent = 'Copied';
      setTimeout(() => { copy.textContent = 'Copy'; }, 1500);
    });
  } else if (event.target.closest('.dock-close')) close();
});
// Escape closes the dock from anywhere, unless it is closing the appearance menu.
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && at !== null && !event.defaultPrevented && !panel.matches(':popover-open')) close();
});
addEventListener('popstate', () => go(parse(new URL(location.href).searchParams.get('at')), '', false));
// The dock's height keeps the page's end and the back-to-top button clear of it.
new ResizeObserver(() => root.style.setProperty('--dock', `${dock.offsetHeight}px`)).observe(dock);
where.hidden = false;
{
  const asked = parse(new URL(location.href).searchParams.get('at'));
  let kept = null;
  try { kept = parse(localStorage.getItem('at')); } catch {}
  at = asked ?? kept;
  if (at !== null && asked === null) history.replaceState(null, '', address());
  fill();
  if (cards.has(asked) && !location.hash) cards.get(asked).scrollIntoView({block: 'center'});
}
