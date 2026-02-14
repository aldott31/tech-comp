# Albanian Tech Map - Odoo 18 Module

Interactive map of IT and digital companies in Albania, powered by automated scraping from the Albanian Business Registry (QKB).

## What It Does

- Scrapes **QKB (Qendra Kombëtare e Biznesit)** for companies whose **activity field** contains IT-related keywords
- Every discovered company is a verified tech company (matched by official business activity description)
- Stores results in Odoo with a public-facing Leaflet map at `/techmap`
- Runs automatically every 24 hours via cron job
- Provides a JSON API for external integrations

## Features

- **Activity-Based Discovery**: Searches QKB's "Objekti i aktivitetit" field with 40 IT keywords — every result is a tech company by definition
- **Standalone Scraper**: Runs as a separate process to avoid Odoo's memory limits (RLIMIT_AS)
- **Auto-Detect Database**: Scraper automatically finds the correct Odoo database
- **Public Map**: Interactive Leaflet map at `/techmap`, no login required
- **Admin Interface**: Full Odoo backend for managing, filtering, and verifying companies
- **REST API**: JSON endpoints with CORS support

## Requirements

- **Odoo 18** Community or Enterprise Edition
- **Docker** (recommended) — the scraper needs Chrome/ChromeDriver
- **PostgreSQL 12+**

## Installation

### 1. Copy the Module

Copy the `albanian_tech_map` folder into your Odoo custom addons directory:

```bash
# Example for Docker setup
cp -r albanian_tech_map /path/to/custom_addons/
```

### 2. Install Dependencies (Inside the Odoo Container)

The scraper uses Selenium with headless Chrome. Install everything with the included script:

```bash
docker exec -u root YOUR_CONTAINER bash /mnt/custom-addons/albanian_tech_map/scripts/install_deps.sh
```

Replace `YOUR_CONTAINER` with your Odoo container name (e.g., `odoo18`).

**What gets installed:**
- ✅ Google Chrome (stable, auto-versioned)
- ✅ ChromeDriver (auto-matched to Chrome version)
- ✅ Python packages: `selenium==4.40.0`, `beautifulsoup4`, `lxml`, `geopy`, `psycopg2-binary`

**Note:** The script handles Python 3.12+ externally-managed-environment automatically using `--break-system-packages`.

### 3. Install the Odoo Module

1. Restart Odoo (or update the apps list)
2. Go to **Apps** > **Update Apps List**
3. Search for **"Albanian Tech Map"**
4. Click **Install**

## Usage

### Public Map

Visit `http://your-odoo-server/techmap` — no authentication required.

Features:
- Interactive Leaflet map centered on Tirana
- Search companies by name, category, or city
- Filter by category (All / Software / Agency)
- Click markers for company details (website, email, phone, NIPT)
- Sidebar with full company list

### Running the Scraper

#### **Option 1: From Odoo UI** (Recommended)
1. Go to **Tech Map → Tools → Run QKB Scraper**
2. Click **"Run QKB Scraping Now"**
3. The system will check dependencies automatically
4. If dependencies are missing, follow the on-screen instructions
5. If everything is OK, scraper will start in background

#### **Option 2: From Command Line**
```bash
# Run scraper in background
docker exec -d YOUR_CONTAINER python3 /mnt/custom-addons/albanian_tech_map/scripts/run_scraper_docker.py

# Monitor logs (real-time)
docker exec YOUR_CONTAINER tail -f /tmp/scraper.log

# Check last 50 lines of logs
docker exec YOUR_CONTAINER tail -50 /tmp/scraper.log
```

Replace `YOUR_CONTAINER` with your container name (e.g., `odoo18`).

#### **Option 3: Automatic (Cron)**
The module creates a scheduled action that runs every 24 hours automatically.

---

### Stopping the Scraper

If you need to stop a running scraper:

```bash
# Stop the scraper process
docker exec YOUR_CONTAINER pkill -f run_scraper_docker.py

# Verify it stopped (should return no results)
docker exec YOUR_CONTAINER ps aux | grep run_scraper_docker.py
```

**Note:** The scraper runs in the background, so stopping it won't affect your Odoo instance.

---

### Quick Reference Commands

