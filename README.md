# eyecare-theme

Eye-comfort color themes for your terminal **and** your code editors, applied everywhere at
once, with automatic day/night switching based on the clock and your own preferences.

Works on **Linux, macOS and Windows**. Only needs Python 3.8+ — no pip packages.

---

## Quick start

```bash
./install.sh            # Linux / macOS   (Windows: powershell -ExecutionPolicy Bypass -File .\install.ps1)
eyecare-theme pick      # preview every theme, choose your day + night themes
```

That's it. From then on a background timer checks every 5 minutes and switches your
theme when day turns to night.

To just look at the themes without changing anything:

```bash
eyecare-theme list                  # ranked table with scores
eyecare-theme preview               # live color swatches of every theme
eyecare-theme preview gruvbox-dark  # just one
eyecare-theme apply nord --dry-run  # show what would change, change nothing
```

---

## The themes, ranked for eye comfort

Ranking is **computed, not hand-waved** (`tools/rescore.py`). Two measured inputs:

- **contrast** — the real WCAG luminance ratio between foreground and background.
  The comfort band is **7:1 to 11:1**. Below ~5:1 you squint; above ~13:1 (think black
  text on pure white) you get glare and afterimages. Both ends are penalised.
- **warmth** — how little blue is in the palette (0 cool … 10 warm). Blue light is the
  part that keeps you awake and drives late-night eye fatigue, so warmth is weighted
  heavily for night use.

### Dark

| # | id | contrast | warmth | why |
|---|----|----------|--------|-----|
| 1 | `gruvbox-dark` | 10.7:1 | 9/10 | Warm, low-saturation. No pure black, no pure white. The best all-round pick, day or night. |
| 2 | `everforest-dark` | 7.4:1 | 8/10 | Green-based, soft, explicitly designed for eye comfort. Closest rival. |
| 3 | `nord` | 9.2:1 | 3/10 | Low saturation so colors never vibrate. Great in daytime, cool for late nights. |
| 4 | `tokyonight-storm` | 9.0:1 | 2/10 | Popular and sharp, but blue-heavy. Daytime only, or pair with `night_warmth`. |
| 5 | `one-dark` | 6.6:1 | 4/10 | Familiar and balanced. Middling on both axes. |
| 6 | `solarized-dark` | 4.7:1 | 7/10 | Famous low-glare design. That low contrast is deliberate — some people love it, others find it too dim. **Try it before you commit.** |

### Light

| # | id | contrast | warmth | why |
|---|----|----------|--------|-----|
| 1 | `gruvbox-light` | 10.2:1 | 9/10 | Warm paper-like background. Best light theme for long sessions. |
| 2 | `everforest-light` | 5.2:1 | 8/10 | Gentler and softer, but noticeably fainter text. |
| 3 | `solarized-light` | 4.1:1 | 8/10 | Cream background kills glare; text is faint. Good in a dim room, hard in a bright one. |
| 4 | `github-light` | 14.7:1 | 2/10 | Pure white, very high contrast. Only for bright rooms; harshest of the set. |

**If you don't want to think about it:** `gruvbox-dark` for both day and night is the
safest answer. If you prefer a light theme while the sun is up, use `gruvbox-light` for
day and `gruvbox-dark` for night.

---

## Day / night switching

Set your own schedule and your own theme for each half:

```bash
eyecare-theme set day_theme=gruvbox-light night_theme=gruvbox-dark
eyecare-theme set day_start=07:30 night_start=19:00
```

Night-shift schedules work too — if `day_start` is later than `night_start`, the
range simply wraps around midnight:

```bash
eyecare-theme set day_start=22:00 night_start=10:00   # "day" = 22:00 -> 10:00
```

### Extra warmth at night

Independently of which theme you pick, you can have every color shifted warmer after
dark (less blue, like Night Shift / f.lux — but baked into the theme rather than a
screen filter, so screenshots and color-critical work in the daytime stay untouched):

```bash
eyecare-theme set night_warmth=0.35    # 0 = off, 1 = maximum. 0.3-0.4 is a good start.
```

This is the fix for "I love Tokyo Night but it's too blue at 1am".

### Checking on it

```bash
eyecare-theme status     # config, which period it thinks it is now, what was last applied
eyecare-theme auto       # force the check that the timer runs
```

---

## What gets themed

Whatever is actually installed — everything else is skipped silently.

**Terminals:** Alacritty (both the old YAML and new TOML formats), kitty, WezTerm,
GNOME Terminal, Konsole, XFCE Terminal, Windows Terminal, iTerm2.

**Editors:** VS Code (plus Insiders, VSCodium, Cursor), all JetBrains IDEs
(PyCharm, IntelliJ, WebStorm, GoLand, CLion, Rider, DataGrip, …), Neovim.

**Desktop:** on GNOME the system light/dark preference is matched too, so window
chrome doesn't flash white around a dark editor.

See exactly what was found on your machine:

```bash
eyecare-theme detect
```

Limit it to certain apps:

```bash
eyecare-theme set targets=vscode,alacritty     # or targets=auto for everything
eyecare-theme apply --targets kitty            # one-off override
```

---

## Notes per app

- **Terminals** — changes apply to **newly opened** windows or tabs. Existing ones keep
  their old colors (kitty is the exception; running instances update live).
- **VS Code** — the matching theme extension is installed automatically via the `code`
  CLI when one is needed, then the theme is selected. It also colors the integrated
  terminal to match. Takes effect immediately.
- **JetBrains** — the IDE must be **restarted** to pick up the change; it rewrites
  config files that a running IDE would otherwise overwrite on exit. If the theme's
  plugin isn't installed, it falls back to bundled Darcula/Light and tells you so.
  To get the real thing, install the plugin from Settings → Plugins (name is in
  `themes/themes.json` under `jetbrains_plugin`).
- **Neovim** — needs the matching colorscheme plugin installed; it fails soft
  (`silent! colorscheme`) and keeps your current colors if it's missing.

---

## Safety

Every file is **backed up before it is touched**, timestamped, to:

```
~/.config/eyecare-theme/backups/     (Linux)
~/Library/Application Support/eyecare-theme/backups/     (macOS)
%APPDATA%\eyecare-theme\backups\     (Windows)
```

`eyecare-theme restore` lists them. Your existing settings are preserved — VS Code's
`settings.json` is parsed with comment support and only theme keys are rewritten;
terminal configs get an `include`/`import` line rather than being overwritten.

To remove the scheduler and PATH entry (config and backups are kept):

```bash
./uninstall.sh
```

---

## Adding your own theme

Add an entry to `themes/themes.json` — copy an existing one, change the colors
(`bg`, `fg`, `cursor`, `selection_*`, and the 16-color `palette`), set `warmth`
by eye, then:

```bash
python3 tools/rescore.py
```

That measures the real contrast and re-ranks everything, so your theme lands in the
list in the right place.

---

## Commands

| command | what it does |
|---------|--------------|
| `pick` | interactive wizard — preview all, choose day + night, save, apply |
| `list` | ranked table of every theme |
| `preview [id]` | live color swatches in your terminal |
| `apply [id]` | apply now (no id = whatever the clock says); `--dry-run`, `--warm`, `--targets` |
| `auto` | apply what the clock calls for, skip if already correct (this is what the timer runs) |
| `status` | current config, period and last-applied theme |
| `set k=v …` | change config; validates everything before saving |
| `detect` | list the apps found on this machine |
| `restore` | list config backups |
