#!/bin/sh
cd ..

export LOGIN_TOKEN=dev
export PYTHONFAULTHANDLER=1

python3.9 -m toontown.launcher.QuickStartLauncher