```bash
# Install dependencies (first time only)
docker exec -u root YOUR_CONTAINER bash /mnt/custom-addons/albanian_tech_map/scripts/install_deps.sh

# Run scraper manually
docker exec -d YOUR_CONTAINER python3 /mnt/custom-addons/albanian_tech_map/scripts/run_scraper_docker.py

# Monitor logs (real-time)
docker exec YOUR_CONTAINER tail -f /tmp/scraper.log

# Stop scraper
docker exec YOUR_CONTAINER pkill -f run_scraper_docker.py

# Check if scraper is running
docker exec YOUR_CONTAINER ps aux | grep run_scraper_docker.py
```

### API Endpoints

**Companies with coordinates (for map):**
```
GET /techmap/api/companies
GET /techmap/api/companies?city=tirane
```

**All companies (including those without coordinates):**
```
GET /techmap/api/companies/all
```

Response format:
```json
[
  {
    "id": 1,
    "name": "Company Name",
    "nipt": "L12345678A",
    "city": "tirane",
    "lat": 41.33,
    "lng": 19.82,
    "website": "https://example.com",
    "email": "info@example.com",
    "phone": "+355 69 123 4567",
    "category": "software",
    "is_tech": true,
    "activity_description": "Zhvillim software, web development..."
  }
]
```

### Admin Interface

Go to **Tech Map > Companies** in the Odoo backend to:
- View all companies in list, form, or kanban view
- Filter by city, category, tech status, or verification status
- Edit company details, coordinates, and contact info
- Mark companies as verified

## How the Scraper Works

1. **Searches QKB** by activity field ("Objekti i aktivitetit") with 40 IT-related keywords
2. **Filters** by Tirana district (qarku=tirane), 3 legal forms, and date ranges from 2000-2026
3. **Saves immediately** — every result has the keyword in their official activity description, so they are tech companies by definition
4. **Enriches** each company by opening the QKB detail modal to get the full activity description
5. **Writes directly to PostgreSQL** (bypasses Odoo ORM to avoid memory limits)

### Why a Standalone Script?

Odoo sets `RLIMIT_AS` to ~2.5GB, which kills Chrome/ChromeDriver with exit code -5. The standalone script resets this limit before starting Chrome, then connects directly to PostgreSQL.

## Module Structure

```
albanian_tech_map/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── tech_company.py           # Company model (tech.company)
│   └── data_scraper.py           # Launches standalone scraper
├── controllers/
│   └── main.py                   # Public map page + JSON API
├── views/
│   ├── tech_company_views.xml    # Backend list/form/search views
│   ├── tech_company_scraper_views.xml  # Scraper wizard UI
│   └── map_template.xml          # Public map template (Leaflet)
├── data/
│   ├── ir_cron.xml               # 24-hour cron job
│   └── tech_company_data.xml     # Initial seed data
├── scripts/
│   ├── run_scraper_docker.py     # Standalone QKB scraper (Selenium)
│   ├── install_deps.sh           # Install Chrome + deps inside container
│   └── install_chrome_docker.sh  # Host-side wrapper script
├── security/
│   ├── ir.model.access.csv       # Access control
│   └── security.xml              # Security groups
└── static/
    └── src/
        ├── js/map.js             # Leaflet map logic
        └── css/map.css           # Map styles
```

## Configuration

### Environment Variables (Optional)

The scraper auto-detects most settings, but you can override with env vars:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_NAME` | auto-detect | PostgreSQL database name |
| `DB_HOST` | `db` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `odoo` | PostgreSQL user |
| `DB_PASS` | `odoo` | PostgreSQL password |

### Cron Schedule

To change the scraping schedule:
1. Go to **Settings > Technical > Scheduled Actions**
2. Find **"Albanian Tech Map: Daily QKB Update"**
3. Adjust the interval

## Troubleshooting

### Dependencies Missing Error
If you see "Dependencies Missing" notification when running the scraper:

```bash
# Install all dependencies
docker exec -u root YOUR_CONTAINER bash /mnt/custom-addons/albanian_tech_map/scripts/install_deps.sh

# Verify installation
docker exec YOUR_CONTAINER google-chrome-stable --version
docker exec YOUR_CONTAINER chromedriver --version
docker exec YOUR_CONTAINER python3 -c "import selenium; print('Selenium OK')"
```

### Scraper Won't Start
```bash
# Check if dependencies are installed
docker exec YOUR_CONTAINER google-chrome-stable --version
docker exec YOUR_CONTAINER chromedriver --version

