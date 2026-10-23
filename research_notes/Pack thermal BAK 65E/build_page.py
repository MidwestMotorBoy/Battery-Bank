"""Assemble the HTML report from renders/series.json, renders/summary.json and the page text (page_text.json).
Run: python build_page.py OUT_DIR -> OUT_DIR/index.html plus the case PNGs beside it"""
import os, sys, json, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); RD = os.path.join(HERE, 'renders')
out = os.path.abspath(sys.argv[1]); os.makedirs(out, exist_ok=True)
series = json.load(open(os.path.join(RD, 'series.json')))
summary = json.load(open(os.path.join(RD, 'summary.json')))
text = json.load(open(os.path.join(HERE, 'page_text.json')))
html = open(os.path.join(HERE, 'page_template.html')).read()
html = html.replace('/*SERIES*/', json.dumps(series, separators=(',', ':'))).replace('/*SUMMARY*/', json.dumps(summary))
html = html.replace('/*FILL*/', open(os.path.join(RD, 'fill.json')).read()).replace('/*SENS*/', open(os.path.join(RD, 'sensitivity.json')).read())
html = html.replace('/*TEXT*/', json.dumps(text, ensure_ascii=False))
open(os.path.join(out, 'index.html'), 'w').write(html)
for f in os.listdir(RD):
    if f.endswith('.png') and not f.startswith('zz'): shutil.copy(os.path.join(RD, f), os.path.join(out, f))
print('wrote', out)
