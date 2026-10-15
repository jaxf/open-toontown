# Launch on macOS

Double-click **start-all.command** in Finder. It uses Homebrew Python 3.9 and
starts Astron, UberDOG, the AI district, then the game in one Terminal window.
Close any manually started servers first; the launcher refuses to duplicate a
running local server. Each service must become ready before the next starts.

Quit the game or press Control+C in the launcher to stop the stack it started.
Individual logs are retained under `local/launcher-logs/` in the repository.
On failure, the launcher leaves its message visible until you press Return.

The existing individual `.sh` launchers remain available. The all-in-one launcher
uses the same game account, server configuration and Python installation.
