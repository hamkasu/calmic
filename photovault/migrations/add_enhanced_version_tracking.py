"""
Database migration: Add enhanced version tracking fields to Photo model
Created: 2025-10-28
"""
from photovault.extensions import db
from sqlalchemy import text

def upgrade():
    """Add fields to track enhanced photo versions"""
    with db.engine.connect() as conn:
        # Add original_photo_id to link enhanced versions to their original
        conn.execute(text('''
            ALTER TABLE photo 
            ADD COLUMN IF NOT EXISTS original_photo_id INTEGER REFERENCES photo(id)
        '''))
        
        # Add is_enhanced_version flag
        conn.execute(text('''
            ALTER TABLE photo 
            ADD COLUMN IF NOT EXISTS is_enhanced_version BOOLEAN NOT NULL DEFAULT FALSE
        '''))
        
        # Add enhancement_type to categorize enhancements
        conn.execute(text('''
            ALTER TABLE photo 
            ADD COLUMN IF NOT EXISTS enhancement_type VARCHAR(50)
        '''))
        
        conn.commit()
    
    print("✅ Enhanced version tracking fields added successfully")

def downgrade():
    """Remove enhanced version tracking fields"""
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE photo DROP COLUMN IF EXISTS original_photo_id'))
        conn.execute(text('ALTER TABLE photo DROP COLUMN IF EXISTS is_enhanced_version'))
        conn.execute(text('ALTER TABLE photo DROP COLUMN IF EXISTS enhancement_type'))
        conn.commit()
    
    print("✅ Enhanced version tracking fields removed")

if __name__ == '__main__':
    print("Running migration: Add enhanced version tracking")
    upgrade()
