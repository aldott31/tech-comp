# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import os
import subprocess

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

    def _check_dependencies(self):
        """Check if scraper dependencies are installed.

        Returns:
            tuple: (bool, str) - (is_installed, error_message)
        """
        missing = []

        # Check Chrome - use full path
        chrome_paths = ['/usr/bin/google-chrome-stable', '/opt/google/chrome/chrome']
        if not any(os.path.exists(p) for p in chrome_paths):
            missing.append('Google Chrome')

        # Check ChromeDriver - use full path
        chromedriver_paths = ['/usr/local/bin/chromedriver', '/usr/bin/chromedriver']
        if not any(os.path.exists(p) for p in chromedriver_paths):
            missing.append('ChromeDriver')

        # Check Selenium
        try:
            import selenium
        except ImportError:
            missing.append('Selenium (Python package)')

        # Check psycopg2
        try:
            import psycopg2
        except ImportError:
            missing.append('psycopg2 (Python package)')

        if missing:
            module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            install_script = os.path.join(module_dir, 'scripts', 'install_deps.sh')

            error_msg = _(
                'Missing dependencies: %s\n\n'
                'Please install dependencies first:\n\n'
                'docker exec -u root <container> bash %s\n\n'
                'Replace <container> with your container name.'
            ) % (', '.join(missing), install_script)

            return False, error_msg

        return True, ''

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
        """Manual trigger from UI button - checks dependencies first."""
        _logger.info("action_run_scraping_job started")

        # Check dependencies
        deps_ok, error_msg = self._check_dependencies()
        _logger.info(f"Dependency check result: {deps_ok}")

        if not deps_ok:
            _logger.warning(f"Dependencies missing: {error_msg}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Dependencies Missing'),
                    'message': error_msg,
                    'type': 'danger',
                    'sticky': True,
                }
            }

        # Check if script exists
        script_path = self._get_scraper_script_path()
        _logger.info(f"Script path: {script_path}, exists: {os.path.exists(script_path)}")
        if not os.path.exists(script_path):
            raise UserError(_(f'Scraper script not found: {script_path}'))

        # Launch scraper using subprocess instead of os.system for better reliability
        _logger.info(f"Launching scraper: {script_path}")
        result = os.system(f'PYTHONUNBUFFERED=1 nohup python3 -u {script_path} > /tmp/scraper.log 2>&1 &')
        _logger.info(f"QKB scraper launched as subprocess (exit code: {result}), log: /tmp/scraper.log")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Scraper Started Successfully'),
                'message': _('QKB scraper is running in background.\n\nMonitor logs:\ndocker exec <container> tail -f /tmp/scraper.log'),
                'type': 'success',
                'sticky': True,
            }
        }
