#!/bin/bash
# Install Chrome + ChromeDriver + Python deps INSIDE an Odoo Docker container.
# Run as root: docker exec -u root <container> bash /mnt/custom-addons/albanian_tech_map/scripts/install_deps.sh
set -e

echo "=== Albanian Tech Map Dependency Installer ==="
echo "=== For Odoo 18 Docker Containers ==="
echo ""

echo "=== 1/4 Installing wget and unzip ==="
apt-get update -qq 2>&1 | grep -v "^Get:" || true
apt-get install -y -qq wget unzip 2>&1 | grep -v "^Selecting\|^Preparing\|^Unpacking\|^Setting up" || true
echo "[OK] wget and unzip installed"
echo ""

echo "=== 2/4 Installing Google Chrome ==="
# Add Google signing key
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - 2>/dev/null || echo "Warning: apt-key deprecated but continuing..."

# Add Chrome repository
echo 'deb http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list

# Install Chrome
apt-get update -qq 2>&1 | grep -v "^Get:" || true
apt-get install -y -qq google-chrome-stable 2>&1 | grep -v "^Selecting\|^Preparing\|^Unpacking\|^Setting up" || true

# Get Chrome version
CHROME_VER=$(google-chrome-stable --version | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1)
echo "[OK] Chrome $CHROME_VER installed"
echo ""

echo "=== 3/4 Installing ChromeDriver (matching Chrome $CHROME_VER) ==="
cd /tmp

# Download matching ChromeDriver
echo "Downloading ChromeDriver $CHROME_VER..."
wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VER}/linux64/chromedriver-linux64.zip" || {
    echo "Error: Failed to download ChromeDriver for version $CHROME_VER"
    exit 1
}

# Extract and install
unzip -q chromedriver-linux64.zip
mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
chmod +x /usr/local/bin/chromedriver
rm -rf chromedriver-linux64*

echo "[OK] ChromeDriver $CHROME_VER installed"
echo ""

echo "=== 4/4 Installing Python packages ==="
# For Python 3.12+ with externally-managed-environment
echo "Installing: selenium, beautifulsoup4, lxml, geopy, psycopg2-binary..."

pip3 install --break-system-packages -q selenium==4.40.0 beautifulsoup4 lxml geopy psycopg2-binary 2>&1 | grep -v "^Collecting\|^Downloading\|^Installing\|^Requirement already" || true

echo "[OK] Python packages installed"
echo ""

echo "=== Verification ==="
echo "Chrome:      $(google-chrome-stable --version)"
echo "ChromeDriver: $(chromedriver --version | head -1)"
echo "Selenium:    $(python3 -c 'import selenium; print(selenium.__version__)' 2>/dev/null || echo 'Not found')"
echo "BS4:         $(python3 -c 'from bs4 import BeautifulSoup; print("OK")' 2>/dev/null || echo 'Not found')"
echo "Geopy:       $(python3 -c 'import geopy; print("OK")' 2>/dev/null || echo 'Not found')"
echo "Psycopg2:    $(python3 -c 'import psycopg2; print("OK")' 2>/dev/null || echo 'Not found')"
echo ""

echo "=== Installation Complete ==="
echo ""
echo "You can now run the scraper:"
echo "  - From Odoo UI: Tech Map → Tools → Run QKB Scraper"
echo "  - From terminal: docker exec -d <container> python3 /mnt/custom-addons/albanian_tech_map/scripts/run_scraper_docker.py"
echo "  - Monitor logs:  docker exec <container> tail -f /tmp/scraper.log"
echo ""
