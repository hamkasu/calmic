#!/usr/bin/env python3
"""
Monthly Quota Reset Script
Run this script as a cron job on the 1st of each month to reset all AI enhancement quotas

Cron schedule (runs at midnight on the 1st of every month):
0 0 1 * * /usr/bin/python3 /path/to/reset_quotas.py

Or use Replit Deployments cron:
Add to .replit file or use Replit's scheduled deployments feature
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from photovault import create_app
from photovault.utils.quota_manager import reset_all_quotas

def main():
    """Reset all user quotas"""
    app = create_app()
    
    with app.app_context():
        print("Starting monthly quota reset...")
        count = reset_all_quotas()
        print(f"✓ Successfully reset quotas for {count} users")
        return count

if __name__ == '__main__':
    try:
        count = main()
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error resetting quotas: {str(e)}")
        sys.exit(1)
