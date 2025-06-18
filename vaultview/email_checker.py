import dns.resolver
import socket
import smtplib
import ssl
import json
from typing import Dict, List, Any
from datetime import datetime
import re

def check_email(domain: str) -> str:
    """
    Comprehensive email/SMTP diagnostics for a domain
    """
    try:
        results = {
            'domain': domain,
            'scan_time': datetime.now().isoformat(),
            'mx_records': [],
            'smtp_tests': {},
            'security_records': {},
            'overall_score': 0,
            'recommendations': []
        }
        
        # 1. Check MX Records
        mx_results = check_mx_records(domain)
        results['mx_records'] = mx_results['records']
        results['mx_status'] = mx_results['status']
        
        # 2. Check Security Records (SPF, DKIM, DMARC)
        security_results = check_security_records(domain)
        results['security_records'] = security_results
        
        # 3. Test SMTP Connections
        if mx_results['records']:
            smtp_results = test_smtp_connections(domain, mx_results['records'])
            results['smtp_tests'] = smtp_results
        else:
            results['smtp_tests'] = {'error': 'No MX records found'}
        
        # 4. Calculate Overall Score
        score = calculate_email_score(results)
        results['overall_score'] = score
        results['score_level'] = get_score_level(score)
        
        # 5. Generate Recommendations
        results['recommendations'] = generate_recommendations(results)
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': f'Unexpected error checking email for {domain}: {str(e)}'
        })

def check_mx_records(domain: str) -> Dict[str, Any]:
    """Check MX records for a domain"""
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        records = []
        
        for record in mx_records:
            records.append({
                'priority': record.preference,
                'server': str(record.exchange),
                'resolved': resolve_mx_ip(str(record.exchange))
            })
        
        # Sort by priority
        records.sort(key=lambda x: x['priority'])
        
        return {
            'status': 'Found' if records else 'Not Found',
            'count': len(records),
            'records': records
        }
        
    except dns.resolver.NXDOMAIN:
        return {'status': 'Domain Not Found', 'count': 0, 'records': []}
    except dns.resolver.NoAnswer:
        return {'status': 'No MX Records', 'count': 0, 'records': []}
    except Exception as e:
        return {'status': f'Error: {str(e)}', 'count': 0, 'records': []}

def resolve_mx_ip(mx_server: str) -> str:
    """Resolve IP address for MX server"""
    try:
        answers = dns.resolver.resolve(mx_server, 'A')
        return str(answers[0])
    except:
        return 'Unresolved'

def check_security_records(domain: str) -> Dict[str, Any]:
    """Check SPF, DKIM, and DMARC records"""
    results = {
        'spf': check_spf_record(domain),
        'dkim': check_dkim_records(domain),
        'dmarc': check_dmarc_record(domain)
    }
    return results

def check_spf_record(domain: str) -> Dict[str, Any]:
    """Check SPF record"""
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        
        for record in txt_records:
            record_str = str(record)
            if record_str.startswith('"v=spf1'):
                # Parse SPF record
                spf_parts = record_str.strip('"').split()
                mechanisms = []
                
                for part in spf_parts[1:]:  # Skip v=spf1
                    if part.startswith('include:'):
                        mechanisms.append(f"Include: {part.split(':')[1]}")
                    elif part.startswith('ip4:'):
                        mechanisms.append(f"IP4: {part.split(':')[1]}")
                    elif part.startswith('ip6:'):
                        mechanisms.append(f"IP6: {part.split(':')[1]}")
                    elif part in ['all', '~all', '-all', '+all']:
                        mechanisms.append(f"Default: {part}")
                    else:
                        mechanisms.append(part)
                
                return {
                    'found': True,
                    'record': record_str.strip('"'),
                    'mechanisms': mechanisms,
                    'status': 'Valid'
                }
        
        return {'found': False, 'status': 'Not Found'}
        
    except dns.resolver.NXDOMAIN:
        return {'found': False, 'status': 'Domain Not Found'}
    except dns.resolver.NoAnswer:
        return {'found': False, 'status': 'No TXT Records'}
    except Exception as e:
        return {'found': False, 'status': f'Error: {str(e)}'}

def check_dkim_records(domain: str) -> Dict[str, Any]:
    """Check DKIM records (common selectors)"""
    common_selectors = ['default', 'google', 'selector1', 'selector2', 'k1', 'mail']
    dkim_records = []
    
    for selector in common_selectors:
        try:
            dkim_domain = f"{selector}._domainkey.{domain}"
            txt_records = dns.resolver.resolve(dkim_domain, 'TXT')
            
            for record in txt_records:
                record_str = str(record)
                if 'v=DKIM1' in record_str:
                    dkim_records.append({
                        'selector': selector,
                        'record': record_str.strip('"'),
                        'status': 'Valid'
                    })
                    break
                    
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            continue
        except Exception:
            continue
    
    return {
        'found': len(dkim_records) > 0,
        'count': len(dkim_records),
        'records': dkim_records,
        'status': 'Found' if dkim_records else 'Not Found'
    }

