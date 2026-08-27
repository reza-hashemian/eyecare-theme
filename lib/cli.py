"""eyecare-theme CLI: preview, pick, apply, auto day/night switching."""
import argparse, datetime, json, os, sys
from pathlib import Path
import core, appliers
from core import (load_config, save_config, load_state, save_state, load_themes, get_theme,
                  themes_by_mode, current_period, contrast_ratio, warm_theme, parse_hhmm,
                  CONFIG_FILE, config_dir)

RESET = "\033[0m"

def _sgr(hexcolor, fg=True):
    h = hexcolor.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"\033[{38 if fg else 48};2;{r};{g};{b}m"

def _truecolor():
    return os.environ.get("COLORTERM", "") in ("truecolor", "24bit") or sys.platform == "win32"

def render_preview(t, width=64):
    """Print a code-sample swatch using the theme's own colors via truecolor SGR."""
    bg, fg, p = t["bg"], t["fg"], t["palette"]
    B = _sgr(bg, fg=False)
    def line(parts):
        s = B
        for color, text in parts:
            s += _sgr(color) + text
        pad = width - sum(len(x[1]) for x in parts)
        return s + " " * max(0, pad) + RESET
    cr = contrast_ratio(bg, fg)
    out = []
    out.append(line([(fg, f"  {t['name']}  ")]))
    out.append(line([(fg, "  ")]))
    out.append(line([(p[13], "  def "), (p[12], "fetch_user"), (fg, "("), (p[11], "uid"), (fg, ": "),
                     (p[14], "int"), (fg, ") -> "), (p[14], "User"), (fg, ":")]))
    out.append(line([(fg, "      "), (p[8], "# look up a single user by id")]))
    out.append(line([(fg, "      "), (p[13], "if not "), (fg, "uid "), (p[13], "or "),
                     (fg, "uid < "), (p[9], "0"), (fg, ":")]))
    out.append(line([(fg, "          "), (p[13], "raise "), (p[11], "ValueError"), (fg, "("),
                     (p[10], '"bad id"'), (fg, ")")]))
    out.append(line([(fg, "      "), (p[13], "return "), (fg, "db.get("), (p[10], '"users"'), (fg, ", uid)")]))
    out.append(line([(fg, "  ")]))
    out.append(line([(p[10], "  + added line"), (fg, "   "), (p[9], "- removed line"),
                     (fg, "   "), (p[11], "~ modified")]))
    out.append(line([(fg, "  "), (p[2], "$ "), (fg, "git status "), (p[6], "main "), (p[3], "*2 "), (p[1], "!1")]))
    out.append(line([(fg, "  ")]))
    s = B + "  "
    for c in p[:8]:
        s += _sgr(c, fg=False) + "  "
    s += B + " "
    for c in p[8:]:
        s += _sgr(c, fg=False) + "  "
    s += B + " " * max(0, width - 2 - 16 - 16 - 1) + RESET
    out.append(s)
    out.append(line([(fg, f"  #{t['rank']} {t['mode']}   score {t.get('comfort_score', 0):.0f}/100"
                          f"   contrast {cr:.1f}:1   warmth {t['warmth']}/10")]))
    out.append(line([(fg, "  ")]))
    print("\n".join(out))
    print(f"  \033[2m{t['notes']}\033[0m\n")

def cmd_list(args):
    ts = load_themes()
    if args.mode:
        ts = [t for t in ts if t["mode"] == args.mode]
    for mode in ("dark", "light"):
        sel = sorted([t for t in ts if t["mode"] == mode], key=lambda x: x["rank"])
        if not sel:
            continue
        print(f"\n\033[1m{mode.upper()} — ranked best-to-worst for eye comfort\033[0m")
        for t in sel:
            cr = contrast_ratio(t["bg"], t["fg"])
            print(f"  #{t['rank']}  {t['id']:<20} {t['name']:<30} "
                  f"score {t.get('comfort_score', 0):5.1f}  contrast {cr:4.1f}:1  warmth {t['warmth']}/10")
            print(f"      \033[2m{t['notes']}\033[0m")
    print()

def cmd_preview(args):
    if not _truecolor():
        print("\033[33mnote: COLORTERM is not truecolor; swatches may look wrong.\033[0m\n")
    if args.theme:
        ts = [get_theme(args.theme)]
    else:
        ts = sorted(load_themes(), key=lambda t: (t["mode"] != "dark", t["rank"]))
        if args.mode:
            ts = [t for t in ts if t["mode"] == args.mode]
    for t in ts:
        render_preview(t)

def _prompt(msg, default=None):
    try:
        v = input(msg).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(130)
    return v or (default or "")

