#!/bin/bash
# Install Chrome + ChromeDriver + Python deps in any Odoo Docker container.
# Usage: bash install_chrome_docker.sh [container_name]
# Default container: o17-odoo-1

set -e

CONTAINER=${1:-o17-odoo-1}

echo "=== Installing dependencies in container: $CONTAINER ==="
echo ""

# Find the install_deps.sh script inside the container
SCRIPT_PATH="/mnt/custom-addons/albanian_tech_map/scripts/install_deps.sh"

# Check if the internal script exists
if docker exec $CONTAINER test -f "$SCRIPT_PATH"; then
    echo "Running install_deps.sh inside $CONTAINER..."
    docker exec -u root $CONTAINER bash "$SCRIPT_PATH"
else
    echo "ERROR: $SCRIPT_PATH not found in container."
    echo "Make sure albanian_tech_map is mounted at /mnt/custom-addons/"
    exit 1
fi

echo ""
echo "=== Done! Container $CONTAINER is ready. ==="
echo "Run scraper: docker exec -d $CONTAINER python3 /mnt/custom-addons/albanian_tech_map/scripts/run_scraper_docker.py"
