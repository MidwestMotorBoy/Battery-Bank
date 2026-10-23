"""Build the thermal-circuit page from renders/network.json. Run: python build_network_page.py OUT.html"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, 'renders', 'network.json')))
html = open(os.path.join(HERE, 'network_template.html')).read().replace('/*NETWORK*/', json.dumps(d, ensure_ascii=False))
open(sys.argv[1], 'w').write(html); print('wrote', sys.argv[1])
