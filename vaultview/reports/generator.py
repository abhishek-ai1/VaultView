import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from vaultview.models import ScanResult, User
from vaultview.utils import format_scan_result, get_ssl_status_color

class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_user_report(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a user
        """
        since_date = datetime.now() - timedelta(days=days)
        
        # Get user's scan results
        scan_results = ScanResult.query.filter(
            ScanResult.user_id == user_id,
            ScanResult.id >= since_date
        ).order_by(ScanResult.id.desc()).all()
        
        # Separate SSL and DNS results
        ssl_results = [r for r in scan_results if r.result_type == 'SSL']
        dns_results = [r for r in scan_results if r.result_type == 'DNS']
        
        # Analyze SSL certificates
        ssl_analysis = self._analyze_ssl_results(ssl_results)
        
        # Analyze DNS records
        dns_analysis = self._analyze_dns_results(dns_results)
        
        # Generate summary
        summary = {
            'total_scans': len(scan_results),
            'ssl_scans': len(ssl_results),
            'dns_scans': len(dns_results),
            'domains_scanned': len(set(r.domain for r in scan_results)),
            'period_days': days
        }
        
        return {
            'summary': summary,
            'ssl_analysis': ssl_analysis,
            'dns_analysis': dns_analysis,
            'recent_results': scan_results[:10]  # Last 10 results
        }
    
    def _analyze_ssl_results(self, ssl_results: List[ScanResult]) -> Dict[str, Any]:
        """
        Analyze SSL certificate results
        """
        analysis = {
            'total_certificates': len(ssl_results),
            'valid_certificates': 0,
            'expired_certificates': 0,
            'expiring_soon': 0,
            'domains': {}
        }
        
        for result in ssl_results:
            try:
                data = format_scan_result(result.result_data)
                if 'error' not in data:
                    days_until_expiry = data.get('days_until_expiry', 0)
                    is_valid = data.get('is_valid', False)
                    
                    if is_valid:
                        analysis['valid_certificates'] += 1
                        if days_until_expiry <= 30:
                            analysis['expiring_soon'] += 1
                    else:
                        analysis['expired_certificates'] += 1
                    
                    # Track by domain
                    domain = result.domain
                    if domain not in analysis['domains']:
                        analysis['domains'][domain] = {
                            'last_scan': result.id,
                            'status': 'valid' if is_valid else 'expired',
                            'days_until_expiry': days_until_expiry
                        }
            except Exception:
                continue
        
        return analysis
    
    def _analyze_dns_results(self, dns_results: List[ScanResult]) -> Dict[str, Any]:
        """
        Analyze DNS record results including CAA records
        """
        analysis = {
            'total_scans': len(dns_results),
            'domains': {},
            'caa_analysis': {
                'domains_with_caa': 0,
                'caa_issuers': {},
                'security_score': 0
            }
        }
        
        for result in dns_results:
            try:
                data = format_scan_result(result.result_data)
                if 'error' not in data and 'records' in data:
                    domain = result.domain
                    records = data['records']
                    
                    analysis['domains'][domain] = {
                        'last_scan': result.id,
                        'record_types': list(records.keys()),
                        'has_a_records': 'A' in records,
                        'has_aaaa_records': 'AAAA' in records,
                        'has_mx_records': 'MX' in records,
                        'has_ns_records': 'NS' in records,
                        'has_caa_records': 'CAA' in records
                    }
                    
                    # Analyze CAA records
                    if 'CAA' in records and records['CAA'] != ['No CAA records found']:
                        analysis['caa_analysis']['domains_with_caa'] += 1
                        
                        for caa_record in records['CAA']:
                            if isinstance(caa_record, dict) and 'value' in caa_record:
                                issuer = caa_record['value']
                                analysis['caa_analysis']['caa_issuers'][issuer] = \
                                    analysis['caa_analysis']['caa_issuers'].get(issuer, 0) + 1
                    
                    # Calculate security score based on DNS configuration
                    security_score = 0
                    if 'A' in records:
                        security_score += 20
                    if 'AAAA' in records:
                        security_score += 10
                    if 'MX' in records:
                        security_score += 10
                    if 'NS' in records:
                        security_score += 10
                    if 'CAA' in records and records['CAA'] != ['No CAA records found']:
                        security_score += 30  # CAA records are important for security
                    if 'TXT' in records:
                        security_score += 10
                    
                    analysis['domains'][domain]['security_score'] = security_score
                    analysis['caa_analysis']['security_score'] += security_score
                    
            except Exception:
                continue
        
        # Calculate average security score
        if analysis['domains']:
            analysis['caa_analysis']['security_score'] = analysis['caa_analysis']['security_score'] / len(analysis['domains'])
        
        return analysis
    
    def generate_export_data(self, user_id: int, format_type: str = 'json') -> str:
        """
        Generate export data for user's scan results
        """
        scan_results = ScanResult.query.filter_by(user_id=user_id).order_by(ScanResult.id.desc()).all()
        
        export_data = []
        for result in scan_results:
            export_data.append({
                'id': result.id,
                'domain': result.domain,
                'type': result.result_type,
                'data': format_scan_result(result.result_data),
                'timestamp': result.id.isoformat() if hasattr(result.id, 'isoformat') else str(result.id)
            })
        
        if format_type == 'json':
            return json.dumps(export_data, indent=2)
        else:
            # Could add CSV export here
            return json.dumps(export_data, indent=2) 