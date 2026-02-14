#!/usr/bin/env python3
"""
Docker scraper - searches QKB ONLY by activity field ("Objekti i aktivitetit")
with IT keywords. Every result is a tech company by definition.

Then clicks info modal for each result to get the full activity description.

Usage: docker exec -d o17-odoo-1 python3 /mnt/custom-addons/albanian_tech_map/scripts/run_scraper_docker.py
"""

# CRITICAL: Fix inherited resource limits from Odoo process.
import resource
import signal
import os

try:
    resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
except (ValueError, resource.error):
    pass

for sig in range(1, signal.NSIG):
    try:
        signal.signal(sig, signal.SIG_DFL)
    except (OSError, ValueError):
        pass
try:
    signal.alarm(0)
except Exception:
    pass

import sys
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)
for handler in logging.root.handlers:
    handler.flush = lambda h=handler: (h.stream.flush() if hasattr(h, 'stream') else None)
_logger = logging.getLogger(__name__)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

import psycopg2

# =============================================================================
# CONFIG
# =============================================================================
DB_HOST = os.environ.get('DB_HOST', os.environ.get('HOST', 'db'))
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER', os.environ.get('USER', 'odoo'))
DB_PASS = os.environ.get('DB_PASS', os.environ.get('PASSWORD', 'odoo'))


def detect_db_name():
    """Auto-detect Odoo database name. Works on any container."""
    # 1. Explicit env var
    if os.environ.get('DB_NAME'):
        return os.environ['DB_NAME']

    # 2. Read from Odoo config file
    for conf_path in ['/etc/odoo/odoo.conf', '/opt/odoo/odoo.conf']:
        if os.path.exists(conf_path):
            with open(conf_path) as f:
                for line in f:
                    if line.strip().startswith('db_name'):
                        val = line.split('=', 1)[1].strip()
                        if val and val != 'False':
                            return val

    # 3. Query PostgreSQL for non-system databases with tech_company table
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname='postgres',
                                user=DB_USER, password=DB_PASS)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("""
            SELECT datname FROM pg_database
            WHERE datname NOT IN ('postgres', 'template0', 'template1')
            ORDER BY datname
        """)
        for row in cur.fetchall():
            try:
                test_conn = psycopg2.connect(host=DB_HOST, port=DB_PORT,
                                              dbname=row[0], user=DB_USER, password=DB_PASS)
                test_cur = test_conn.cursor()
                test_cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'tech_company'")
                if test_cur.fetchone():
                    test_conn.close()
                    conn.close()
                    return row[0]
                test_conn.close()
            except:
                pass
        conn.close()
    except:
        pass

    return 'odoo'  # fallback


DB_NAME = detect_db_name()

QKB_SEARCH_URL = "https://format.qkb.gov.al/kerko-per-subjekt/"

# IT-specific keywords to search in the ACTIVITY field only.
# QKB searches "Objekti i aktivitetit" - so every result already has the keyword.
ACTIVITY_KEYWORDS = [
    'software', 'programim', 'kodim', 'IT', 'informatik',
    'web', 'internet', 'hosting', 'server', 'cloud',
    'aplikacion', 'app', 'mobile', 'android', 'ios',
    'kompjuter', 'computer', 'teknologji informacion',
    'dixhital', 'cyber', 'siguri kibernetik',
    'databaz', 'database', 'e-commerce',
    'zhvillim software', 'development',
    'ERP', 'CRM', 'SaaS',
    'artificial intelligence', 'inteligjenc artificiale',
    'machine learning', 'blockchain',
    'sistem informacion', 'information technology',
    'telekomunikacion', 'automatizim', 'automation',
    'perpunim te dhenash', 'data processing',
]

LEGAL_FORMS = [
    'Shoqeri me pergjegjesi te kufizuar',
    'Shoqeri aksionare',
    'Dege e Shoqerise se huaj',
]

DATE_RANGES = [
    (2026, 1, 2026, 12),
    (2025, 10, 2025, 12), (2025, 7, 2025, 9), (2025, 4, 2025, 6), (2025, 1, 2025, 3),
    (2024, 10, 2024, 12), (2024, 7, 2024, 9), (2024, 4, 2024, 6), (2024, 1, 2024, 3),
    (2023, 10, 2023, 12), (2023, 7, 2023, 9), (2023, 4, 2023, 6), (2023, 1, 2023, 3),
    (2022, 10, 2022, 12), (2022, 7, 2022, 9), (2022, 4, 2022, 6), (2022, 1, 2022, 3),
    (2021, 10, 2021, 12), (2021, 7, 2021, 9), (2021, 4, 2021, 6), (2021, 1, 2021, 3),
    (2020, 10, 2020, 12), (2020, 7, 2020, 9), (2020, 4, 2020, 6), (2020, 1, 2020, 3),
    (2019, 10, 2019, 12), (2019, 7, 2019, 9), (2019, 4, 2019, 6), (2019, 1, 2019, 3),
    (2018, 7, 2018, 12), (2018, 1, 2018, 6),
    (2017, 7, 2017, 12), (2017, 1, 2017, 6),
    (2016, 1, 2016, 12), (2015, 1, 2015, 12),
    (2013, 1, 2014, 12), (2010, 1, 2012, 12),
    (2000, 1, 2009, 12),
]

