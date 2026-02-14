#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import scraped QKB companies into Odoo tech.company model.

Usage (from Odoo shell):
    python odoo-bin shell -d your_database < albanian_tech_map/scripts/import_companies.py

Or run standalone to generate XML data file:
    python albanian_tech_map/scripts/import_companies.py
"""

import json
import os
import sys


def import_to_odoo(env):
    """Import companies directly into Odoo database via ORM"""
    json_path = os.path.join(os.path.dirname(__file__), '..', '..', 'qkb_companies_comprehensive_with_contacts.json')

    if not os.path.exists(json_path):
        print(f"[ERROR] JSON file not found: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    print(f"[INFO] Loaded {len(companies)} companies from JSON")

    Company = env['tech.company']
    created = 0
    updated = 0
    skipped = 0

    for company_data in companies:
        nipt = company_data.get('nipt')
        name = company_data.get('name')

        if not nipt or not name:
            skipped += 1
            continue

        vals = {
            'name': name,
            'nipt': nipt,
            'city': company_data.get('city', 'Tirane'),
            'legal_form': company_data.get('type', ''),
            'registration_date': company_data.get('registration_date', ''),
            'email': company_data.get('email') or False,
            'phone': company_data.get('phone') or False,
            'data_source': 'qkb',
        }

        existing = Company.search([('nipt', '=', nipt)], limit=1)
        if existing:
            existing.write(vals)
            updated += 1
        else:
            Company.create(vals)
            created += 1

    env.cr.commit()
    print(f"[OK] Import complete: {created} created, {updated} updated, {skipped} skipped")


def generate_xml_data():
    """Generate Odoo XML data file from JSON (alternative to shell import)"""
    json_path = os.path.join(os.path.dirname(__file__), '..', '..', 'qkb_companies_comprehensive_with_contacts.json')

    if not os.path.exists(json_path):
        print(f"[ERROR] JSON file not found: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    xml_lines = ['<?xml version="1.0" encoding="utf-8"?>', '<odoo>', '    <data noupdate="1">']

    for i, c in enumerate(companies, 1):
        nipt = c.get('nipt', '')
        name = c.get('name', '').replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        city = c.get('city', 'Tirane')
        legal_form = (c.get('type') or '').replace('&', '&amp;')
        reg_date = c.get('registration_date', '')
        email = c.get('email') or ''
        phone = c.get('phone') or ''

        xml_id = f"company_{nipt.lower()}"

        xml_lines.append(f'')
        xml_lines.append(f'        <record id="{xml_id}" model="tech.company">')
        xml_lines.append(f'            <field name="name">{name}</field>')
        xml_lines.append(f'            <field name="nipt">{nipt}</field>')
        xml_lines.append(f'            <field name="city">{city}</field>')
        xml_lines.append(f'            <field name="legal_form">{legal_form}</field>')
        xml_lines.append(f'            <field name="registration_date">{reg_date}</field>')
        if email:
            xml_lines.append(f'            <field name="email">{email}</field>')
        if phone:
            xml_lines.append(f'            <field name="phone">{phone}</field>')
        xml_lines.append(f'            <field name="data_source">qkb</field>')
        xml_lines.append(f'        </record>')

    xml_lines.append('    </data>')
    xml_lines.append('</odoo>')

    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tech_company_data.xml')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))

    print(f"[OK] Generated XML data file with {len(companies)} companies: {output_path}")


if __name__ == '__main__':
    # When run standalone, generate XML data file
    generate_xml_data()
else:
    # When run via Odoo shell, import directly
    try:
        import_to_odoo(env)
    except NameError:
        print("Run this script via: python odoo-bin shell -d DATABASE < import_companies.py")