# Check if script exists
docker exec YOUR_CONTAINER ls -la /mnt/custom-addons/albanian_tech_map/scripts/

# Try running manually to see errors
docker exec YOUR_CONTAINER python3 /mnt/custom-addons/albanian_tech_map/scripts/run_scraper_docker.py
```

### Check Scraper Status
```bash
# Is scraper running?
docker exec YOUR_CONTAINER ps aux | grep run_scraper_docker.py

# View logs (last 50 lines)
docker exec YOUR_CONTAINER tail -50 /tmp/scraper.log

# Monitor logs in real-time
docker exec YOUR_CONTAINER tail -f /tmp/scraper.log

# Stop scraper if needed
docker exec YOUR_CONTAINER pkill -f run_scraper_docker.py
```

### No Companies Appearing in Map
- Companies need `latitude` and `longitude` values to show on the map
- Check the API: visit `/techmap/api/companies` in your browser
- Check all companies (with/without coords): `/techmap/api/companies/all`
- Geocoding is not automated — coordinates must be added manually in the admin

### Module Won't Install
- Make sure the addons path includes your custom addons directory
- Check Odoo logs for specific error messages: `docker logs YOUR_CONTAINER`
- The module only requires `requests` as a Python dependency
- Chrome/Selenium are only needed for the scraper script, not the module itself

### Container Name
Find your container name:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## Advanced Troubleshooting: Scraper Stuck or Not Finding Results

If the scraper starts but gets stuck without finding companies, here's the debugging process we used:

### Symptom: Scraper Logs Show "Searches planned" but No Results

**Logs show:**
```
INFO - Searches planned: 4560
INFO - Loaded 2021 existing NIPTs from database
(then nothing...)
```

### Step 1: Clean State - Restart Container

Sometimes Chrome processes get stuck. Restart for a clean state:

```bash
# Kill any stuck processes
docker exec YOUR_CONTAINER bash -c "pkill -9 chrome; pkill -9 chromedriver; pkill -f run_scraper_docker.py"

# Restart container completely
docker restart YOUR_CONTAINER

# Wait for container to be ready
sleep 15 && docker exec YOUR_CONTAINER echo "Container ready"
```

### Step 2: Minimal Test - Verify Chrome Works

Create a minimal test to verify Chrome can load the QKB page:

```bash
docker exec YOUR_CONTAINER bash -c "cat > /tmp/test_chrome.py << 'EOF'
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service('/usr/local/bin/chromedriver'), options=opts)
driver.set_page_load_timeout(15)

print('Loading page...')
try:
    start = time.time()
    driver.get('https://format.qkb.gov.al/kerko-per-subjekt/')
    elapsed = time.time() - start
    print(f'Page loaded in {elapsed:.2f}s')
    print(f'Title: {driver.title}')
except Exception as e:
    print(f'ERROR: {e}')
finally:
    driver.quit()
EOF
python3 /tmp/test_chrome.py"
```

**Expected output:**
```
Loading page...
Page loaded in 2.03s
Title: Kërko Për Subjekt
```

✅ If this works, Chrome is OK - problem is in the scraper script logic.
❌ If this fails, Chrome/network has issues.

### Step 3: Check QKB Page Structure

QKB might have changed their HTML structure. Verify selectors still exist:

```bash
# Fetch current page
docker exec YOUR_CONTAINER curl -s 'https://format.qkb.gov.al/kerko-per-subjekt/' > /tmp/qkb_page.html

