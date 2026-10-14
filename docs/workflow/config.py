"""Where the sources are, and the page's own frame: title, lede, glossary, roles, colours, fonts."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(ROOT, 'skills', 'ask-team', 'SKILL.md')
REGISTRY = os.path.join(ROOT, 'skills', 'ask-team', 'REGISTRY.md')
README = os.path.join(ROOT, 'README.md')
PREVIEW = os.path.join(ROOT, 'docs', 'workflow.html')
FONTS = os.path.join(ROOT, 'docs', 'fonts')
REPO_URL = 'https://github.com/YannickBaudraz/claude-team-workflow'
PAGE_URL = 'https://yannickbaudraz.github.io/claude-team-workflow/'

TITLE = 'Claude Team Workflow'
LEDE = 'From an idea to a merged epic, run the way an engineering team works.'
# Terms the sources use without explaining them; each shows only while a source uses it.
TERMS = [
    ('ADR', r'\bADRs?\b', 'Architecture decision record: a short file that keeps one decision and why it was made.'),
    ('PRD', r'\bPRD\b', 'Product requirements document: what to build, for whom, and how success is measured.'),
    ('Epic', r'\bepic\b', 'One release slice of the roadmap, carried through every per-epic step.'),
    ('Spike', r'\bspike\b', 'One question answered with a throwaway prototype or a write-up, not production code.'),
    ('Fog', r'\bFog\b', 'The way forward is unclear: /wayfinder maps the open decisions before the work starts.'),
    ('Tracer-bullet ticket', r'tracer-bullet', 'A thin slice that runs end to end through every layer, so it can be built and merged on its own.'),
    ('Blocking edge', r'blocking edges?', 'A link saying one ticket has to be done before another can start.'),
    ('CI green', r'\bCI green\b', 'Every automated check on the pull request passes.'),
]

# The router's Sessions section names these roles; the steps it leaves out are yours.
ROLE_WORDS = {'product': 'product', 'tech lead': 'lead', 'developer': 'dev', 'reviewer': 'review'}
ROLE_NAMES = {'product': 'Product', 'lead': 'Tech lead', 'dev': 'Developer',
              'review': 'Reviewer', 'you': 'You'}
GROUP_TITLES = {'start': 'Start here', 'in': 'Other ways in', 'any': 'Any time',
                'other': 'Ad hoc'}
OUTSIDE = 'Outside the flow'

LIGHT = dict(paper='#F2F4F7', surface='#FFFFFF', tray='#E7EBF0', ink='#16202C', muted='#5B6778',
             rule='#D3DAE2', product='#94600F', lead='#0E7A70', dev='#2C5BC8',
             review='#7445C2', you='#C02E48', on_role='#FFFFFF')
DARK = dict(paper='#18191B', surface='#212225', tray='#141517', ink='#E8E9EB', muted='#A0A4AA',
            rule='#34363A', product='#D6A45E', lead='#64B5A7', dev='#93A9E2',
            review='#B7A2E0', you='#E98A93', on_role='#18191B')

# The palettes a visitor picks in the bar's appearance menu, each with a light and a dark
# side: (key, name, light, dark). Reader is the page's own, the one a first visit gets.
# Cool is Reader moved toward blue-grey; its light side takes the same OKLab step, colour by
# colour, as its dark side, with the change in lightness mirrored. Catppuccin (Latte, Mocha)
# and Nord (Snow Storm, Polar Night) keep their authors' published colours, except the text
# colours that read under 4.5:1 on paper or cards: only their lightness was moved, until
# they pass. Every text colour is checked at 4.5:1 on each build.
PALETTES = [
    ('reader', 'Reader', LIGHT, DARK),
    ('cool', 'Cool',
     dict(paper='#F0F5FB', surface='#FFFFFF', tray='#E7EDF3', ink='#15202D', muted='#546275',
          rule='#CDD9E6', product='#94600F', lead='#0E7A70', dev='#2C5BC8',
          review='#7445C2', you='#C02E48', on_role='#FFFFFF'),
     dict(paper='#16191D', surface='#1E2227', tray='#121417', ink='#E6E9EC', muted='#A3AAB2',
          rule='#323840', product='#D6A45E', lead='#64B5A7', dev='#93A9E2',
          review='#B7A2E0', you='#E98A93', on_role='#121417')),
    # Latte: mantle, base, crust, text, subtext0, surface0; yellow, teal, blue, mauve, red.
    # Mocha: the same roles, peach for product.
    ('catppuccin', 'Catppuccin',
     dict(paper='#E6E9EF', surface='#EFF1F5', tray='#DCE0E8', ink='#4C4F69', muted='#65687E',
          rule='#CCD0DA', product='#965C04', lead='#04757B', dev='#135CEA',
          review='#8737ED', you='#D00A38', on_role='#FFFFFF'),
     dict(paper='#181825', surface='#1E1E2E', tray='#11111B', ink='#CDD6F4', muted='#A6ADC8',
          rule='#313244', product='#FAB387', lead='#94E2D5', dev='#89B4FA',
          review='#CBA6F7', you='#F38BA8', on_role='#11111B')),
    # Snow Storm: nord5, nord6, nord4, nord0, nord3; Polar Night: nord0, nord1, nord3, nord4.
    # Roles: nord13 yellow, nord7 frost, nord10 or nord9 blue, nord15 purple, nord11 red.
    ('nord', 'Nord',
     dict(paper='#E5E9F0', surface='#ECEFF4', tray='#D8DEE9', ink='#2E3440', muted='#4C566A',
          rule='#CBD2DE', product='#816423', lead='#45706F', dev='#496B95',
          review='#815E7B', you='#A64B55', on_role='#FFFFFF'),
     dict(paper='#2E3440', surface='#3B4252', tray='#272C36', ink='#D8DEE9', muted='#AEB6C4',
          rule='#4C566A', product='#EBCB8B', lead='#8FBCBB', dev='#90B1D1',
          review='#C9A2C2', you='#F6929A', on_role='#272C36')),
]
PALETTE_SOURCES = [('Catppuccin', 'https://catppuccin.com/palette/'), ('Nord', 'https://www.nordtheme.com/docs/colors-and-palettes')]

# One variable woff2 per family, latin subset: (family, file, weight range).
FACES = [('Bricolage Grotesque', 'bricolage-grotesque.woff2', '600 700'),
         ('Instrument Sans', 'instrument-sans.woff2', '400 700'),
         ('JetBrains Mono', 'jetbrains-mono.woff2', '600 700')]
# The approval diamond, as the tab icon.
ICON = ('data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22>'
        '<rect x=%223.5%22 y=%223.5%22 width=%229%22 height=%229%22 rx=%221%22 '
        'transform=%22rotate(45 8 8)%22 fill=%22%23C02E48%22/></svg>')
