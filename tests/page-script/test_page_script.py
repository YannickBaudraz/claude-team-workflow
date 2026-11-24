"""The workflow page's script, run in headless Chrome.

The build and the other suites read the sources and the Python that writes the page, and
never run page.js, so one error in it can leave every card and the step answer dead while
they all pass. This test builds the page, loads it with nothing after # in the address, and
checks that the script ran without an error, that every card's number became its step
button, and that a click on a card opens the step's answer and a second click closes it.

Run: python3 -m unittest discover tests/page-script
Chrome must run outside the Claude Code sandbox; CHROME sets its path. With no Chrome found,
the test is skipped, unless REQUIRE_BROWSER is set, as CI sets it.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Put first in the page's <head>, so it hears an error from any script after it. Once the page
# has loaded, it clicks the first card twice, then writes what it saw into the page, where
# Chrome's --dump-dom shows it. Animations are finished by hand: headless Chrome does not
# always run them to their end, and closing the answer waits for its slide-out.
PROBE = """<script>
window.__errors = [];
addEventListener('error', event => __errors.push(String(event.message || event.error)));
addEventListener('unhandledrejection', event => __errors.push('unhandled rejection: ' + event.reason));
addEventListener('load', () => setTimeout(async () => {
  const settle = ms => new Promise(resolve => setTimeout(resolve, ms));
  const finish = () => document.getAnimations().forEach(animation => animation.finish());
  const click = async target => { target.click(); await settle(1200); finish(); await settle(300); };
  const cards = [...document.querySelectorAll('.card')], dock = document.getElementById('dock');
  const report = {cards: cards.length, buttons: document.querySelectorAll('.card button.num').length};
  const text = cards[0] && cards[0].querySelector('.summary');
  if (text && dock) {
    await click(text);
    report.opened = !dock.hidden;
    if (report.opened) {
      await click(text);
      report.closed = dock.hidden;
    }
  }
  report.errors = __errors;
  const out = document.createElement('pre');
  out.id = 'page-check';
  out.textContent = JSON.stringify(report);
  document.body.append(out);
}, 300));
</script>"""


def chrome():
    named = os.environ.get('CHROME')
    if named:
        return named
    for name in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'):
        found = shutil.which(name)
        if found:
            return found
    return '/opt/google/chrome/chrome' if os.path.isfile('/opt/google/chrome/chrome') else None


class PageScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        browser = chrome()
        if not browser:
            if os.environ.get('REQUIRE_BROWSER'):
                raise RuntimeError('No Chrome found: set CHROME to its path')
            raise unittest.SkipTest('No Chrome found: set CHROME to run this test')
        work = tempfile.mkdtemp(prefix='workflow-page-script-')
        cls.addClassCleanup(shutil.rmtree, work, ignore_errors=True)
        page = os.path.join(work, 'index.html')
        built = subprocess.run([sys.executable, os.path.join(ROOT, 'docs', 'build-workflow.py'), '--out', page],
                               capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError('The page did not build:\n' + built.stdout + built.stderr)
        with open(page, encoding='utf-8') as source:
            text = source.read()
        with open(page, 'w', encoding='utf-8') as probed:
            probed.write(text.replace('<head>', '<head>' + PROBE, 1))
        dom = subprocess.run([browser, '--headless=new', '--no-sandbox', '--disable-gpu',
                              f'--user-data-dir={os.path.join(work, "profile")}', '--virtual-time-budget=15000',
                              '--dump-dom', 'file://' + page],
                             capture_output=True, text=True, timeout=120).stdout
        found = re.search(r'<pre id="page-check">(.*?)</pre>', dom, re.S)
        if not found:
            raise RuntimeError('The page never finished its check in Chrome')
        cls.report = json.loads(html.unescape(found.group(1)))

    def test_the_script_runs_without_an_error(self):
        self.assertEqual(self.report['errors'], [])

    def test_every_card_number_becomes_its_step_button(self):
        self.assertGreater(self.report['cards'], 0)
        self.assertEqual(self.report['buttons'], self.report['cards'])

    def test_a_click_on_a_card_opens_its_answer(self):
        self.assertTrue(self.report.get('opened'))

    def test_a_second_click_on_the_card_closes_it(self):
        self.assertTrue(self.report.get('closed'))


if __name__ == '__main__':
    unittest.main()
