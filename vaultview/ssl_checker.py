import ssl
import socket
from datetime import datetime
import json

def check_ssl(domain):
    """
    Check SSL certificate information for a given domain
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
                # Extract certificate information
                subject = dict(x[0] for x in cert['subject'])
                issuer = dict(x[0] for x in cert['issuer'])
                
                # Parse dates
                not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                
                # Check if certificate is valid
                now = datetime.now()
                is_valid = not_before <= now <= not_after
                
                # Calculate days until expiration
                days_until_expiry = (not_after - now).days
                
                result = {
                    'domain': domain,
                    'subject': subject.get('commonName', 'Unknown'),
                    'issuer': issuer.get('commonName', 'Unknown'),
                    'valid_from': not_before.isoformat(),
                    'valid_until': not_after.isoformat(),
                    'is_valid': is_valid,
                    'days_until_expiry': days_until_expiry,
                    'serial_number': cert.get('serialNumber', 'Unknown'),
                    'version': cert.get('version', 'Unknown')
                }
                
                return json.dumps(result, indent=2)
                
    except socket.gaierror:
        return json.dumps({'error': f'Could not resolve domain: {domain}'})
    except socket.timeout:
        return json.dumps({'error': f'Connection timeout for: {domain}'})
    except ssl.SSLError as e:
        return json.dumps({'error': f'SSL error for {domain}: {str(e)}'})
    except Exception as e:
        return json.dumps({'error': f'Unexpected error for {domain}: {str(e)}'}) 