def check_dmarc_record(domain: str) -> Dict[str, Any]:
    """Check DMARC record"""
    try:
        dmarc_domain = f"_dmarc.{domain}"
        txt_records = dns.resolver.resolve(dmarc_domain, 'TXT')
        
        for record in txt_records:
            record_str = str(record)
            if 'v=DMARC1' in record_str:
                # Parse DMARC record
                dmarc_parts = record_str.strip('"').split(';')
                policy = {}
                
                for part in dmarc_parts:
                    part = part.strip()
                    if '=' in part:
                        key, value = part.split('=', 1)
                        policy[key.strip()] = value.strip()
                
                return {
                    'found': True,
                    'record': record_str.strip('"'),
                    'policy': policy,
                    'status': 'Valid'
                }
        
        return {'found': False, 'status': 'Not Found'}
        
    except dns.resolver.NXDOMAIN:
        return {'found': False, 'status': 'Domain Not Found'}
    except dns.resolver.NoAnswer:
        return {'found': False, 'status': 'No TXT Records'}
    except Exception as e:
        return {'found': False, 'status': f'Error: {str(e)}'}

def test_smtp_connections(domain: str, mx_records: List[Dict]) -> Dict[str, Any]:
    """Test SMTP connections to MX servers"""
    results = {}
    
    for mx_record in mx_records[:3]:  # Test top 3 MX servers
        server = mx_record['server']
        ip = mx_record['resolved']
        
        if ip == 'Unresolved':
            results[server] = {'status': 'Unresolved IP', 'error': 'Cannot resolve IP'}
            continue
        
        server_results = {
            'ip': ip,
            'priority': mx_record['priority'],
            'tests': {}
        }
        
        # Test SMTP connection
        try:
            with socket.create_connection((ip, 25), timeout=10) as sock:
                server_results['tests']['smtp_25'] = {
                    'status': 'Connected',
                    'banner': sock.recv(1024).decode('utf-8', errors='ignore').strip()
                }
        except Exception as e:
            server_results['tests']['smtp_25'] = {
                'status': 'Failed',
                'error': str(e)
            }
        
        # Test SMTP with STARTTLS
        try:
            with socket.create_connection((ip, 25), timeout=10) as sock:
                # Read banner
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                
                # Send EHLO
                sock.send(b'EHLO test.com\r\n')
                response = sock.recv(1024).decode('utf-8', errors='ignore')
                
                if 'STARTTLS' in response:
                    server_results['tests']['starttls'] = {
                        'status': 'Supported',
                        'banner': banner.strip()
                    }
                else:
                    server_results['tests']['starttls'] = {
                        'status': 'Not Supported',
                        'banner': banner.strip()
                    }
        except Exception as e:
            server_results['tests']['starttls'] = {
                'status': 'Failed',
                'error': str(e)
            }
        
        # Test SMTP over SSL
        try:
            context = ssl.create_default_context()
            with socket.create_connection((ip, 465), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=server) as ssock:
                    banner = ssock.recv(1024).decode('utf-8', errors='ignore')
                    server_results['tests']['smtp_ssl'] = {
                        'status': 'Connected',
                        'banner': banner.strip()
                    }
        except Exception as e:
            server_results['tests']['smtp_ssl'] = {
                'status': 'Failed',
                'error': str(e)
            }
        
        results[server] = server_results
    
    return results

def calculate_email_score(results: Dict) -> int:
    """Calculate overall email security score (0-100)"""
    score = 0
    
    # MX Records (20 points)
    if results['mx_records']:
        score += 20
    
    # SPF Record (20 points)
    if results['security_records']['spf']['found']:
        score += 20
    
    # DKIM Records (20 points)
    if results['security_records']['dkim']['found']:
        score += 20
    
    # DMARC Record (20 points)
    if results['security_records']['dmarc']['found']:
        score += 20
    
    # SMTP Security (20 points)
    smtp_secure = False
    for server_results in results['smtp_tests'].values():
        if isinstance(server_results, dict) and 'tests' in server_results:
            if (server_results['tests'].get('starttls', {}).get('status') == 'Supported' or
                server_results['tests'].get('smtp_ssl', {}).get('status') == 'Connected'):
                smtp_secure = True
                break
    
    if smtp_secure:
        score += 20
    
    return score

def get_score_level(score: int) -> str:
    """Get score level description"""
    if score >= 80:
        return 'Excellent'
    elif score >= 60:
        return 'Good'
    elif score >= 40:
        return 'Fair'
    elif score >= 20:
        return 'Poor'
    else:
        return 'Very Poor'

def generate_recommendations(results: Dict) -> List[str]:
    """Generate recommendations based on scan results"""
    recommendations = []
    
    if not results['mx_records']:
        recommendations.append("Add MX records to enable email delivery")
    
    if not results['security_records']['spf']['found']:
        recommendations.append("Add SPF record to prevent email spoofing")
    
    if not results['security_records']['dkim']['found']:
        recommendations.append("Add DKIM record for email authentication")
    
    if not results['security_records']['dmarc']['found']:
        recommendations.append("Add DMARC record to monitor email authentication")
    
    # Check SMTP security
    smtp_secure = False
    for server_results in results['smtp_tests'].values():
        if isinstance(server_results, dict) and 'tests' in server_results:
            if (server_results['tests'].get('starttls', {}).get('status') == 'Supported' or
                server_results['tests'].get('smtp_ssl', {}).get('status') == 'Connected'):
                smtp_secure = True
                break
    
    if not smtp_secure:
        recommendations.append("Enable STARTTLS or SMTP over SSL for secure email transmission")
    
    if not recommendations:
        recommendations.append("Email configuration looks good! Keep monitoring for changes.")
    
    return recommendations 