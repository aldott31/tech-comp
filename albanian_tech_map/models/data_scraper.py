# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import os

_logger = logging.getLogger(__name__)


class TechCompanyScraper(models.TransientModel):
    _name = 'tech.company.scraper'
    _description = 'Tech Company Data Scraper'

    last_run = fields.Datetime(string='Last Run', readonly=True)
    companies_found = fields.Integer(string='Companies Found', readonly=True)
    companies_created = fields.Integer(string='Companies Created', readonly=True)
    companies_updated = fields.Integer(string='Companies Updated', readonly=True)
    status_log = fields.Text(string='Status Log', readonly=True)

    def _get_scraper_script_path(self):
        """Get path to the standalone scraper script."""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(module_dir, 'scripts', 'run_scraper_docker.py')

    @api.model
    def _execute_scraping_job(self):
        """Cron job entry point - launches standalone scraper as subprocess.

        The scraper runs as a separate process because:
        1. Odoo's RLIMIT_AS (2.5GB) kills Chrome/chromedriver with exit -5
        2. The standalone script resets this limit before starting Chrome
        3. It connects directly to PostgreSQL, bypassing Odoo ORM
        """
        script_path = self._get_scraper_script_path()

        if not os.path.exists(script_path):
            _logger.error(f'Scraper script not found: {script_path}')
            return False

        os.system(f'PYTHONUNBUFFERED=1 nohup python3 -u {script_path} > /tmp/scraper.log 2>&1 &')
        _logger.info("QKB scraper launched as subprocess (cron), log: /tmp/scraper.log")
        return True

    def action_run_scraping_job(self):
        """Manual trigger from UI button - same as cron but with notification."""
        script_path = self._get_scraper_script_path()

        if not os.path.exists(script_path):
            raise UserError(_(f'Scraper script not found: {script_path}'))

        os.system(f'PYTHONUNBUFFERED=1 nohup python3 -u {script_path} > /tmp/scraper.log 2>&1 &')
        _logger.info("QKB scraper launched as subprocess, log: /tmp/scraper.log")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Scraping Started'),
                'message': _('QKB scraper launched in background. Monitor with: tail -f /tmp/scraper.log'),
                'type': 'info',
                'sticky': True,
            }
        }
