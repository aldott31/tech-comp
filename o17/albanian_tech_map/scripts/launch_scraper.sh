#!/bin/bash
# Launcher that creates a truly independent process for the scraper.
# This is needed because chromedriver exits with -5 (SIGTRAP) when
# launched as a child of any Odoo process.

# Reset all signal handlers to defaults
trap - EXIT HUP INT QUIT PIPE TERM ALRM USR1 USR2

# Use setsid to create a new session (fully detached from parent)
exec setsid python3 /mnt/custom-addons/albanian_tech_map/scripts/run_scraper_docker.py > /tmp/scraper.log 2>&1
