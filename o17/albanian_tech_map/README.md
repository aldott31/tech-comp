# Albanian Tech Map - Odoo 17 Module

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

- **Odoo 17** Community or Enterprise Edition
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

Replace `YOUR_CONTAINER` with your Odoo container name (e.g., `o17-odoo-1`).

This installs:
- Google Chrome (stable)
- ChromeDriver (auto-matched to Chrome version)
- Python packages: `selenium`, `beautifulsoup4`, `lxml`, `geopy`

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

**From Odoo UI:**
1. Go to **Tech Map > Tools > Run Scraper**
2. Click **"Run QKB Scraper"**
3. Monitor progress: `docker exec YOUR_CONTAINER tail -f /tmp/scraper.log`

**From command line:**
```bash
docker exec -d YOUR_CONTAINER python3 /mnt/custom-addons/albanian_tech_map/scripts/run_scraper_docker.py
```

**Automatically (cron):**
The module creates a scheduled action that runs every 24 hours.

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

### Scraper won't start
- Verify Chrome is installed: `docker exec YOUR_CONTAINER google-chrome-stable --version`
- Verify ChromeDriver: `docker exec YOUR_CONTAINER chromedriver --version`
- Re-run `install_deps.sh` if needed

### No companies appearing in the map
- Companies need `latitude` and `longitude` values to show on the map
- Check the API: visit `/techmap/api/companies` in your browser
- Geocoding is not yet automated — coordinates can be added manually in the admin

### Module won't install
- Make sure the addons path includes your custom addons directory
- Check Odoo logs for specific error messages
- The module only requires `requests` as a Python dependency (Chrome/Selenium are only needed for the scraper script)

### Scraper log
```bash
docker exec YOUR_CONTAINER tail -f /tmp/scraper.log
```

## License

LGPL-3

## Credits

- [QKB (Qendra Kombëtare e Biznesit)](https://qkb.gov.al) — Albanian Business Registry
- [Leaflet](https://leafletjs.com) — Map library
- [OpenStreetMap](https://www.openstreetmap.org) — Map tiles
