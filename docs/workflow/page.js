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
let at = null, via = '';
// The game: the loops counted so far (epic 2, ticket 3), the moves to undo, the way picked at a
// fork while choosing (-1 when not), and whether a move is still under way.
let score = {}, moves = [], picked = -1, busy = false;
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
  // The game's score, only once a move has been played: it counts this run, not the project,
  // which only /ask-team, reading the tracker, can tell.
  const loops = done ? [] : step.loops.map(loop => `${loop} ${score[loop] || 1}`);
  const counted = !moves.length ? '' : done ? `This run: ${score.epic || 1} epic${(score.epic || 1) > 1 ? 's' : ''}`
    : loops.length ? `This run: ${loops.join(' · ')}` : '';
  dock.querySelector('.dock-score').textContent = counted;
  dock.querySelector('.dock-score').hidden = !counted;
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
  picked = -1;
  paintGame();
}
// The keys the game answers to, shown under the ways on where there is a keyboard; at a fork
// being chosen, the ways not picked step back.
function paintGame() {
  const ways = [...dock.querySelectorAll('.go')], key = text => `<kbd>${text}</kbd>`;
  dock.querySelector('.dock-next').classList.toggle('choosing', picked >= 0);
  ways.forEach((way, index) => way.classList.toggle('chosen', index === picked));
  dock.querySelector('.dock-keys').innerHTML = picked >= 0
    ? `${key('↑')}${key('↓')} choose ${key('→')} go ${key('←')} back`
    : (at === 'done' ? '' : `${key('→')} play `) + (moves.length ? `${key('←')} undo ` : '') + `${key('Esc')} leave`;
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
async function go(to, {how = '', push = true, label = null, undo = null} = {}) {
  if (to === at && !label) return;
  const was = at;
  if (undo) score = undo.score;
  else if (push && was !== null && to !== null) moves.push({at: was, via, score});
  if (to === null) moves = [];
  const unit = label && /^Another (\w+)/.exec(label)?.[1];
  if (!undo) score = !label ? {} : label === 'Next epic' ? {epic: (score.epic || 1) + 1}
    : unit ? {...score, [unit]: (score[unit] || 1) + 1} : score;
  at = to;
  via = how;
  busy = true;
  land(null);  // a card reached from a link loses its ring: the step you pick is the one marked
  if (push) history.pushState(null, '', address());
  try { to === null ? localStorage.removeItem('at') : localStorage.setItem('at', to); } catch {}
  const card = cards.get(to);
  if (still.matches) {
    fill();
    if (card) card.scrollIntoView({block: 'nearest'});
    busy = false;
    return;
  }
  if (card) await glide(card);
  const from = here.isConnected ? here.getBoundingClientRect() : null;
  if (to === null) await dock.animate({translate: ['0 0', '0 100%']}, {duration: 250, easing: 'cubic-bezier(.7,0,.84,0)'}).finished;
  fill();
  if (was === null) dock.animate({translate: ['0 100%', '0 0']}, {duration: 350, easing: settle.easing});
  busy = false;
  if (!here.isConnected) return;
  // The tab hops like a piece on a board: up from its old card and down onto the new one, or
  // in place when the step comes round again.
  const now = here.getBoundingClientRect();
  if (!from) {
    here.animate({opacity: [0, 1], transform: ['translateY(-6px)', 'none']}, {duration: 300, easing: settle.easing});
    return;
  }
  const dx = from.left - now.left, dy = from.top - now.top, lift = 14 + Math.min(26, Math.hypot(dx, dy) / 24);
  here.animate({transform: [`translate(${dx}px, ${dy}px)`, `translate(${dx / 2}px, ${dy / 2 - lift}px)`, 'none']}, settle);
}
// A way on, from its button or the game's keys. Focus that was on the ways on stays there.
function follow(label, to) {
  const focused = dock.contains(document.activeElement);
  back = null;
  return go(to, {how: label === 'Done' || to === 'done' ? '' : `${label} at step ${at}`, label})
    .then(() => { if (focused) (dock.querySelector('.go') || dock).focus(); });
}
// From the keyboard (a click with no pointer behind it), picking a step takes focus into the
// dock, so its answer is read and Tab reaches it at once; a way on keeps focus on the ways on,
// so Enter after Enter walks the flow; closing returns focus to where the dock was opened.
function close() {
  const from = back?.isConnected ? back : cards.get(at)?.querySelector('.num');
  const focused = dock.contains(document.activeElement);
  back = null;
  go(null).then(() => {
    if (focused && from) from.focus();
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
  } else if (next) follow(next.dataset.label, parse(next.dataset.to));
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
addEventListener('popstate', () => {
  moves = [];
  go(parse(new URL(location.href).searchParams.get('at')), {push: false});
});
// The game, while a step is open: → plays it, to the next step or, at a fork, to choosing
// between its ways with ↑ and ↓, then → again; ← undoes the last move, or the choosing.
// Arrow keys only, never with a modifier: nothing scrolls sideways here, and ↑ ↓ are taken
// only while choosing.
document.addEventListener('keydown', event => {
  if (at === null || busy || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  if (panel.matches(':popover-open') || event.target.closest('input, textarea, select')) return;
  const ways = at === 'done' ? [] : answers.steps[at].next;
  const take = way => follow(way.label, way.to || 'done');
  if (event.key === 'ArrowRight') {
    event.preventDefault();
    if (picked >= 0) take(ways[picked]);
    else if (ways.length === 1) take(ways[0]);
    else if (ways.length) { picked = 0; paintGame(); }
  } else if (event.key === 'ArrowLeft') {
    event.preventDefault();
    if (picked >= 0) { picked = -1; paintGame(); return; }
    const last = moves.pop();
    if (last) go(last.at, {how: last.via, undo: last});
  } else if (picked >= 0 && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
    event.preventDefault();
    picked = (picked + (event.key === 'ArrowDown' ? 1 : ways.length - 1)) % ways.length;
    paintGame();
  }
});
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
