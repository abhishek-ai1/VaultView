import dns.resolver
import dns.reversename
import json
from typing import Dict, List, Any

def check_dns(domain):
    """
    Check DNS records for a given domain
    """
    try:
        result = {
            'domain': domain,
            'records': {}
        }
        
        # Check A records
        try:
            a_records = dns.resolver.resolve(domain, 'A')
            result['records']['A'] = [str(record) for record in a_records]
        except dns.resolver.NXDOMAIN:
            result['records']['A'] = ['Domain not found']
        except dns.resolver.NoAnswer:
            result['records']['A'] = ['No A records found']
        except Exception as e:
            result['records']['A'] = [f'Error: {str(e)}']
        
        # Check AAAA records (IPv6)
        try:
            aaaa_records = dns.resolver.resolve(domain, 'AAAA')
            result['records']['AAAA'] = [str(record) for record in aaaa_records]
        except dns.resolver.NXDOMAIN:
            result['records']['AAAA'] = ['Domain not found']
        except dns.resolver.NoAnswer:
            result['records']['AAAA'] = ['No AAAA records found']
        except Exception as e:
            result['records']['AAAA'] = [f'Error: {str(e)}']
        
        # Check MX records
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            result['records']['MX'] = [f'{record.preference} {record.exchange}' for record in mx_records]
        except dns.resolver.NXDOMAIN:
            result['records']['MX'] = ['Domain not found']
        except dns.resolver.NoAnswer:
            result['records']['MX'] = ['No MX records found']
        except Exception as e:
            result['records']['MX'] = [f'Error: {str(e)}']
        
        # Check NS records
        try:
            ns_records = dns.resolver.resolve(domain, 'NS')
            result['records']['NS'] = [str(record) for record in ns_records]
        except dns.resolver.NXDOMAIN:
            result['records']['NS'] = ['Domain not found']
        except dns.resolver.NoAnswer:
            result['records']['NS'] = ['No NS records found']
        except Exception as e:
            result['records']['NS'] = [f'Error: {str(e)}']
        
        # Check TXT records
        try:
            txt_records = dns.resolver.resolve(domain, 'TXT')
            result['records']['TXT'] = [str(record) for record in txt_records]
        except dns.resolver.NXDOMAIN:
            result['records']['TXT'] = ['Domain not found']
        except dns.resolver.NoAnswer:
            result['records']['TXT'] = ['No TXT records found']
        except Exception as e:
            result['records']['TXT'] = [f'Error: {str(e)}']
        
        # Check CNAME records
        try:
            cname_records = dns.resolver.resolve(domain, 'CNAME')
            result['records']['CNAME'] = [str(record) for record in cname_records]
        except dns.resolver.NXDOMAIN:
            result['records']['CNAME'] = ['Domain not found']
        except dns.resolver.NoAnswer:
            result['records']['CNAME'] = ['No CNAME records found']
        except Exception as e:
            result['records']['CNAME'] = [f'Error: {str(e)}']
        
        # Check CAA records (Certification Authority Authorization)
        try:
            caa_records = dns.resolver.resolve(domain, 'CAA')
            result['records']['CAA'] = []
            for record in caa_records:
                # Parse CAA record components
                caa_data = str(record)
                # CAA records have format: <flags> <tag> <value>
                parts = caa_data.split(' ', 2)
                if len(parts) >= 3:
                    flags = parts[0]
                    tag = parts[1]
                    value = parts[2].strip('"')
                    
                    caa_info = {
                        'flags': flags,
                        'tag': tag,
                        'value': value,
                        'description': get_caa_description(tag, value)
                    }
                    result['records']['CAA'].append(caa_info)
                else:
                    result['records']['CAA'].append(caa_data)
        except dns.resolver.NXDOMAIN:
            result['records']['CAA'] = ['Domain not found']
        except dns.resolver.NoAnswer:
            result['records']['CAA'] = ['No CAA records found']
        except Exception as e:
            result['records']['CAA'] = [f'Error: {str(e)}']
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({'error': f'Unexpected error for {domain}: {str(e)}'})

def get_caa_description(tag, value):
    """
    Get human-readable description for CAA record tags and values
    """
    tag_descriptions = {
        'issue': 'Certificate Authority allowed to issue certificates',
        'issuewild': 'Certificate Authority allowed to issue wildcard certificates',
        'iodef': 'Report certificate issuance requests to this URL',
        'contactemail': 'Contact email for certificate issues',
        'contactphone': 'Contact phone for certificate issues'
    }
    
    # Common CA descriptions
    ca_descriptions = {
        'letsencrypt.org': 'Let\'s Encrypt',
        'digicert.com': 'DigiCert',
        'globalsign.com': 'GlobalSign',
        'comodo.com': 'Comodo',
        'godaddy.com': 'GoDaddy',
        'sectigo.com': 'Sectigo',
        'entrust.com': 'Entrust',
        'certum.pl': 'Certum',
        'actalis.it': 'Actalis',
        'buypass.com': 'Buypass',
        'harica.gr': 'HARICA',
        'ssl.com': 'SSL.com',
        'trustwave.com': 'Trustwave',
        'certigna.fr': 'Certigna',
        'acertum.com': 'ACertum',
        'certplus.fr': 'Certplus',
        'quovadisglobal.com': 'QuoVadis',
        'certum.pl': 'Certum',
        'secomtrust.net': 'SECOM Trust Systems',
        'affirmtrust.com': 'AffirmTrust',
        'certigna.fr': 'Certigna',
        'certplus.fr': 'Certplus',
        'quovadisglobal.com': 'QuoVadis',
        'secomtrust.net': 'SECOM Trust Systems',
        'affirmtrust.com': 'AffirmTrust'
    }
    
    tag_desc = tag_descriptions.get(tag, f'Unknown tag: {tag}')
    
    if tag in ['issue', 'issuewild']:
        ca_desc = ca_descriptions.get(value, value)
        return f"{tag_desc}: {ca_desc}"
    elif tag == 'iodef':
        return f"{tag_desc}: {value}"
    else:
        return f"{tag_desc}: {value}" 