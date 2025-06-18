from vaultview.app import create_app
from vaultview.db import db
from vaultview.utils import get_ist_now, format_timestamp_log

app = create_app()

# Initialize database
with app.app_context():
    db.create_all()
    
    # Start the scheduler if enabled (with error handling)
    try:
        from vaultview.scheduler import scheduler
        if app.config.get('SCHEDULER_ENABLED', True):
            scheduler.start(app)  # Pass the app instance
            print("✓ Scheduler started successfully")
    except Exception as e:
        print(f"⚠ Warning: Could not start scheduler: {e}")
        print("Application will continue without scheduled monitoring")

if __name__ == '__main__':
    print(f"Starting VaultView application at {format_timestamp_log(get_ist_now())}...")
    print("Access the application at: http://127.0.0.1:5000")
    app.run(debug=app.config.get('DEBUG', False), host='0.0.0.0', port=5000) 