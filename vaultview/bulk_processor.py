import csv
import json
import os
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from flask import current_app
import pandas as pd
from io import StringIO
import uuid
import socket

class BulkProcessor:
    """Handles bulk domain processing and batch scanning"""
    
    def __init__(self):
        self.jobs = {}
        self.is_processing = False
    
    def create_job(self, domains: List[str], scan_types: List[str], user_id: int, save_results: bool = True, send_notifications: bool = True) -> str:
        """Create a new bulk processing job"""
        job_id = str(uuid.uuid4())
        
        job = {
            'id': job_id,
            'user_id': user_id,
            'domains': domains,
            'scan_types': scan_types,
            'total_domains': len(domains),
            'total_scans': len(domains) * len(scan_types),
            'completed_scans': 0,
            'failed_scans': 0,
            'results': [],
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None,
            'progress_callback': None,
            'save_results': save_results,
            'send_notifications': send_notifications
        }
        
        self.jobs[job_id] = job
        
        # Start processing immediately
        self.start_job(job_id)
        
        return job_id
    
    def start_job(self, job_id: str, progress_callback: Optional[Callable] = None):
        """Start processing a bulk job"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        job['status'] = 'processing'
        job['started_at'] = datetime.now().isoformat()
        job['progress_callback'] = progress_callback
        
        # Start processing in background thread
        thread = threading.Thread(target=self._process_job, args=(job_id,), daemon=True)
        thread.start()
    
    def _process_job(self, job_id: str):
        """Process a bulk job in the background"""
        job = self.jobs[job_id]
        
        try:
            for domain in job['domains']:
                if job['status'] == 'cancelled':
                    break
                
                domain_results = {
                    'domain': domain,
                    'scans': {},
                    'status': 'completed',
                    'errors': []
                }
                
                for scan_type in job['scan_types']:
                    if job['status'] == 'cancelled':
                        break
                    
                    try:
                        # Import scan functions dynamically
                        if scan_type == 'SSL':
                            from vaultview.ssl_checker import check_ssl
                            result = check_ssl(domain)
                            # Parse JSON result
                            try:
                                ssl_data = json.loads(result)
                                domain_results['scans'][scan_type] = {
                                    'status': 'success',
                                    'data': ssl_data
                                }
                            except:
                                domain_results['scans'][scan_type] = {
                                    'status': 'success',
                                    'data': result
                                }
                        elif scan_type == 'DNS':
                            from vaultview.dns_checker import check_dns
                            result = check_dns(domain)
                            # Parse JSON result
                            try:
                                dns_data = json.loads(result)
                                domain_results['scans'][scan_type] = {
                                    'status': 'success',
                                    'data': dns_data
                                }
                            except:
                                domain_results['scans'][scan_type] = {
                                    'status': 'success',
                                    'data': result
                                }
                        elif scan_type == 'WHOIS':
                            import whois
                            
                            # Set timeout for WHOIS query
                            original_timeout = socket.getdefaulttimeout()
                            socket.setdefaulttimeout(10)  # 10 second timeout
                            
                            try:
                                whois_data = whois.whois(domain)
                                
                                # Restore original timeout
                                socket.setdefaulttimeout(original_timeout)
                                
                                whois_result = {
                                    'domain': whois_data.domain if whois_data.domain else domain,
                                    'registrar': whois_data.registrar if whois_data.registrar else 'N/A',
                                    'creation_date': str(whois_data.creation_date) if whois_data.creation_date else 'N/A',
                                    'expiration_date': str(whois_data.expiration_date) if whois_data.expiration_date else 'N/A',
                                    'updated_date': str(whois_data.updated_date) if whois_data.updated_date else 'N/A',
                                    'status': whois_data.status if whois_data.status else 'N/A',
                                    'name_servers': whois_data.name_servers if whois_data.name_servers else 'N/A',
                                    'emails': whois_data.emails if whois_data.emails else 'N/A',
                                    'raw': str(whois_data.text)[:1000] if whois_data.text else 'No raw data available'
                                }
                                
                                domain_results['scans'][scan_type] = {
                                    'status': 'success',
                                    'data': whois_result
                                }
                            except Exception as whois_error:
                                # Restore original timeout
                                socket.setdefaulttimeout(original_timeout)
                                raise Exception(f"WHOIS lookup failed: {str(whois_error)}")
                        elif scan_type.upper() == 'BLACKLIST':
                            from vaultview.blacklist_checker import check_blacklist
                            result = check_blacklist(domain)
                            # Parse JSON result
                            try:
                                blacklist_data = json.loads(result)
                                domain_results['scans'][scan_type] = {
                                    'status': 'success',
                                    'data': blacklist_data
                                }
                            except:
                                domain_results['scans'][scan_type] = {
                                    'status': 'success',
                                    'data': result
                                }
                        elif scan_type.upper() == 'EMAIL':
                            from vaultview.email_checker import check_email
                            result = check_email(domain)
                            # Parse JSON result
                            try:
                                email_data = json.loads(result)
                                domain_results['scans'][scan_type] = {
                                    'status': 'success',
                                    'data': email_data
                                }
                            except:
                                domain_results['scans'][scan_type] = {
                                    'status': 'success',
                                    'data': result
                                }
                        else:
                            raise ValueError(f"Unknown scan type: {scan_type}")
                        
                    except Exception as e:
                        domain_results['scans'][scan_type] = {
                            'status': 'error',
                            'error': str(e)
                        }
                        domain_results['errors'].append(f"{scan_type}: {str(e)}")
                        job['failed_scans'] += 1
                    
                    job['completed_scans'] += 1
                    
                    # Update progress
                    if job['progress_callback']:
                        progress = (job['completed_scans'] / job['total_scans']) * 100
                        job['progress_callback'](progress, job['completed_scans'], job['total_scans'])
                    
                    # Small delay to prevent overwhelming
                    time.sleep(0.1)
                
                job['results'].append(domain_results)
                
                # Check if domain has errors
                if domain_results['errors']:
                    domain_results['status'] = 'partial'
                
            job['status'] = 'completed'
            job['completed_at'] = datetime.now().isoformat()
            
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)
            job['completed_at'] = datetime.now().isoformat()
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a job"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        
        # Calculate progress
        progress = 0
        if job['total_scans'] > 0:
            progress = (job['completed_scans'] / job['total_scans']) * 100
        
        return {
            'id': job['id'],
            'status': job['status'],
            'progress': progress,
            'completed_scans': job['completed_scans'],
            'total_scans': job['total_scans'],
            'failed_scans': job['failed_scans'],
            'created_at': job['created_at'],
            'started_at': job['started_at'],
            'completed_at': job['completed_at'],
            'error': job.get('error')
        }
    
    def get_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the results of a completed job"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        
        if job['status'] not in ['completed', 'failed']:
            return None
        
        return {
            'id': job['id'],
            'user_id': job['user_id'],
            'status': job['status'],
            'results': job['results'],
            'summary': self._generate_summary(job['results']),
            'created_at': job['created_at'],
            'started_at': job['started_at'],
            'completed_at': job['completed_at']
        }

    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the results of a completed job (legacy method)"""
        return self.get_results(job_id)
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for job results"""
        total_domains = len(results)
        completed_domains = len([r for r in results if r['status'] == 'completed'])
        partial_domains = len([r for r in results if r['status'] == 'partial'])
        failed_domains = len([r for r in results if r['status'] == 'failed'])
        
        scan_summary = {}
        for result in results:
            for scan_type, scan_result in result['scans'].items():
                if scan_type not in scan_summary:
                    scan_summary[scan_type] = {'success': 0, 'error': 0}
                
                if scan_result['status'] == 'success':
                    scan_summary[scan_type]['success'] += 1
                else:
                    scan_summary[scan_type]['error'] += 1
        
        return {
            'total_domains': total_domains,
            'completed_domains': completed_domains,
            'partial_domains': partial_domains,
            'failed_domains': failed_domains,
            'scan_summary': scan_summary
        }
    
    def cancel_job(self, job_id: str, user_id: int) -> bool:
        """Cancel a job (only if user owns it)"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        # Check if user owns this job
        if job['user_id'] != user_id:
            return False
        
        # Only allow cancellation if job is still pending or processing
        if job['status'] in ['pending', 'processing']:
            job['status'] = 'cancelled'
            job['completed_at'] = datetime.now().isoformat()
            return True
        
        return False
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if job['status'] in ['completed', 'failed', 'cancelled']:
                job_time = datetime.fromisoformat(job['created_at']).timestamp()
                if job_time < cutoff_time:
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]

