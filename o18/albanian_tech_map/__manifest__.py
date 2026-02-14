# -*- coding: utf-8 -*-
{
    'name': 'Albanian Tech Map',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Interactive map of Albanian IT companies in Tirane',
    'description': """
Albanian Tech Map - Odoo 18 Module
==================================
Automatic scraping of IT companies from QKB (Albanian Business Registry),
filtered to Tirane district only, with daily cron updates.

Features:
- Selenium scraper searching both company name AND activity fields
- Qarku=tirane filter for Tirane-only companies
- PDF download with contact extraction (email, phone)
- Free geocoding with Nominatim (OpenStreetMap)
- Public web interface with Leaflet map
- 24-hour cron job for automatic updates
    """,
    'author': 'Albanian Tech Community',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
    ],
    'external_dependencies': {
        'python': [
            'requests',
        ],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/tech_company_data.xml',
        'views/tech_company_views.xml',
        'views/tech_company_scraper_views.xml',
        'views/map_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'albanian_tech_map/static/src/css/map.css',
            'albanian_tech_map/static/src/js/map.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