# Check critical selectors
docker exec YOUR_CONTAINER bash -c "grep -o 'id=\"sektoriIVeprimtarise\"' /tmp/qkb_page.html"  # Activity field
docker exec YOUR_CONTAINER bash -c "grep -o 'id=\"qarku\"' /tmp/qkb_page.html"  # City dropdown
docker exec YOUR_CONTAINER bash -c "grep -o 'data-bs-target=\"#locationCollapse\"' /tmp/qkb_page.html"  # Location section
```

**All selectors should return results.** If not, QKB changed their HTML and the scraper needs updating.

### Step 4: Add Debug Logging

Add detailed logging to see exactly where the scraper gets stuck:

Edit `/mnt/custom-addons/albanian_tech_map/scripts/run_scraper_docker.py` and add these logging lines in the `search_qkb_activity()` function:

```python
def search_qkb_activity(driver, keyword, legal_form='', date_from=None, date_to=None):
    try:
        _logger.info(f"[DEBUG] About to load page for keyword='{keyword}', legal_form='{legal_form}'")
        _logger.info(f"[DEBUG] Calling driver.get({QKB_SEARCH_URL})")
        driver.get(QKB_SEARCH_URL)
        _logger.info(f"[DEBUG] Page loaded successfully!")

        # ... existing code ...

        _logger.info(f"[DEBUG] Opening activity section...")
        # collapse opening code

        _logger.info(f"[DEBUG] Looking for activity input field...")
        inp = driver.find_element(By.CSS_SELECTOR, '#sektoriIVeprimtarise')
        _logger.info(f"[DEBUG] Found element with selector '#sektoriIVeprimtarise', displayed={inp.is_displayed()}")

        _logger.info(f"[DEBUG] Entering keyword '{keyword}'...")
        inp.clear()
        inp.send_keys(keyword)

        _logger.info(f"[DEBUG] Clicking submit button...")
        btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        driver.execute_script("arguments[0].click();", btn)

        _logger.info(f"[DEBUG] Waiting for results...")
        time.sleep(5)  # IMPORTANT: Was 3, changed to 5

        # ... results collection ...

        results = driver.find_elements(By.CSS_SELECTOR, 'ul.list li .card.responsive-card-text')
        _logger.info(f"[DEBUG] Found {len(results)} result cards on page {page}")
```

### Step 5: The Fix - Increase Wait Time

**Root Cause:** After clicking submit, QKB needs more than 3 seconds to load results.

**Solution:** Change the wait time from 3 to 5 seconds:

```python
# Before:
time.sleep(3)  # After submit

# After:
time.sleep(5)  # Increased wait time - QKB needs 5s to load results
```

**Location:** Line ~265 in `run_scraper_docker.py`, right after clicking the submit button.

### Step 6: Verify the Fix

Start the scraper and check logs:

```bash
# Start scraper
docker exec YOUR_CONTAINER bash -c "nohup python3 -u /mnt/custom-addons/albanian_tech_map/scripts/run_scraper_docker.py > /tmp/scraper.log 2>&1 &"

# Wait 20 seconds then check logs
sleep 20 && docker exec YOUR_CONTAINER tail -50 /tmp/scraper.log
```

**Expected logs (working):**
```
INFO - [DEBUG] Clicking submit button...
INFO - [DEBUG] Waiting for results...
INFO - [DEBUG] Found 10 result cards on page 1
INFO - [DEBUG] Found 10 result cards on page 2
INFO - [DEBUG] Found 6 result cards on page 3
```

✅ **Success:** Scraper is finding results and paginating through pages!

### Why Results Aren't Saving

If the scraper finds results but doesn't show "saved" messages:

**This is normal!** The scraper only logs when NEW companies are found. If all companies already exist in the database (loaded at startup: "Loaded 2021 existing NIPTs"), the scraper correctly skips duplicates.

Check the code at line ~514:
```python
if new_in_batch > 0:
    _logger.info(f"[{search_count}/{total}] '{keyword}' [...]: +{new_in_batch}")
```

**To verify database is updating:**
```bash
docker exec YOUR_CONTAINER python3 -c "import psycopg2; conn = psycopg2.connect(host='db', port=5432, user='odoo', password='odoo', dbname='odoo'); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM tech_company'); print(f'Total companies: {cur.fetchone()[0]}'); conn.close()"
```

### Summary of Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Scraper stuck at "Searches planned" | QKB page needs more time to load results | Increase `time.sleep(3)` to `time.sleep(5)` after submit |
| Chrome crashes (exit -5) | Odoo RLIMIT_AS kills Chrome | Use standalone script (already implemented) |
| No results found | QKB HTML structure changed | Verify selectors with curl + grep |
| "Saved" messages not showing | All companies are duplicates | Check database count - duplicates are correctly skipped |
| Page won't load | Network/firewall blocking QKB | Test with minimal Chrome script |

### Clean Up Debug Logging

Once the scraper is working, you can remove the `[DEBUG]` logging lines to reduce log noise.

---

## License

LGPL-3

## Credits

- [QKB (Qendra Kombëtare e Biznesit)](https://qkb.gov.al) — Albanian Business Registry
- [Leaflet](https://leafletjs.com) — Map library
- [OpenStreetMap](https://www.openstreetmap.org) — Map tiles
