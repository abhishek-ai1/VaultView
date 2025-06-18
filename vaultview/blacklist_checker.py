import dns.resolver
import socket
import json
from typing import Dict, List, Any
from datetime import datetime

def check_blacklist(domain_or_ip: str) -> str:
    """
    Check if a domain or IP is listed on major DNS blacklists
    """
    try:
        # Determine if input is IP or domain
        try:
            socket.inet_aton(domain_or_ip)
            is_ip = True
            check_value = domain_or_ip
        except socket.error:
            is_ip = False
            check_value = domain_or_ip
        
        # Major DNS blacklists to check
        blacklists = {
            'spamhaus_zen': {
                'name': 'Spamhaus ZEN',
                'description': 'Combined Spamhaus blocklist',
                'query': f'{check_value}.zen.spamhaus.org',
                'response': '127.0.0.2-127.0.0.11'
            },
            'spamhaus_sbl': {
                'name': 'Spamhaus SBL',
                'description': 'Spamhaus Block List',
                'query': f'{check_value}.sbl.spamhaus.org',
                'response': '127.0.0.2'
            },
            'spamhaus_xbl': {
                'name': 'Spamhaus XBL',
                'description': 'Exploits Block List',
                'query': f'{check_value}.xbl.spamhaus.org',
                'response': '127.0.0.4-127.0.0.7'
            },
            'spamhaus_pbl': {
                'name': 'Spamhaus PBL',
                'description': 'Policy Block List',
                'query': f'{check_value}.pbl.spamhaus.org',
                'response': '127.0.0.10-127.0.0.11'
            },
            'sorbs': {
                'name': 'SORBS',
                'description': 'Spam and Open Relay Blocking System',
                'query': f'{check_value}.dnsbl.sorbs.net',
                'response': '127.0.0.10'
            },
            'barracuda': {
                'name': 'Barracuda',
                'description': 'Barracuda Reputation Block List',
                'query': f'{check_value}.b.barracudacentral.org',
                'response': '127.0.0.2'
            },
            'spamcop': {
                'name': 'SpamCop',
                'description': 'SpamCop Blocking List',
                'query': f'{check_value}.bl.spamcop.net',
                'response': '127.0.0.2'
            },
            'dnsbl_abuseat': {
                'name': 'AbuseAt',
                'description': 'AbuseAt CBL',
                'query': f'{check_value}.cbl.abuseat.org',
                'response': '127.0.0.2'
            },
            'dynip': {
                'name': 'DynIP',
                'description': 'Dynamic IP Block List',
                'query': f'{check_value}.dynip.rothen.com',
                'response': '127.0.0.2'
            },
            'dnsbl_ahbl': {
                'name': 'AHBL',
                'description': 'Abusive Hosts Blocking List',
                'query': f'{check_value}.dnsbl.ahbl.org',
                'response': '127.0.0.10'
            }
        }
        
        results = {
            'domain_or_ip': domain_or_ip,
            'type': 'IP' if is_ip else 'Domain',
            'scan_time': datetime.now().isoformat(),
            'blacklists': {},
            'summary': {
                'total_checked': len(blacklists),
                'listed_count': 0,
                'clean_count': 0,
                'error_count': 0
            }
        }
        
        # Check each blacklist
        for bl_key, bl_info in blacklists.items():
            try:
                # Perform DNS lookup
                answers = dns.resolver.resolve(bl_info['query'], 'A')
                listed = True
                response_ip = str(answers[0])
                status = 'Listed'
                
                # Check if response matches expected blacklist response
                if response_ip.startswith('127.0.0.'):
                    status = 'Listed'
                else:
                    status = 'Unknown Response'
                    
            except dns.resolver.NXDOMAIN:
                listed = False
                response_ip = None
                status = 'Clean'
            except dns.resolver.NoAnswer:
                listed = False
                response_ip = None
                status = 'Clean'
            except Exception as e:
                listed = False
                response_ip = None
                status = f'Error: {str(e)}'
                results['summary']['error_count'] += 1
            
            # Update summary counts
            if status == 'Listed':
                results['summary']['listed_count'] += 1
            elif status == 'Clean':
                results['summary']['clean_count'] += 1
            
            results['blacklists'][bl_key] = {
                'name': bl_info['name'],
                'description': bl_info['description'],
                'listed': listed,
                'status': status,
                'response_ip': response_ip,
                'query': bl_info['query']
            }
        
        # Determine overall status
        if results['summary']['listed_count'] > 0:
            results['overall_status'] = 'Listed'
            results['severity'] = 'High' if results['summary']['listed_count'] > 3 else 'Medium'
        else:
            results['overall_status'] = 'Clean'
            results['severity'] = 'Low'
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': f'Unexpected error checking blacklists for {domain_or_ip}: {str(e)}'
        })

def get_blacklist_info() -> Dict[str, Any]:
    """
    Get information about available blacklists
    """
    return {
        'total_blacklists': 10,
        'categories': {
            'spam': ['Spamhaus ZEN', 'Spamhaus SBL', 'Spamhaus XBL', 'Spamhaus PBL', 'SORBS', 'SpamCop'],
            'security': ['Barracuda', 'AbuseAt', 'AHBL'],
            'dynamic': ['DynIP']
        },
        'description': 'Checks against major DNS blacklists for spam, security, and reputation issues'
    } 