CITY_MAP = {
    'tirane': 'tirane', 'tirana': 'tirane',
    'durres': 'durres', 'shkoder': 'shkoder',
    'vlore': 'vlore', 'elbasan': 'elbasan',
    'korce': 'korce', 'fier': 'fier', 'berat': 'berat',
    'lushnje': 'lushnje', 'kavaje': 'kavaje',
    'pogradec': 'pogradec', 'gjirokaster': 'gjirokaster',
    'sarande': 'sarande', 'kukes': 'kukes',
    'lezhe': 'lezhe', 'peshkopi': 'peshkopi',
}


# =============================================================================
# CHROME DRIVER
# =============================================================================
def start_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    import shutil
    chromedriver = shutil.which('chromedriver') or '/usr/local/bin/chromedriver'
    svc = Service(chromedriver)
    driver = webdriver.Chrome(service=svc, options=opts)
    _logger.info(f"[OK] Chrome started with {chromedriver}")
    return driver


# =============================================================================
# QKB ACTIVITY SEARCH - returns companies whose activity matches keyword
# =============================================================================
def search_qkb_activity(driver, keyword, legal_form='', date_from=None, date_to=None):
    """Search QKB by activity field. Returns list of {nipt, name, city, legal_form, registration_date}."""
    try:
        driver.get(QKB_SEARCH_URL)
        time.sleep(3)

        # Set date range
        if date_from and date_to:
            driver.execute_script(f"""
                var d1 = document.querySelector('#dataNga');
                var d2 = document.querySelector('#dataNe');
                if (d1 && d1._flatpickr) d1._flatpickr.setDate(new Date({date_from[0]}, {date_from[1]-1}, 1), true);
                if (d2 && d2._flatpickr) d2._flatpickr.setDate(new Date({date_to[0]}, {date_to[1]-1}, 28), true);
            """)

        # Set qarku to Tirane
        try:
            loc = driver.find_element(By.CSS_SELECTOR, 'div[data-bs-target="#locationCollapse"]')
            if loc.get_attribute('aria-expanded') != 'true':
                driver.execute_script("arguments[0].scrollIntoView(true);", loc)
                time.sleep(0.5)
                loc.click()
                time.sleep(1)
            Select(driver.find_element(By.CSS_SELECTOR, 'select#qarku')).select_by_value('tirane')
        except Exception as e:
            _logger.warning(f"qarku: {e}")

        # Set legal form
        if legal_form:
            try:
                Select(driver.find_element(By.CSS_SELECTOR, 'select#formeLigjore')).select_by_value(legal_form)
            except:
                pass

        # Open activity section and enter keyword
        driver.execute_script("""
            var btn = document.querySelector('div[data-bs-target="#sectorCollapse"]');
            if (btn && btn.getAttribute('aria-expanded') !== 'true') btn.click();
        """)
        time.sleep(1)

        inp = None
        for s in ['#sektoriIVeprimtarise', 'input[name="sektoriIVeprimtarise"]']:
            try:
                el = driver.find_element(By.CSS_SELECTOR, s)
                if el.is_displayed():
                    inp = el
                    break
            except:
                continue
        if not inp:
            return []

        inp.clear()
        inp.send_keys(keyword)
        btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)

        # Collect results from all pages
        companies = []
        page = 1
        while page <= 10:
            results = driver.find_elements(By.CSS_SELECTOR, 'ul.list li .card.responsive-card-text')
            if not results:
                break
            for r in results:
                try:
                    nipt = r.find_element(By.CSS_SELECTOR, '.nipti').text.strip()
                    name = r.find_element(By.CSS_SELECTOR, '.emriISubjektit').text.strip()
                    if not nipt or not name:
                        continue
                    city = ''
                    try:
                        city = r.find_element(By.CSS_SELECTOR, '.qyteti').text.strip()
                    except:
                        pass
                    lf = ''
                    try:
                        lf = r.find_element(By.CSS_SELECTOR, '.formaLigjore').text.strip()
                    except:
                        pass
                    reg_date = ''
                    try:
                        reg_date = r.find_element(By.CSS_SELECTOR, '.dataERegjistrimit').text.strip()
                    except:
                        pass
                    if 'fizik' not in lf.lower():
                        companies.append({
                            'nipt': nipt, 'name': name,
                            'city': CITY_MAP.get(city.lower(), 'tirane'),
                            'legal_form': lf, 'registration_date': reg_date,
                        })
                except:
                    pass

            # Next page
            try:
                nxt = None
                for item in driver.find_elements(By.CSS_SELECTOR, 'ul.pagination li'):
                    if 'active' not in (item.get_attribute('class') or ''):
                        link = item.find_elements(By.TAG_NAME, 'a')
                        if link and link[0].text.strip() == str(page + 1):
                            nxt = link[0]
                            break
                if nxt:
                    driver.execute_script("arguments[0].scrollIntoView(true);", nxt)
                    time.sleep(0.5)
                    nxt.click()
                    time.sleep(3)
                    page += 1
                else:
                    break
            except:
                break

        return companies
    except Exception as e:
        _logger.error(f"Search error: {e}")
        return []


