#!/usr/bin/env bash
# Remove the scheduler and PATH symlink. Config and backups are kept.
set -euo pipefail
rm -f "$HOME/.local/bin/eyecare-theme"
if [ "$(uname -s)" = "Darwin" ]; then
  P="$HOME/Library/LaunchAgents/com.eyecare.theme.plist"
  launchctl unload "$P" 2>/dev/null || true; rm -f "$P"
else
  systemctl --user disable --now eyecare-theme.timer 2>/dev/null || true
  rm -f "$HOME/.config/systemd/user/eyecare-theme."{timer,service}
  systemctl --user daemon-reload 2>/dev/null || true
  if command -v crontab >/dev/null 2>&1; then
    T="$(mktemp)"; crontab -l 2>/dev/null | grep -v eyecare-theme > "$T" || true
    crontab "$T"; rm -f "$T"
  fi
fi
echo "  removed. Config kept at ~/.config/eyecare-theme (delete by hand if you want)."
echo "  Original app configs are in ~/.config/eyecare-theme/backups/"