def cmd_pick(args):
    """Interactive: preview each theme, choose day + night, save, apply."""
    cfg = load_config()
    print("\n\033[1mEye-comfort theme picker\033[0m")
    print("Themes are shown ranked best-first. Pick one for day and one for night.\n")
    chosen = {}
    for period, mode_hint in (("day", None), ("night", "dark")):
        pool = sorted(load_themes(), key=lambda t: (t["mode"] != "dark", t["rank"]))
        if period == "night":
            pool = [t for t in pool if t["mode"] == "dark"]
        print(f"\n\033[1m=== {period.upper()} theme ===\033[0m")
        if period == "night":
            print("(only dark themes are offered for night)\n")
        for i, t in enumerate(pool, 1):
            print(f"\033[1m[{i}]\033[0m", end=" ")
            render_preview(t)
        default_idx = 1
        while True:
            v = _prompt(f"{period} theme number [1-{len(pool)}] (default {default_idx}): ", str(default_idx))
            try:
                n = int(v)
                if 1 <= n <= len(pool):
                    chosen[period] = pool[n-1]["id"]
                    break
            except ValueError:
                pass
            print("  please enter a valid number")
        print(f"  -> {period}: {get_theme(chosen[period])['name']}")
    cfg["day_theme"], cfg["night_theme"] = chosen["day"], chosen["night"]
    ds = _prompt(f"\nDay starts at (HH:MM) [{cfg['day_start']}]: ", cfg["day_start"])
    ns = _prompt(f"Night starts at (HH:MM) [{cfg['night_start']}]: ", cfg["night_start"])
    try:
        parse_hhmm(ds); parse_hhmm(ns)
        cfg["day_start"], cfg["night_start"] = ds, ns
    except ValueError as e:
        print(f"  \033[33m{e} — keeping previous times\033[0m")
    avail = appliers.detect_available()
    print(f"\nDetected on this machine: {', '.join(avail) or 'nothing'}")
    v = _prompt("Apply to all detected apps? [Y/n]: ", "y")
    if v.lower().startswith("n"):
        picked = _prompt(f"Comma-separated subset ({','.join(avail)}): ", ",".join(avail))
        cfg["targets"] = [x.strip() for x in picked.split(",") if x.strip()]
    else:
        cfg["targets"] = ["auto"]
    save_config(cfg)
    print(f"\nSaved to {CONFIG_FILE}")
    args2 = argparse.Namespace(theme=None, warm=None, dry_run=False, targets=None)
    cmd_apply(args2)

def _resolve_targets(cfg, override=None):
    if override:
        return [x.strip() for x in override.split(",") if x.strip()]
    tg = cfg.get("targets") or ["auto"]
    if "auto" in tg:
        return appliers.detect_available()
    return tg

def _night_warmth(cfg, now=None):
    """Extra warm shift applied during night hours only."""
    return float(cfg.get("night_warmth", 0.0))

def cmd_apply(args):
    cfg = load_config()
    if args.theme:
        t = get_theme(args.theme)
        period = t["mode"]
    else:
        period = current_period(cfg)
        t = get_theme(cfg[f"{period}_theme"])
    warm = args.warm if args.warm is not None else (_night_warmth(cfg) if period == "night" else 0.0)
    if warm:
        t = warm_theme(t, max(0.0, min(1.0, warm)))
    targets = _resolve_targets(cfg, args.targets)
    print(f"\n\033[1m{t['name']}\033[0m  ({period})")
    if args.dry_run:
        print(f"  dry-run; would apply to: {', '.join(targets)}\n")
        render_preview(t)
        return
    ok_n = 0
    for name in targets:
        fn = appliers.TARGETS.get(name)
        if not fn:
            print(f"  \033[33mskip\033[0m  {name}: unknown target")
            continue
        try:
            ok, msg = fn(t)
        except Exception as e:
            ok, msg = False, f"error: {e}"
        if ok:
            ok_n += 1
            print(f"  \033[32m ok \033[0m  {msg}")
        else:
            print(f"  \033[33mskip\033[0m  {name}: {msg}")
    save_state({"theme": t["id"], "base": t["id"].replace("-warm",""), "period": period,
                "at": datetime.datetime.now().isoformat(timespec="seconds")})
    print(f"\n{ok_n}/{len(targets)} applied. "
          f"Open a NEW terminal window/tab for terminal changes to show.\n")

def cmd_auto(args):
    """Apply whatever the clock says. Idempotent — safe to run every minute."""
    cfg = load_config()
    if not cfg.get("auto_switch", True) and not args.force:
        print("auto_switch is disabled in config")
        return
    period = current_period(cfg)
    want = cfg[f"{period}_theme"]
    warm = _night_warmth(cfg) if period == "night" else 0.0
    want_id = want + ("-warm" if warm else "")
    st = load_state()
    if st.get("theme") == want_id and not args.force:
        if not args.quiet:
            print(f"already on {want_id} ({period}); nothing to do")
        return
    ns = argparse.Namespace(theme=None, warm=None, dry_run=False, targets=None)
    cmd_apply(ns)