# =============================================================================
# QKB DETAIL - get activity description from info modal
# =============================================================================
def get_activity_from_modal(driver, nipt):
    """Search QKB by NIPT, click info button, return activity description text."""
    try:
        driver.get(QKB_SEARCH_URL)
        time.sleep(2)

        nipt_field = driver.find_element(By.ID, 'nipt')
        nipt_field.clear()
        nipt_field.send_keys(nipt)

        btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        driver.execute_script('arguments[0].click();', btn)
        time.sleep(3)

        info_btns = driver.find_elements(By.CSS_SELECTOR, '.btn-info-local')
        if not info_btns:
            return ''

        driver.execute_script('arguments[0].click();', info_btns[0])
        time.sleep(4)

        try:
            modal = driver.find_element(By.ID, 'detailModal')
            text = modal.text
        except:
            return ''

        # Extract activity description
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'Objekti i aktivitetit' in line:
                activity_lines = []
                for j in range(i + 1, len(lines)):
                    stripped = lines[j].strip()
                    if stripped in ['Administrator/ Ortak/ Aksionar', 'Qyteti',
                                    'Pronësia', 'Ekstrakt RPP', 'Ekstrakt i thjeshtë',
                                    'Ekstrakt historik', '']:
                        break
                    activity_lines.append(stripped)
                return ' '.join(activity_lines)

        # Close modal
        try:
            close_btn = modal.find_element(By.CSS_SELECTOR, 'button.btn-close, [data-bs-dismiss="modal"]')
            driver.execute_script('arguments[0].click();', close_btn)
        except:
            pass

        return ''
    except Exception as e:
        _logger.error(f"Modal error for {nipt}: {e}")
        return ''


# =============================================================================
# DATABASE
# =============================================================================
def get_db_connection():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)


def ensure_columns(cur):
    for col, coltype, default in [
        ('activity_description', 'TEXT', "''"),
        ('is_tech', 'BOOLEAN', 'false'),
    ]:
        cur.execute(f"""
            DO $$
            BEGIN
                ALTER TABLE tech_company ADD COLUMN {col} {coltype} DEFAULT {default};
            EXCEPTION
                WHEN duplicate_column THEN NULL;
            END $$;
        """)


def upsert_company(cur, data):
    nipt = data['nipt']
    cur.execute("SELECT id FROM tech_company WHERE nipt = %s", (nipt,))
    existing = cur.fetchone()
    now = datetime.utcnow()

    if existing:
        cur.execute("""
            UPDATE tech_company SET
                city = COALESCE(NULLIF(city, ''), %s),
                legal_form = COALESCE(NULLIF(legal_form, ''), %s),
                registration_date = COALESCE(NULLIF(registration_date, ''), %s),
                activity_description = COALESCE(NULLIF(activity_description, ''), %s),
                is_tech = true,
                last_scraped = %s,
                write_date = %s
            WHERE nipt = %s
        """, (
            data.get('city', 'tirane'),
            data.get('legal_form', ''),
            data.get('registration_date', ''),
            data.get('activity_description', ''),
            now, now, nipt,
        ))
        return 'updated'
    else:
        cur.execute("""
            INSERT INTO tech_company (name, nipt, city, legal_form, registration_date,
                                      activity_description, is_tech, data_source, last_scraped,
                                      active, latitude, longitude,
                                      create_date, write_date, create_uid, write_uid)
            VALUES (%s, %s, %s, %s, %s, %s, true, 'qkb', %s, true, 0, 0, %s, %s, 1, 1)
        """, (
            data['name'], nipt,
            data.get('city', 'tirane'),
            data.get('legal_form', ''),
            data.get('registration_date', ''),
            data.get('activity_description', ''),
            now, now, now,
        ))
        return 'created'