def parse_csv_domains(file_content: str) -> List[str]:
    """Parse domains from CSV content"""
    domains = []
    
    try:
        # Try pandas first for better CSV handling
        df = pd.read_csv(StringIO(file_content))
        
        # Look for common column names
        domain_columns = ['domain', 'domains', 'url', 'urls', 'hostname', 'hostnames']
        
        for col in domain_columns:
            if col in df.columns:
                domains = df[col].dropna().astype(str).tolist()
                break
        
        # If no matching column found, use first column
        if not domains and len(df.columns) > 0:
            domains = df.iloc[:, 0].dropna().astype(str).tolist()
    
    except Exception:
        # Fallback to csv module
        try:
            csv_reader = csv.reader(StringIO(file_content))
            for row in csv_reader:
                if row and row[0].strip():
                    domains.append(row[0].strip())
        except Exception:
            pass
    
    # Clean and validate domains
    cleaned_domains = []
    for domain in domains:
        domain = domain.strip().lower()
        if domain and '.' in domain and len(domain) > 3:
            # Basic domain validation
            if not domain.startswith('http'):
                cleaned_domains.append(domain)
    
    return list(set(cleaned_domains))  # Remove duplicates

def parse_text_domains(text_content: str) -> List[str]:
    """Parse domains from plain text content"""
    domains = []
    
    lines = text_content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and '.' in line and len(line) > 3:
            # Remove common prefixes
            for prefix in ['http://', 'https://', 'www.']:
                if line.startswith(prefix):
                    line = line[len(prefix):]
            
            # Basic domain validation
            if '.' in line and len(line) > 3:
                domains.append(line.lower())
    
    return list(set(domains))  # Remove duplicates

