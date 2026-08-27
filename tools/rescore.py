#!/usr/bin/env python3
"""Recompute contrast, comfort_score and rank for every theme in themes/themes.json.
Run after editing any theme's colors so the ranking stays honest."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import core

def score(t):
    c = t["contrast"]
    if   c < 4.5:   cs = 0.35
    elif c < 6.0:   cs = 0.65
    elif c < 7.0:   cs = 0.85
    elif c <= 11.0: cs = 1.00
    elif c <= 13.0: cs = 0.75
    else:           cs = 0.50
    ws = 0.5 + 0.05 * t["warmth"]
    return round(100 * (0.62 * cs + 0.38 * ws), 1)

def main():
    p = core.THEMES_FILE
    d = json.loads(p.read_text(encoding="utf-8"))
    for t in d["themes"]:
        t["contrast"] = round(core.contrast_ratio(t["bg"], t["fg"]), 1)
        t["comfort_score"] = score(t)
    for mode in ("dark", "light"):
        sel = [t for t in d["themes"] if t["mode"] == mode]
        sel.sort(key=lambda t: (-t["comfort_score"], -t["warmth"]))
        for i, t in enumerate(sel, 1):
            t["rank"] = i
    d["themes"].sort(key=lambda t: (t["mode"] != "dark", t["rank"]))
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    for t in d["themes"]:
        print(f"{t['mode']:5} #{t['rank']} {t['id']:<18} score {t['comfort_score']:5} "
              f"contrast {t['contrast']:5} warmth {t['warmth']}")

if __name__ == "__main__":
    main()
