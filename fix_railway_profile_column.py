"""
Fix Railway Database - Move Stripe IDs from profile_picture to stripe_customer_id column
Run this script locally to fix the production database
"""
import os
import psycopg2
from urllib.parse import urlparse

def fix_railway_database():
    # Get Railway database URL from environment
    database_url = input("Paste your Railway DATABASE_URL (from Railway Variables tab): ").strip()
    
    if not database_url:
        print("❌ No DATABASE_URL provided")
        return
    
    try:
        # Parse the URL
        result = urlparse(database_url)
        
        # Connect to database
        print("🔌 Connecting to Railway database...")
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        cur = conn.cursor()
        
        # Check current state
        print("\n📊 Checking current columns...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' 
            ORDER BY column_name;
        """)
        columns = [row[0] for row in cur.fetchall()]
        print(f"Current columns: {', '.join(columns)}")
        
        # Add stripe_customer_id if missing
        if 'stripe_customer_id' not in columns:
            print("\n➕ Adding stripe_customer_id column...")
            cur.execute('ALTER TABLE "user" ADD COLUMN stripe_customer_id VARCHAR(255);')
            print("✅ Column added")
        else:
            print("\n✅ stripe_customer_id column already exists")
        
        # Check for corrupted data
        print("\n🔍 Checking for Stripe IDs in profile_picture column...")
        cur.execute("""
            SELECT COUNT(*) FROM "user" 
            WHERE profile_picture LIKE 'cus_%';
        """)
        corrupted_count = cur.fetchone()[0]
        print(f"Found {corrupted_count} records with Stripe IDs in profile_picture")
        
        if corrupted_count > 0:
            # Move Stripe IDs to correct column
            print("\n🔄 Moving Stripe IDs to stripe_customer_id column...")
            cur.execute("""
                UPDATE "user" 
                SET stripe_customer_id = profile_picture 
                WHERE profile_picture LIKE 'cus_%';
            """)
            print(f"✅ Moved {cur.rowcount} Stripe IDs")
            
            # Clear profile_picture
            print("\n🧹 Clearing profile_picture column...")
            cur.execute("""
                UPDATE "user" 
                SET profile_picture = NULL 
                WHERE profile_picture LIKE 'cus_%';
            """)
            print(f"✅ Cleared {cur.rowcount} records")
        
        # Commit changes
        conn.commit()
        
        # Verify fix
        print("\n✅ Verifying fix...")
        cur.execute("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(profile_picture) as has_profile_pic,
                COUNT(stripe_customer_id) as has_stripe_id
            FROM "user";
        """)
        stats = cur.fetchone()
        print(f"Total users: {stats[0]}")
        print(f"Users with profile pictures: {stats[1]}")
        print(f"Users with Stripe IDs: {stats[2]}")
        
        # Close connection
        cur.close()
        conn.close()
        
        print("\n🎉 Database fixed successfully!")
        print("\nNow test profile picture upload in your iOS app - it should work!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    print("🔧 Railway Database Fix Script")
    print("=" * 50)
    print("\nThis script will:")
    print("1. Add stripe_customer_id column if missing")
    print("2. Move Stripe IDs from profile_picture to stripe_customer_id")
    print("3. Clear profile_picture column for new uploads")
    print("\n" + "=" * 50 + "\n")
    
    fix_railway_database()
