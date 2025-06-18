from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from vaultview.db import db
from vaultview.models import ScanResult, User
from vaultview.ssl_checker import check_ssl
from vaultview.dns_checker import check_dns
from vaultview.blacklist_checker import check_blacklist
from vaultview.email_checker import check_email
from vaultview.notifications import send_ssl_alert, send_blacklist_alert, notification_manager
from vaultview.bulk_processor import bulk_processor, parse_csv_domains, parse_text_domains, export_results_to_csv
from vaultview.utils import format_scan_result, format_timestamp
import json
import whois
from io import BytesIO
from datetime import datetime
import socket

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    """Main dashboard page"""
    # Get user's recent scan results
    scan_results = ScanResult.query.filter_by(user_id=current_user.id).order_by(ScanResult.id.desc()).limit(10).all()
    return render_template('index.html', scan_results=scan_results)

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/old')
@login_required
def index_old():
    """Old UI design for comparison"""
    scan_results = ScanResult.query.filter_by(user_id=current_user.id).order_by(ScanResult.id.desc()).limit(10).all()
    return render_template('index_old.html', scan_results=scan_results)

@main.route('/', methods=['POST'])
@login_required
def scan_domain():
    """Handle single domain scanning"""
    domain = request.form.get('domain', '').strip()
    scan_type = request.form.get('type', 'SSL')
    
    if not domain:
        flash('Please enter a domain name', 'error')
        return redirect(url_for('main.index'))
    
    try:
        if scan_type == 'SSL':
            result_data = check_ssl(domain)
            # Check for SSL alerts
            try:
                ssl_data = json.loads(result_data)
                send_ssl_alert(domain, ssl_data, current_user.id)
            except:
                pass
        elif scan_type == 'DNS':
            result_data = check_dns(domain)
        elif scan_type == 'WHOIS':
            try:
                # Set timeout for WHOIS query
                original_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(10)  # 10 second timeout
                
                whois_data = whois.whois(domain)
                
                # Restore original timeout
                socket.setdefaulttimeout(original_timeout)
                
                # Extract key fields for display with better error handling
                result_data = json.dumps({
                    'domain': whois_data.domain if whois_data.domain else domain,
                    'registrar': whois_data.registrar if whois_data.registrar else 'N/A',
                    'creation_date': str(whois_data.creation_date) if whois_data.creation_date else 'N/A',
                    'expiration_date': str(whois_data.expiration_date) if whois_data.expiration_date else 'N/A',
                    'updated_date': str(whois_data.updated_date) if whois_data.updated_date else 'N/A',
                    'status': whois_data.status if whois_data.status else 'N/A',
                    'name_servers': whois_data.name_servers if whois_data.name_servers else 'N/A',
                    'emails': whois_data.emails if whois_data.emails else 'N/A',
                    'raw': str(whois_data.text)[:1000] if whois_data.text else 'No raw data available'
                }, indent=2)
            except Exception as whois_error:
                result_data = json.dumps({
                    'error': f'WHOIS lookup failed: {str(whois_error)}',
                    'domain': domain,
                    'suggestion': 'Try checking the domain format or try again later'
                }, indent=2)
        elif scan_type == 'BLACKLIST':
            result_data = check_blacklist(domain)
            # Check for blacklist alerts
            try:
                blacklist_data = json.loads(result_data)
                send_blacklist_alert(domain, blacklist_data, current_user.id)
            except:
                pass
        elif scan_type == 'EMAIL':
            result_data = check_email(domain)
        else:
            flash('Invalid scan type', 'error')
            return redirect(url_for('main.index'))
        
        # Save scan result
        scan_result = ScanResult(
            user_id=current_user.id,
            domain=domain,
            result_type=scan_type,
            result_data=result_data
        )
        db.session.add(scan_result)
        db.session.commit()
        
        flash(f'Successfully scanned {domain} for {scan_type} information', 'success')
        
    except Exception as e:
        flash(f'Error scanning {domain}: {str(e)}', 'error')
    
    return redirect(url_for('main.index'))

