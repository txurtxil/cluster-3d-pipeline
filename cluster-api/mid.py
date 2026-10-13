import sys, re
raw = sys.stdin.read()
m = re.search(r'"mission_id"\s*:\s*"([^"]+)"', raw)
if not m:
    m = re.search(r'([a-z0-9_]+_[0-9]{6,})', raw)
print(m.group(1) if m else "")
