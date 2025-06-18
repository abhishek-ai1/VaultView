import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import current_app
import threading
import time
from vaultview.utils import get_ist_now, format_timestamp_log

class NotificationManager:
    """Manages notifications and alerts for domain monitoring"""
    
    def __init__(self):
        self.notification_queue = []
        self.is_running = False
        self.worker_thread = None
    
    def start_worker(self):
        """Start the notification worker thread"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
    
    def stop_worker(self):
        """Stop the notification worker thread"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join()
    
    def add_notification(self, notification_type: str, data: Dict[str, Any], user_id: int = None):
        """Add a notification to the queue"""
        notification = {
            'id': int(time.time() * 1000),  # Simple ID generation
            'type': notification_type,
            'data': data,
            'user_id': user_id,
            'timestamp': get_ist_now().isoformat(),
            'status': 'pending'
        }
        self.notification_queue.append(notification)
    
    def _process_queue(self):
        """Process the notification queue"""
        while self.is_running:
            if self.notification_queue:
                notification = self.notification_queue.pop(0)
                try:
                    self._send_notification(notification)
                    notification['status'] = 'sent'
                except Exception as e:
                    notification['status'] = 'failed'
                    notification['error'] = str(e)
                    print(f"Notification failed: {e}")
            else:
                time.sleep(1)  # Wait before checking again
    
    def _send_notification(self, notification: Dict[str, Any]):
        """Send a notification based on its type"""
        notification_type = notification['type']
        
        if notification_type == 'email':
            self._send_email_notification(notification)
        elif notification_type == 'webhook':
            self._send_webhook_notification(notification)
        elif notification_type == 'alert':
            self._send_alert_notification(notification)
    
    def _send_email_notification(self, notification: Dict[str, Any]):
        """Send email notification"""
        data = notification['data']
        
        # Get email settings from config
        smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_username = current_app.config.get('SMTP_USERNAME')
        smtp_password = current_app.config.get('SMTP_PASSWORD')
        from_email = current_app.config.get('FROM_EMAIL', smtp_username)
        
        if not all([smtp_username, smtp_password, data.get('to_email')]):
            raise ValueError("Email configuration incomplete")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = data['to_email']
        msg['Subject'] = data.get('subject', 'VaultView Alert')
        
        # Create HTML body
        html_body = self._create_email_template(data)
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
    
    def _create_email_template(self, data: Dict[str, Any]) -> str:
        """Create HTML email template"""
        domain = data.get('domain', 'Unknown')
        scan_type = data.get('scan_type', 'Unknown')
        status = data.get('status', 'Unknown')
        details = data.get('details', {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }}
                .status-{status.lower()} {{ padding: 10px; border-radius: 4px; margin: 15px 0; }}
                .status-warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }}
                .status-error {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
                .status-success {{ background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
                .details {{ background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 15px 0; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔒 VaultView Security Alert</h2>
                    <p>Domain: {domain}</p>
                </div>
                
                <div class="status-{status.lower()}">
                    <strong>Status:</strong> {status}
                </div>
                
                <h3>Scan Details</h3>
                <div class="details">
                    <p><strong>Domain:</strong> {domain}</p>
                    <p><strong>Scan Type:</strong> {scan_type}</p>
                    <p><strong>Time:</strong> {format_timestamp_log(get_ist_now())}</p>
                </div>
                
                {self._format_details_html(details)}
                
                <div class="footer">
                    <p>This alert was generated by VaultView Domain Security Monitor</p>
                    <p>Visit your dashboard for more details and to configure alerts.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_details_html(self, details: Dict[str, Any]) -> str:
        """Format details for HTML display"""
        if not details:
            return ""
        
        html = "<h3>Details</h3><div class='details'>"
        
        for key, value in details.items():
            if isinstance(value, dict):
                html += f"<p><strong>{key.title()}:</strong></p><ul>"
                for k, v in value.items():
                    html += f"<li><strong>{k}:</strong> {v}</li>"
                html += "</ul>"
            else:
                html += f"<p><strong>{key.title()}:</strong> {value}</p>"
        
        html += "</div>"
        return html
    
    def _send_webhook_notification(self, notification: Dict[str, Any]):
        """Send webhook notification"""
        data = notification['data']
        webhook_url = data.get('webhook_url')
        
        if not webhook_url:
            raise ValueError("Webhook URL not provided")
        
        payload = {
            'timestamp': notification['timestamp'],
            'type': notification['type'],
            'domain': data.get('domain'),
            'scan_type': data.get('scan_type'),
            'status': data.get('status'),
            'details': data.get('details', {}),
            'user_id': notification.get('user_id')
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'VaultView/1.0'
        }
        
        # Add custom headers if provided
        if data.get('headers'):
            headers.update(data['headers'])
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code >= 400:
            raise Exception(f"Webhook failed with status {response.status_code}: {response.text}")
    
    def _send_alert_notification(self, notification: Dict[str, Any]):
        """Send in-app alert notification"""
        # This would typically store the alert in the database
        # for display in the web interface
        data = notification['data']
        
        # For now, we'll just log it
        print(f"🔔 In-App Alert: {data.get('message', 'No message')}")
        
        # TODO: Store in database for web display
        # from vaultview.models import Alert
        # alert = Alert(
        #     user_id=notification['user_id'],
        #     message=data['message'],
        #     level=data.get('level', 'info'),
        #     domain=data.get('domain'),
        #     scan_type=data.get('scan_type')
        # )
        # db.session.add(alert)
        # db.session.commit()

# Global notification manager instance
notification_manager = NotificationManager()

def send_ssl_alert(domain: str, scan_result: Dict[str, Any], user_id: int = None):
    """Send SSL certificate alert"""
    days_until_expiry = scan_result.get('days_until_expiry', 0)
    
    if days_until_expiry <= 30:
        status = 'warning' if days_until_expiry > 0 else 'error'
        message = f"SSL certificate for {domain} expires in {days_until_expiry} days"
        
        notification_data = {
            'domain': domain,
            'scan_type': 'SSL',
            'status': status,
            'message': message,
            'details': {
                'days_until_expiry': days_until_expiry,
                'valid_until': scan_result.get('valid_until'),
                'issuer': scan_result.get('issuer')
            }
        }
        
        notification_manager.add_notification('alert', notification_data, user_id)

def send_blacklist_alert(domain: str, scan_result: Dict[str, Any], user_id: int = None):
    """Send blacklist alert"""
    if scan_result.get('overall_status') == 'Listed':
        notification_data = {
            'domain': domain,
            'scan_type': 'BLACKLIST',
            'status': 'error',
            'message': f"Domain {domain} is listed on {scan_result.get('summary', {}).get('listed_count', 0)} blacklist(s)",
            'details': {
                'listed_count': scan_result.get('summary', {}).get('listed_count', 0),
                'severity': scan_result.get('severity'),
                'blacklists': [k for k, v in scan_result.get('blacklists', {}).items() if v.get('listed')]
            }
        }
        
        notification_manager.add_notification('alert', notification_data, user_id)

def send_email_notification(to_email: str, subject: str, data: Dict[str, Any], user_id: int = None):
    """Send email notification"""
    notification_data = {
        'to_email': to_email,
        'subject': subject,
        **data
    }
    
    notification_manager.add_notification('email', notification_data, user_id)

def send_webhook_notification(webhook_url: str, data: Dict[str, Any], headers: Dict[str, str] = None, user_id: int = None):
    """Send webhook notification"""
    notification_data = {
        'webhook_url': webhook_url,
        'headers': headers or {},
        **data
    }
    
    notification_manager.add_notification('webhook', notification_data, user_id)

def start_notification_service():
    """Start the notification service"""
    notification_manager.start_worker()

def stop_notification_service():
    """Stop the notification service"""
    notification_manager.stop_worker() 