@main.route('/api/scan', methods=['POST'])
@login_required
def api_scan():
    """API endpoint for scanning domains"""
    data = request.get_json()
    domain = data.get('domain', '').strip()
    scan_type = data.get('type', 'SSL')
    
    if not domain:
        return jsonify({'error': 'Domain is required'}), 400
    
    try:
        if scan_type == 'SSL':
            result_data = check_ssl(domain)
            # Check for SSL alerts
            try:
                ssl_data = json.loads(result_data)
                send_ssl_alert(domain, ssl_data, current_user.id)
            except:
                pass
        elif scan_type == 'DNS':
            result_data = check_dns(domain)
        elif scan_type == 'WHOIS':
            try:
                # Set timeout for WHOIS query
                original_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(10)  # 10 second timeout
                
                whois_data = whois.whois(domain)
                
                # Restore original timeout
                socket.setdefaulttimeout(original_timeout)
                
                # Extract key fields for display with better error handling
                result_data = json.dumps({
                    'domain': whois_data.domain if whois_data.domain else domain,
                    'registrar': whois_data.registrar if whois_data.registrar else 'N/A',
                    'creation_date': str(whois_data.creation_date) if whois_data.creation_date else 'N/A',
                    'expiration_date': str(whois_data.expiration_date) if whois_data.expiration_date else 'N/A',
                    'updated_date': str(whois_data.updated_date) if whois_data.updated_date else 'N/A',
                    'status': whois_data.status if whois_data.status else 'N/A',
                    'name_servers': whois_data.name_servers if whois_data.name_servers else 'N/A',
                    'emails': whois_data.emails if whois_data.emails else 'N/A',
                    'raw': str(whois_data.text)[:1000] if whois_data.text else 'No raw data available'
                }, indent=2)
            except Exception as whois_error:
                result_data = json.dumps({
                    'error': f'WHOIS lookup failed: {str(whois_error)}',
                    'domain': domain,
                    'suggestion': 'Try checking the domain format or try again later'
                }, indent=2)
        elif scan_type == 'BLACKLIST':
            result_data = check_blacklist(domain)
            # Check for blacklist alerts
            try:
                blacklist_data = json.loads(result_data)
                send_blacklist_alert(domain, blacklist_data, current_user.id)
            except:
                pass
        elif scan_type == 'EMAIL':
            result_data = check_email(domain)
        else:
            return jsonify({'error': 'Invalid scan type'}), 400
        
        # Save scan result
        scan_result = ScanResult(
            user_id=current_user.id,
            domain=domain,
            result_type=scan_type,
            result_data=result_data
        )
        db.session.add(scan_result)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully scanned {domain}',
            'result': json.loads(result_data)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error scanning {domain}: {str(e)}'}), 500