def cmd_status(args):
    cfg, st = load_config(), load_state()
    period = current_period(cfg)
    print(f"\n\033[1mconfig\033[0m   {CONFIG_FILE}")
    print(f"  day   {cfg['day_start']} -> {cfg['day_theme']}")
    print(f"  night {cfg['night_start']} -> {cfg['night_theme']}")
    print(f"  night_warmth  {cfg.get('night_warmth', 0.0)}")
    print(f"  targets       {', '.join(cfg.get('targets', []))}")
    print(f"  auto_switch   {cfg.get('auto_switch', True)}")
    print(f"\n\033[1mnow\033[0m      {datetime.datetime.now():%H:%M} -> period \033[1m{period}\033[0m "
          f"(should be {cfg[f'{period}_theme']})")
    print(f"\033[1mapplied\033[0m  {st.get('theme','(never)')} at {st.get('at','-')}")
    print(f"\n\033[1mdetected\033[0m {', '.join(appliers.detect_available()) or 'nothing'}\n")

def cmd_set(args):
    """Validate every pair first, then save — so one bad value never applies a partial change."""
    cfg = load_config()
    staged, errs = {}, []
    for kv in args.pairs:
        if "=" not in kv:
            errs.append(f"{kv}: want key=value"); continue
        k, v = kv.split("=", 1)
        k = k.strip()
        try:
            if k in ("day_theme", "night_theme"):
                get_theme(v); staged[k] = v
            elif k in ("day_start", "night_start"):
                parse_hhmm(v); staged[k] = v
            elif k == "night_warmth":
                f = float(v)
                if not 0 <= f <= 1:
                    raise ValueError("night_warmth must be between 0 and 1")
                staged[k] = f
            elif k == "auto_switch":
                staged[k] = v.lower() in ("1", "true", "yes", "on")
            elif k == "targets":
                vals = [x.strip() for x in v.split(",") if x.strip()]
                bad = [x for x in vals if x != "auto" and x not in appliers.TARGETS]
                if bad:
                    raise ValueError(f"unknown target(s): {', '.join(bad)}")
                staged[k] = vals
            else:
                errs.append(f"{k}: unknown key")
        except KeyError as e:
            errs.append(f"{k}: {e.args[0] if e.args else e}")
        except ValueError as e:
            errs.append(f"{k}: {e}")
    if errs:
        for e in errs:
            print(f"\033[31merror:\033[0m {e}", file=sys.stderr)
        print("\nnothing saved.", file=sys.stderr)
        return 2
    cfg.update(staged)
    save_config(cfg)
    for k, v in staged.items():
        print(f"  {k} = {v}")
    print(f"\nsaved {CONFIG_FILE}\n")

def cmd_detect(args):
    for n in appliers.detect_available():
        print(n)

def cmd_restore(args):
    d = core.BACKUP_DIR
    if not d.exists():
        print("no backups"); return
    files = sorted(d.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files[:40]:
        print(f"  {f.name}")
    print(f"\nBackups live in {d}. Copy one back over the original by hand to restore.\n")

def build_parser():
    p = argparse.ArgumentParser(prog="eyecare-theme",
        description="Eye-comfort themes for terminals and code editors, with day/night auto-switching.")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("list", help="list themes ranked by eye comfort")
    s.add_argument("--mode", choices=["dark","light"])
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("preview", help="show live color swatches in this terminal")
    s.add_argument("theme", nargs="?")
    s.add_argument("--mode", choices=["dark","light"])
    s.set_defaults(func=cmd_preview)

    s = sub.add_parser("pick", help="interactive wizard: preview, choose day+night, save, apply")
    s.set_defaults(func=cmd_pick)

    s = sub.add_parser("apply", help="apply a theme now")
    s.add_argument("theme", nargs="?", help="theme id; omit to use the clock")
    s.add_argument("--warm", type=float, help="extra warm shift 0..1")
    s.add_argument("--targets", help="comma-separated targets, overrides config")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_apply)

    s = sub.add_parser("auto", help="apply the theme the clock calls for (for cron/timer)")
    s.add_argument("--force", action="store_true")
    s.add_argument("--quiet", action="store_true")
    s.set_defaults(func=cmd_auto)

    s = sub.add_parser("status", help="show config, current period and last applied")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("set", help="set config keys, e.g. set night_theme=nord night_start=20:30")
    s.add_argument("pairs", nargs="+")
    s.set_defaults(func=cmd_set)

    s = sub.add_parser("detect", help="list apps found on this machine")
    s.set_defaults(func=cmd_detect)

    s = sub.add_parser("restore", help="list config backups")
    s.set_defaults(func=cmd_restore)
    return p

def main(argv=None):
    p = build_parser()
    a = p.parse_args(argv)
    if not getattr(a, "func", None):
        p.print_help(); return 0
    try:
        a.func(a)
    except KeyError as e:
        print(f"\033[31merror:\033[0m {e}", file=sys.stderr); return 2
    except ValueError as e:
        print(f"\033[31merror:\033[0m {e}", file=sys.stderr); return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
