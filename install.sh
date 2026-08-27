#!/usr/bin/env bash
# Install eyecare-theme: PATH symlink + day/night auto-switch scheduler.
# Linux (systemd user timer or cron) and macOS (launchd).
set -euo pipefail
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
BIN="$DIR/eyecare-theme"
chmod +x "$BIN" 2>/dev/null || true

say() { printf '  %s\n' "$*"; }

# ---- 1. put it on PATH ----
TARGET="$HOME/.local/bin"
mkdir -p "$TARGET"
ln -sf "$BIN" "$TARGET/eyecare-theme"
say "linked $TARGET/eyecare-theme"
case ":$PATH:" in
  *":$TARGET:"*) ;;
  *) say "NOTE: $TARGET is not on your PATH. Add to ~/.bashrc or ~/.zshrc:"
     say '      export PATH="$HOME/.local/bin:$PATH"' ;;
esac

# ---- 2. scheduler ----
OS="$(uname -s)"
if [ "$OS" = "Darwin" ]; then
  PLIST="$HOME/Library/LaunchAgents/com.eyecare.theme.plist"
  mkdir -p "$(dirname "$PLIST")"
  cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.eyecare.theme</string>
  <key>ProgramArguments</key>
  <array><string>$BIN</string><string>auto</string><string>--quiet</string></array>
  <key>StartInterval</key><integer>300</integer>
  <key>RunAtLoad</key><true/>
</dict></plist>
PL
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  say "launchd agent installed (checks every 5 min)"

elif command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
  UD="$HOME/.config/systemd/user"
  mkdir -p "$UD"
  cat > "$UD/eyecare-theme.service" <<SV
[Unit]
Description=Apply the eye-comfort theme for the current time of day

[Service]
Type=oneshot
ExecStart="$BIN" auto --quiet
SV
  cat > "$UD/eyecare-theme.timer" <<TM
[Unit]
Description=Check every 5 minutes whether the day/night theme should change

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
TM
  systemctl --user daemon-reload
  systemctl --user enable --now eyecare-theme.timer
  say "systemd user timer enabled (checks every 5 min)"
  say "status: systemctl --user status eyecare-theme.timer"

elif command -v crontab >/dev/null 2>&1; then
  TMP="$(mktemp)"
  crontab -l 2>/dev/null | grep -v 'eyecare-theme' > "$TMP" || true
  echo "*/5 * * * * \"$BIN\" auto --quiet >/dev/null 2>&1" >> "$TMP"
  crontab "$TMP"; rm -f "$TMP"
  say "cron job installed (checks every 5 min)"
else
  say "WARNING: no systemd/launchd/cron found — auto-switching not scheduled."
  say "         You can still run 'eyecare-theme apply' by hand."
fi

echo
say "Done. Next step:  eyecare-theme pick"