@main.route('/api/results')
@login_required
def api_results():
    """API endpoint to get user's scan results"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    scan_results = ScanResult.query.filter_by(user_id=current_user.id)\
        .order_by(ScanResult.id.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    results = []
    for result in scan_results.items:
        results.append({
            'id': result.id,
            'domain': result.domain,
            'type': result.result_type,
            'data': format_scan_result(result.result_data),
            'timestamp': format_timestamp(result.timestamp) if result.timestamp else None
        })
    
    return jsonify({
        'results': results,
        'total': scan_results.total,
        'pages': scan_results.pages,
        'current_page': page
    })

@main.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'VaultView is running'})

@main.route('/bulk')
@login_required
def bulk_page():
    """Redirect to the new bulk scan page"""
    return redirect(url_for('main.bulk_scan'))

@main.route('/bulk/scan', methods=['GET', 'POST'])
@login_required
def bulk_scan():
    """Simple bulk scan functionality"""
    if request.method == 'GET':
        return render_template('bulk_scan.html', user=current_user)
    
    # Handle POST request
    domains_text = request.form.get('domains', '').strip()
    scan_type = request.form.get('scan_type', 'SSL')
    
    if not domains_text:
        flash('Please enter at least one domain', 'error')
        return render_template('bulk_scan.html', user=current_user)
    
    # Parse domains
    domains = []
    for line in domains_text.splitlines():
        domain = line.strip()
        if domain and '.' in domain:
            domains.append(domain)
    
    if not domains:
        flash('No valid domains found', 'error')
        return render_template('bulk_scan.html', user=current_user)
    
    # Limit to 50 domains
    if len(domains) > 50:
        domains = domains[:50]
        flash(f'Limited to first 50 domains', 'info')
    
    results = []
    
    # Process each domain
    for domain in domains:
        try:
            if scan_type == 'SSL':
                from vaultview.ssl_checker import check_ssl
                result = check_ssl(domain)
                results.append({
                    'domain': domain,
                    'status': 'success',
                    'scan_type': 'SSL',
                    'data': json.loads(result) if result else {'error': 'No SSL data returned'},
                    'message': f'SSL check completed'
                })
                
                # Save to database
                scan_result = ScanResult(
                    domain=domain,
                    result_type='SSL',
                    result_data=result,
                    user_id=current_user.id
                )
                db.session.add(scan_result)
                
            elif scan_type == 'DNS':
                from vaultview.dns_checker import check_dns
                result = check_dns(domain)
                results.append({
                    'domain': domain,
                    'status': 'success',
                    'scan_type': 'DNS',
                    'data': json.loads(result) if result else {'error': 'No DNS data returned'},
                    'message': f'DNS check completed'
                })
                
                # Save to database
                scan_result = ScanResult(
                    domain=domain,
                    result_type='DNS',
                    result_data=result,
                    user_id=current_user.id
                )
                db.session.add(scan_result)
                
            elif scan_type == 'WHOIS':
                import whois
                import socket
                
                # Set timeout
                original_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(10)
                
                try:
                    whois_data = whois.whois(domain)
                    socket.setdefaulttimeout(original_timeout)
                    
                    # Format WHOIS data for display
                    formatted_whois = {
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
                    
                    results.append({
                        'domain': domain,
                        'status': 'success',
                        'scan_type': 'WHOIS',
                        'data': formatted_whois,
                        'message': f'WHOIS check completed'
                    })
                    
                    # Save to database
                    scan_result = ScanResult(
                        domain=domain,
                        result_type='WHOIS',
                        result_data=json.dumps(formatted_whois),
                        user_id=current_user.id
                    )
                    db.session.add(scan_result)
                    
                except Exception as e:
                    socket.setdefaulttimeout(original_timeout)
                    results.append({
                        'domain': domain,
                        'status': 'error',
                        'scan_type': 'WHOIS',
                        'data': {'error': f'WHOIS failed: {str(e)}'},
                        'message': f'WHOIS failed: {str(e)}'
                    })
                    
            elif scan_type == 'Blacklist':
                from vaultview.blacklist_checker import check_blacklist
                result = check_blacklist(domain)
                results.append({
                    'domain': domain,
                    'status': 'success',
                    'scan_type': 'Blacklist',
                    'data': json.loads(result) if result else {'error': 'No blacklist data returned'},
                    'message': f'Blacklist check completed'
                })
                
                # Save to database
                scan_result = ScanResult(
                    domain=domain,
                    result_type='Blacklist',
                    result_data=result,
                    user_id=current_user.id
                )
                db.session.add(scan_result)
                
            elif scan_type == 'EMAIL':
                from vaultview.email_checker import check_email
                result = check_email(domain)
                results.append({
                    'domain': domain,
                    'status': 'success',
                    'scan_type': 'EMAIL',
                    'data': json.loads(result) if result else {'error': 'No email data returned'},
                    'message': f'Email diagnostics completed'
                })
                
                # Save to database
                scan_result = ScanResult(
                    domain=domain,
                    result_type='EMAIL',
                    result_data=result,
                    user_id=current_user.id
                )
                db.session.add(scan_result)
                
        except Exception as e:
            results.append({
                'domain': domain,
                'status': 'error',
                'scan_type': scan_type,
                'data': {'error': f'Scan failed: {str(e)}'},
                'message': f'Scan failed: {str(e)}'
            })
    
    # Commit all results to database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
    
    flash(f'Bulk scan completed for {len(domains)} domains', 'success')
    return render_template('bulk_scan.html', user=current_user, results=results)

@main.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html')

@main.route('/api/notifications/test', methods=['POST'])
@login_required
def test_notification():
    try:
        data = request.get_json()
        notification_type = data.get('type')
        
        if notification_type == 'email':
            to_email = data.get('to_email')
            if not to_email:
                return jsonify({'error': 'Email address required'}), 400
            
            from vaultview.notifications import send_email_notification
            send_email_notification(
                to_email=to_email,
                subject='VaultView Test Notification',
                data={
                    'domain': 'example.com',
                    'scan_type': 'SSL',
                    'status': 'success',
                    'message': 'This is a test notification from VaultView',
                    'details': {
                        'test': True,
                        'timestamp': datetime.now().isoformat()
                    }
                },
                user_id=current_user.id
            )
            
        elif notification_type == 'webhook':
            webhook_url = data.get('webhook_url')
            if not webhook_url:
                return jsonify({'error': 'Webhook URL required'}), 400
            
            from vaultview.notifications import send_webhook_notification
            send_webhook_notification(
                webhook_url=webhook_url,
                data={
                    'domain': 'example.com',
                    'scan_type': 'SSL',
                    'status': 'success',
                    'message': 'This is a test webhook notification from VaultView',
                    'details': {
                        'test': True,
                        'timestamp': datetime.now().isoformat()
                    }
                },
                user_id=current_user.id
            )
        
        return jsonify({'success': True, 'message': 'Test notification sent successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Error sending test notification: {str(e)}'}), 500

@main.route('/api/results/<int:result_id>/copy')
@login_required
def copy_result(result_id):
    """Copy scan result to clipboard"""
    try:
        result = ScanResult.query.filter_by(id=result_id, user_id=current_user.id).first()
        if not result:
            return jsonify({'error': 'Result not found'}), 404
        
        # Format the result data for copying
        data = format_scan_result(result.result_data)
        
        # Create a formatted text representation
        formatted_text = f"""
Domain: {result.domain}
Scan Type: {result.result_type}
Timestamp: {format_timestamp(result.timestamp)}

Results:
{json.dumps(data, indent=2)}
        """.strip()
        
        return jsonify({
            'success': True,
            'data': formatted_text
        })
        
    except Exception as e:
        return jsonify({'error': f'Error copying result: {str(e)}'}), 500

@main.route('/api/results/<int:result_id>/export')
@login_required
def export_result(result_id):
    """Export scan result as JSON file"""
    try:
        result = ScanResult.query.filter_by(id=result_id, user_id=current_user.id).first()
        if not result:
            return jsonify({'error': 'Result not found'}), 404
        
        # Format the result data
        data = format_scan_result(result.result_data)
        
        # Create export data
        export_data = {
            'domain': result.domain,
            'scan_type': result.result_type,
            'timestamp': format_timestamp(result.timestamp),
            'results': data
        }
        
        # Create file response
        output = BytesIO()
        output.write(json.dumps(export_data, indent=2).encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'{result.domain}_{result.result_type.lower()}_{result.timestamp.strftime("%Y%m%d_%H%M%S")}.json'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error exporting result: {str(e)}'}), 500 