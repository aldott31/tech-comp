#!/bin/bash
# Install Chrome + ChromeDriver + Python deps INSIDE an Odoo Docker container.
# Run as root: docker exec -u root <container> bash /mnt/custom-addons/albanian_tech_map/scripts/install_deps.sh
set -e

echo "=== 1/4 Installing wget and unzip ==="
apt-get update -qq && apt-get install -y -qq wget unzip >/dev/null 2>&1
echo "[OK] wget and unzip installed"

echo "=== 2/4 Installing Google Chrome ==="
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - 2>/dev/null
echo 'deb http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list
apt-get update -qq && apt-get install -y -qq google-chrome-stable >/dev/null 2>&1
CHROME_VER=$(google-chrome-stable --version | grep -oP '\d+\.\d+\.\d+\.\d+')
echo "[OK] Chrome $CHROME_VER installed"

echo "=== 3/4 Installing ChromeDriver (matching Chrome $CHROME_VER) ==="
cd /tmp
wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VER}/linux64/chromedriver-linux64.zip"
unzip -q chromedriver-linux64.zip
mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
chmod +x /usr/local/bin/chromedriver
rm -rf chromedriver-linux64*
echo "[OK] ChromeDriver installed"

echo "=== 4/4 Installing Python packages ==="
pip3 install -q selenium==4.40.0 beautifulsoup4 lxml geopy 2>/dev/null
echo "[OK] Python packages installed"

echo ""
echo "=== Verification ==="
google-chrome-stable --version
chromedriver --version
python3 -c "import selenium; print('selenium', selenium.__version__)"
python3 -c "from bs4 import BeautifulSoup; print('bs4 OK')"
python3 -c "import geopy; print('geopy OK')"
echo ""
echo "=== All dependencies installed successfully ==="
echo "You can now run the scraper from Odoo UI or directly:"
echo "  python3 $(dirname $0)/run_scraper_docker.py"
