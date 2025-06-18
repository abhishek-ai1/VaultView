import schedule
import time
import threading
from datetime import datetime
from flask import current_app
from vaultview.db import db
from vaultview.models import ScanResult, User
from vaultview.ssl_checker import check_ssl
from vaultview.dns_checker import check_dns
from vaultview.utils import get_ist_now, format_timestamp_log

class DomainScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        self.app = None
    
    def start(self, app=None):
        """Start the scheduler in a separate thread"""
        if not self.running:
            self.running = True
            self.app = app
            self.thread = threading.Thread(target=self._run_scheduler)
            self.thread.daemon = True
            self.thread.start()
            print(f"✓ Scheduler started at {format_timestamp_log(get_ist_now())}")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        print(f"✓ Scheduler stopped at {format_timestamp_log(get_ist_now())}")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def add_domain_monitoring(self, domain, scan_type, user_id, interval_hours=24):
        """Add a domain to be monitored at regular intervals"""
        if scan_type == 'SSL':
            schedule.every(interval_hours).hours.do(
                self._perform_ssl_scan, domain, user_id
            )
        elif scan_type == 'DNS':
            schedule.every(interval_hours).hours.do(
                self._perform_dns_scan, domain, user_id
            )
    
    def _perform_ssl_scan(self, domain, user_id):
        """Perform SSL scan and save results"""
        try:
            # Use Flask app context for database operations
            if self.app:
                with self.app.app_context():
                    result_data = check_ssl(domain)
                    scan_result = ScanResult(
                        domain=domain,
                        result_type='SSL',
                        result_data=result_data,
                        user_id=user_id
                    )
                    db.session.add(scan_result)
                    db.session.commit()
                    print(f"✓ Scheduled SSL scan completed for {domain} at {format_timestamp_log(get_ist_now())}")
            else:
                # Fallback to current_app if available
                with current_app.app_context():
                    result_data = check_ssl(domain)
                    scan_result = ScanResult(
                        domain=domain,
                        result_type='SSL',
                        result_data=result_data,
                        user_id=user_id
                    )
                    db.session.add(scan_result)
                    db.session.commit()
                    print(f"✓ Scheduled SSL scan completed for {domain} at {format_timestamp_log(get_ist_now())}")
        except Exception as e:
            print(f"✗ Error in scheduled SSL scan for {domain} at {format_timestamp_log(get_ist_now())}: {str(e)}")
    
    def _perform_dns_scan(self, domain, user_id):
        """Perform DNS scan and save results"""
        try:
            # Use Flask app context for database operations
            if self.app:
                with self.app.app_context():
                    result_data = check_dns(domain)
                    scan_result = ScanResult(
                        domain=domain,
                        result_type='DNS',
                        result_data=result_data,
                        user_id=user_id
                    )
                    db.session.add(scan_result)
                    db.session.commit()
                    print(f"✓ Scheduled DNS scan completed for {domain} at {format_timestamp_log(get_ist_now())}")
            else:
                # Fallback to current_app if available
                with current_app.app_context():
                    result_data = check_dns(domain)
                    scan_result = ScanResult(
                        domain=domain,
                        result_type='DNS',
                        result_data=result_data,
                        user_id=user_id
                    )
                    db.session.add(scan_result)
                    db.session.commit()
                    print(f"✓ Scheduled DNS scan completed for {domain} at {format_timestamp_log(get_ist_now())}")
        except Exception as e:
            print(f"✗ Error in scheduled DNS scan for {domain} at {format_timestamp_log(get_ist_now())}: {str(e)}")

# Global scheduler instance
scheduler = DomainScheduler() 