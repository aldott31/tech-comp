# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
import requests

_logger = logging.getLogger(__name__)


class TechCompany(models.Model):
    _name = 'tech.company'
    _description = 'Albanian Tech Company'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Company Name',
        required=True,
        index=True,
        tracking=True,
    )
    nipt = fields.Char(
        string='NIPT',
        index=True,
        help='Albanian Tax Identification Number',
    )
    legal_form = fields.Char(
        string='Legal Form',
        help='e.g. SHPK, SHA, Dege e Shoqerise se huaj',
    )
    registration_date = fields.Char(
        string='Registration Date',
    )
    category = fields.Selection(
        selection=[
            ('software', 'Software Company'),
            ('digital_agency', 'Digital Agency'),
            ('it_services', 'IT Services'),
            ('consulting', 'IT Consulting'),
            ('ecommerce', 'E-commerce'),
            ('mobile', 'Mobile Development'),
            ('data', 'Data/Analytics'),
            ('security', 'Cybersecurity'),
            ('other', 'Other'),
        ],
        string='Category',
        default='other',
    )

    # Location
    city = fields.Selection(
        selection=[
            ('tirane', 'Tiranë'),
            ('durres', 'Durrës'),
            ('shkoder', 'Shkodër'),
            ('vlore', 'Vlorë'),
            ('elbasan', 'Elbasan'),
            ('korce', 'Korçë'),
            ('fier', 'Fier'),
            ('berat', 'Berat'),
            ('lushnje', 'Lushnjë'),
            ('kavaje', 'Kavajë'),
            ('pogradec', 'Pogradec'),
            ('gjirokaster', 'Gjirokastër'),
            ('sarande', 'Sarandë'),
            ('kukes', 'Kukës'),
            ('lezhe', 'Lezhë'),
            ('peshkopi', 'Peshkopi'),
            ('other', 'Other'),
        ],
        string='City',
        default='tirane',
    )
    address = fields.Text(
        string='Address',
    )
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
    )
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
    )

    # Contact Information
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')

    # Data Management
    data_source = fields.Selection(
        selection=[
            ('manual', 'Manual Entry'),
            ('qkb', 'QKB Scraper'),
            ('import', 'Data Import'),
            ('biznes_al', 'biznes.al'),
            ('niptgov_al', 'niptgov.al'),
            ('facebook', 'Facebook'),
            ('linkedin', 'LinkedIn'),
            ('api', 'API'),
        ],
        string='Data Source',
        default='manual',
    )
    last_scraped = fields.Datetime(string='Last Scraped')
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')
    activity_description = fields.Text(
        string='Activity Description',
        help='Objekti i aktivitetit from QKB',
    )
    is_tech = fields.Boolean(
        string='Is Tech Company',
        default=False,
        help='True if activity description contains IT/tech keywords',
    )

    # Computed
    has_coordinates = fields.Boolean(
        string='Has Coordinates',
        compute='_compute_has_coordinates',
        store=True,
    )

    @api.depends('latitude', 'longitude')
    def _compute_has_coordinates(self):
        for company in self:
            company.has_coordinates = bool(
                company.latitude and company.longitude and
                company.latitude != 0.0 and company.longitude != 0.0
            )

    _sql_constraints = [
        ('nipt_unique', 'unique(nipt)', 'A company with this NIPT already exists!'),
    ]

    def get_map_marker_data(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'lat': self.latitude,
            'lng': self.longitude,
            'category': self.category or 'other',
            'website': self.website or '',
            'phone': self.phone or '',
            'email': self.email or '',
            'city': self.city or '',
            'nipt': self.nipt or '',
        }
