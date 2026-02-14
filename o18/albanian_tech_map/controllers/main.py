# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json


class TechMapController(http.Controller):

    @http.route('/techmap', type='http', auth='public', website=True)
    def tech_map_page(self, **kwargs):
        """Public map page - no authentication required"""
        companies = request.env['tech.company'].sudo().search([
            ('active', '=', True),
            ('latitude', '!=', 0),
            ('longitude', '!=', 0),
        ])

        values = {
            'companies': companies,
            'company_count': len(companies),
            'selected_company_id': int(kwargs.get('company_id', 0)) or None,
        }

        return request.render('albanian_tech_map.techmap_page', values)

    @http.route('/techmap/api/companies', type='http', auth='public', methods=['GET'], cors='*')
    def api_companies_list(self, **kwargs):
        """JSON API - returns all companies with coordinates"""
        domain = [
            ('active', '=', True),
            ('latitude', '!=', 0),
            ('longitude', '!=', 0),
        ]

        city = kwargs.get('city')
        if city:
            domain.append(('city', 'ilike', city))

        companies = request.env['tech.company'].sudo().search(domain)

        data = []
        for c in companies:
            data.append({
                'id': c.id,
                'name': c.name,
                'lat': c.latitude,
                'lng': c.longitude,
                'city': c.city or '',
                'website': c.website or '',
                'email': c.email or '',
                'phone': c.phone or '',
                'category': c.category or 'other',
                'nipt': c.nipt or '',
                'is_tech': c.is_tech,
                'activity_description': c.activity_description or '',
            })

        return request.make_response(
            json.dumps(data, ensure_ascii=False, indent=2),
            headers=[
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
        )

    @http.route('/techmap/api/companies/all', type='http', auth='public', methods=['GET'], cors='*')
    def api_all_companies(self, **kwargs):
        """JSON API - returns ALL companies (even without coordinates)"""
        companies = request.env['tech.company'].sudo().search([('active', '=', True)])

        data = []
        for c in companies:
            data.append({
                'id': c.id,
                'name': c.name,
                'nipt': c.nipt or '',
                'city': c.city or '',
                'email': c.email or '',
                'phone': c.phone or '',
                'legal_form': c.legal_form or '',
                'lat': c.latitude,
                'lng': c.longitude,
                'is_tech': c.is_tech,
                'activity_description': c.activity_description or '',
            })

        return request.make_response(
            json.dumps(data, ensure_ascii=False, indent=2),
            headers=[
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
        )