def export_results_to_csv(results: List[Dict[str, Any]], scan_types: List[str]) -> str:
    """Export bulk scan results to CSV format"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    header = ['Domain', 'Status']
    for scan_type in scan_types:
        header.extend([f'{scan_type}_Status', f'{scan_type}_Result'])
    writer.writerow(header)
    
    # Write data
    for result in results:
        row = [result['domain'], result['status']]
        
        for scan_type in scan_types:
            scan_result = result['scans'].get(scan_type, {})
            status = scan_result.get('status', 'not_scanned')
            
            if status == 'success':
                # Try to extract key info from result
                try:
                    result_data = json.loads(scan_result['result'])
                    if scan_type == 'SSL':
                        summary = f"Valid: {result_data.get('is_valid', 'N/A')}, Expires: {result_data.get('valid_until', 'N/A')[:10]}"
                    elif scan_type == 'BLACKLIST':
                        summary = f"Status: {result_data.get('overall_status', 'N/A')}, Listed: {result_data.get('summary', {}).get('listed_count', 0)}"
                    elif scan_type == 'EMAIL':
                        summary = f"Score: {result_data.get('overall_score', 'N/A')}/100"
                    else:
                        summary = "Completed"
                except:
                    summary = "Completed"
            else:
                summary = scan_result.get('error', 'Failed')
            
            row.extend([status, summary])
        
        writer.writerow(row)
    
    return output.getvalue()

def process_bulk_scan(domains: List[str], scan_types: List[str], user_id: int) -> str:
    """Process bulk scan and return job ID"""
    processor = BulkProcessor()
    job_id = processor.create_job(domains, scan_types, user_id)
    return job_id

# Global bulk processor instance
bulk_processor = BulkProcessor() 