import re
import sys
with open('frontend/dist/assets/index-Oueheec7.js', 'r', encoding='utf-8') as f:
    s = f.read()
matches = re.findall(r'http://[^\s\"]+', s)
for m in matches:
    print(m)