# =============================================================================
# MAIN
# =============================================================================
def main():
    start = datetime.now()
    _logger.info("=" * 80)
    _logger.info("QKB SCRAPER - Activity field search only (IT companies)")
    _logger.info("=" * 80)

    driver = start_driver()
    conn = get_db_connection()
    cur = conn.cursor()

    ensure_columns(cur)
    conn.commit()

    # Load existing NIPTs
    cur.execute("SELECT nipt FROM tech_company WHERE nipt IS NOT NULL")
    existing_nipts = {row[0] for row in cur.fetchall()}
    _logger.info(f"Loaded {len(existing_nipts)} existing NIPTs from database")

    # ==========================================================================
    # SEARCH: Activity field only with IT keywords
    # All results are tech companies (matched by activity field on QKB)
    # ==========================================================================
    total = len(ACTIVITY_KEYWORDS) * len(LEGAL_FORMS) * len(DATE_RANGES)
    _logger.info(f"Searches planned: {total} ({len(ACTIVITY_KEYWORDS)} keywords x {len(LEGAL_FORMS)} legal forms x {len(DATE_RANGES)} date ranges)")

    found = {}  # nipt -> company data
    search_count = 0
    created = 0
    updated = 0

    try:
        for keyword in ACTIVITY_KEYWORDS:
            for legal_form in LEGAL_FORMS:
                for (y1, m1, y2, m2) in DATE_RANGES:
                    search_count += 1
                    companies = search_qkb_activity(driver, keyword, legal_form, (y1, m1), (y2, m2))

                    new_in_batch = 0
                    for c in companies:
                        nipt = c['nipt']
                        if nipt in found or nipt in existing_nipts:
                            continue
                        found[nipt] = c
                        new_in_batch += 1

                        # Save immediately - all activity search results are tech companies
                        c['is_tech'] = True
                        c['activity_description'] = f'[matched: {keyword}]'  # placeholder
                        action = upsert_company(cur, c)
                        if action == 'created':
                            created += 1
                        else:
                            updated += 1

                    if new_in_batch > 0:
                        _logger.info(f"[{search_count}/{total}] '{keyword}' [{legal_form[:10]}] [{y1}/{m1:02d}-{y2}/{m2:02d}]: +{new_in_batch} (total: {len(found)}, saved: {created})")

                    # Commit every 10 searches
                    if search_count % 10 == 0:
                        conn.commit()

                    time.sleep(1.5)

            # Progress every keyword
            conn.commit()
            _logger.info(f"[KEYWORD DONE] '{keyword}' - {search_count}/{total} searches, {len(found)} found, {created} created")

    except KeyboardInterrupt:
        _logger.info("Interrupted - saving progress")
    except Exception as e:
        _logger.error(f"Search error: {e}")
        import traceback
        traceback.print_exc()

    conn.commit()
    _logger.info(f"Search complete: {len(found)} tech companies found")

    # ==========================================================================
    # ENRICH: Get full activity description from info modal for each company
    # ==========================================================================
    _logger.info("=" * 80)
    _logger.info(f"ENRICHING: Getting activity descriptions for {len(found)} companies")
    _logger.info("=" * 80)

    enriched = 0
    for i, (nipt, data) in enumerate(found.items(), 1):
        try:
            activity = get_activity_from_modal(driver, nipt)
            if activity:
                cur.execute(
                    "UPDATE tech_company SET activity_description = %s WHERE nipt = %s",
                    (activity, nipt)
                )
                enriched += 1
            if i % 10 == 0:
                conn.commit()
                _logger.info(f"[ENRICH {i}/{len(found)}] {enriched} enriched - last: {data['name']}")
            time.sleep(1)
        except Exception as e:
            _logger.error(f"Enrich error {nipt}: {e}")

    conn.commit()

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    driver.quit()
    cur.close()
    conn.close()

    duration = (datetime.now() - start).total_seconds()
    _logger.info("=" * 80)
    _logger.info("DONE")
    _logger.info(f"Duration: {duration/3600:.1f} hours")
    _logger.info(f"Searches: {search_count}/{total}")
    _logger.info(f"Tech companies found: {len(found)}")
    _logger.info(f"Created: {created}, Updated: {updated}")
    _logger.info(f"Enriched with activity: {enriched}")
    _logger.info("=" * 80)


if __name__ == '__main__':
    main()
