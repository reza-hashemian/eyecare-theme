"""Core: platform detection, config, theme loading, color helpers."""
import json, os, sys, platform, shutil, subprocess, datetime, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES_FILE = ROOT / "themes" / "themes.json"

def config_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "eyecare-theme"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "eyecare-theme"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "eyecare-theme"

CONFIG_FILE = config_dir() / "config.json"
STATE_FILE = config_dir() / "state.json"
BACKUP_DIR = config_dir() / "backups"

DEFAULT_CONFIG = {
    "day_theme": "gruvbox-dark",
    "night_theme": "gruvbox-dark",
    "day_start": "07:00",
    "night_start": "19:00",
    "targets": ["auto"],
    "auto_switch": True,
}

# ---------- config ----------
def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"warning: could not parse {CONFIG_FILE}: {e}", file=sys.stderr)
    return cfg

def save_config(cfg):
    config_dir().mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_state(st):
    config_dir().mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(st, indent=2), encoding="utf-8")

# ---------- themes ----------
def load_themes():
    return json.loads(THEMES_FILE.read_text(encoding="utf-8"))["themes"]

def get_theme(tid):
    for t in load_themes():
        if t["id"] == tid:
            return t
    raise KeyError(f"unknown theme id: {tid}")

def themes_by_mode(mode):
    ts = [t for t in load_themes() if t["mode"] == mode]
    return sorted(ts, key=lambda t: t["rank"])

# ---------- color helpers ----------
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)

def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminance(h):
    r, g, b = hex_to_rgb(h)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)

def contrast_ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def warm_shift(h, strength):
    """Shift a color toward warm (reduce blue, slightly lift red). strength 0..1."""
    r, g, b = hex_to_rgb(h)
    b = b * (1 - 0.28 * strength)
    g = g * (1 - 0.09 * strength)
    r = min(255, r * (1 + 0.05 * strength))
    return rgb_to_hex((r, g, b))

def warm_theme(theme, strength):
    """Return a copy of theme with all colors warm-shifted."""
    if strength <= 0:
        return theme
    t = json.loads(json.dumps(theme))
    for k in ("bg", "fg", "cursor", "selection_bg", "selection_fg"):
        if t.get(k):
            t[k] = warm_shift(t[k], strength)
    t["palette"] = [warm_shift(c, strength) for c in t["palette"]]
    t["id"] = t["id"] + "-warm"
    t["name"] = t["name"] + f" (warm {int(strength*100)}%)"
    return t

# ---------- time ----------
def parse_hhmm(s):
    m = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", s or "")
    if not m:
        raise ValueError(f"bad time (want HH:MM): {s!r}")
    h, mi = int(m.group(1)), int(m.group(2))
    if not (0 <= h < 24 and 0 <= mi < 60):
        raise ValueError(f"time out of range: {s!r}")
    return h * 60 + mi

def current_period(cfg, now=None):
    now = now or datetime.datetime.now()
    cur = now.hour * 60 + now.minute
    day, night = parse_hhmm(cfg["day_start"]), parse_hhmm(cfg["night_start"])
    if day == night:
        return "day"
    if day < night:
        return "day" if day <= cur < night else "night"
    # day_start after night_start (night wraps midnight the other way)
    return "night" if night <= cur < day else "day"

# ---------- platform ----------
def which(cmd):
    return shutil.which(cmd)

def run(cmd, **kw):
    """Run a command, return (rc, stdout, stderr). Never raises."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=25, **kw)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return 1, "", str(e)

def backup(path: Path):
    """Copy path into the backup dir once per run-timestamp. Returns backup path or None."""
    path = Path(path)
    if not path.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"{path.name}.{stamp}.bak"
    try:
        shutil.copy2(path, dest)
        return dest
    except Exception:
        return None
