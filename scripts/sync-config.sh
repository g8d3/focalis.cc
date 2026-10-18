#!/bin/bash
# Sync personal values from site.config.json -> HTML fallback text for crawlers
set -e
VARIANT="${1:-variant-d-world}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CFG="$ROOT/variants/$VARIANT/site.config.json"
if [[ ! -f "$CFG" ]]; then echo "Config not found: $CFG"; exit 1; fi
PRIMARY=$(jq -r .contact.primaryEmail "$CFG")
SUPPORT=$(jq -r .contact.supportEmail "$CFG")
LEGAL=$(jq -r .company.legalName "$CFG")
LOC=$(jq -r .company.location "$CFG")
echo "Syncing $VARIANT with PRIMARY=$PRIMARY SUPPORT=$SUPPORT LEGAL=$LEGAL LOC=$LOC"
# Update fallback text in HTML (keeps data-config but updates visible text for no-JS crawlers)
cd "$ROOT/variants/$VARIANT"
for f in *.html; do
  # Use python for safe replacement
  python3 - "$f" "$PRIMARY" "$SUPPORT" "$LEGAL" "$LOC" << 'PY'
import pathlib, sys
f, primary, support, legal, loc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
text = pathlib.Path(f).read_text()
# Update fallback email text (inside data-config anchors) - keep href but update visible text
import re
text = re.sub(r'(data-config="contact\.primaryEmail"[^>]*>)[^<]+</a>', r'\1'+primary+'</a>', text)
text = re.sub(r'(data-config="contact\.supportEmail"[^>]*>)[^<]+</a>', r'\1'+support+'</a>', text)
text = re.sub(r'(data-config="company\.legalName">)[^<]+</span>', r'\1'+legal+'</span>', text)
text = re.sub(r'(data-config="company\.location">)[^<]+</span>', r'\1'+loc+'</span>', text)
pathlib.Path(f).write_text(text)
print(f"  synced {f}")
PY
done
echo "Done. Also manually update Caddyfile email if you changed primaryEmail: sites/focalis.cc/Caddyfile"
echo "And site-config.js: cp site.config.json values to assets/js/site-config.js"
