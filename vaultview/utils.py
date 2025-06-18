import json
import re
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

# IST timezone (UTC+5:30)
IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))

def validate_domain(domain: str) -> bool:
    """
    Validate domain name format
    """
    if not domain:
        return False
    
    # Basic domain validation regex
    domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(domain_pattern, domain))

def format_scan_result(result_data: str) -> Dict[str, Any]:
    """
    Format scan result for display
    """
    try:
        data = json.loads(result_data)
        return data
    except json.JSONDecodeError:
        return {'error': 'Invalid result format'}

def get_ssl_status_color(days_until_expiry: int) -> str:
    """
    Get color code for SSL certificate status
    """
    if days_until_expiry < 0:
        return 'red'  # Expired
    elif days_until_expiry <= 30:
        return 'orange'  # Expiring soon
    elif days_until_expiry <= 90:
        return 'yellow'  # Warning
    else:
        return 'green'  # Good

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'

def get_ist_now() -> datetime:
    """
    Get current time in IST
    """
    return datetime.now(IST_TIMEZONE)

def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp for display in IST
    """
    if timestamp.tzinfo is None:
        # If timestamp is naive (no timezone), assume it's UTC and convert to IST
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    # Convert to IST
    ist_timestamp = timestamp.astimezone(IST_TIMEZONE)
    return ist_timestamp.strftime('%Y-%m-%d %H:%M:%S IST')

def format_timestamp_short(timestamp: datetime) -> str:
    """
    Format timestamp for display in IST (short format)
    """
    if timestamp.tzinfo is None:
        # If timestamp is naive (no timezone), assume it's UTC and convert to IST
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    # Convert to IST
    ist_timestamp = timestamp.astimezone(IST_TIMEZONE)
    return ist_timestamp.strftime('%d-%m-%Y %H:%M IST')

def format_timestamp_log(timestamp: datetime) -> str:
    """
    Format timestamp for log display in IST
    """
    if timestamp.tzinfo is None:
        # If timestamp is naive (no timezone), assume it's UTC and convert to IST
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    # Convert to IST
    ist_timestamp = timestamp.astimezone(IST_TIMEZONE)
    return ist_timestamp.strftime('%d/%m/%Y %H:%M:%S IST')

def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input
    """
    if not input_str:
        return ''
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', input_str)
    return sanitized.strip()

def parse_scan_interval(interval_str: str) -> Optional[int]:
    """
    Parse scan interval string to hours
    """
    try:
        if interval_str.endswith('h'):
            return int(interval_str[:-1])
        elif interval_str.endswith('d'):
            return int(interval_str[:-1]) * 24
        else:
            return int(interval_str)
    except (ValueError, AttributeError):
        return None 