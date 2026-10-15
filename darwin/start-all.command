#!/bin/bash
# Double-click in Finder; resolve paths independently of Terminal's directory.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
LAUNCH_DIR="$(cd "$(dirname "$0")" && pwd)"
if command -v python3.9 >/dev/null 2>&1; then
    python3.9 "$LAUNCH_DIR/start_all.py"
    result=$?
else
    echo 'Python 3.9 was not found. Install the Python used by your working game launcher.'
    result=1
fi
printf '\nPress Return to close this launcher.\n'
read -r _
exit "$result"
