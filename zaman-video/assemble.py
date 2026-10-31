"""Assemble index.html: shared engine (from ../ruh-video/index.html) + this topic's scenes.html and build.js."""
import re
src = open('../ruh-video/index.html', encoding='utf-8').read().split('\n')
head = '\n'.join(src[:67])                      # <head> + stage chrome
tail_html = '\n'.join(src[160:166])             # caption/tag/vignette + </div> + <script>
helpers = '\n'.join(src[166:227])               # helpers (svgEl, figure, check, circleNum...)
engine = '\n'.join(src[525:])                   # prepDraw, render, captions, setup
head = head.replace('<title>Seni sen yapan şey nedir? · İsrâ 85</title>', '<title>Allah katında zaman nedir? · Hac 47 · Secde 5</title>')
head = head.replace('</style>', '.hdr{font-size:34px;font-weight:700;color:var(--navy);white-space:nowrap}\n</style>')
tail_html = tail_html.replace('Seni sen yapan şey nedir? · İsrâ 85', 'Allah katında zaman nedir? · Hac 47 · Secde 5')
engine = engine.replace('  renderCaption(t);\n}', '  hooks.forEach(h => h(t));\n  renderCaption(t);\n}', 1)
out = '\n'.join([head, open('scenes.html', encoding='utf-8').read(), tail_html, helpers,
                 open('build.js', encoding='utf-8').read(), engine])
assert 'hooks.forEach' in out
open('index.html', 'w', encoding='utf-8').write(out)
print('ok', len(out))
