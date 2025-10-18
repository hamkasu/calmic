"""make_person_id_nullable_in_photo_people

Revision ID: f1a2b3c4d5e6
Revises: e9416442732b
Create Date: 2025-10-05 05:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e9416442732b'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the unique constraint if it exists
    op.drop_constraint('unique_photo_person', 'photo_people', type_='unique')
    
    # Make person_id nullable to support unrecognized faces
    op.alter_column('photo_people', 'person_id',
                   existing_type=sa.Integer(),
                   nullable=True)


def downgrade():
    # Make person_id non-nullable again
    op.alter_column('photo_people', 'person_id',
                   existing_type=sa.Integer(),
                   nullable=False)
    
    # Re-add the unique constraint
    op.create_unique_constraint('unique_photo_person', 'photo_people', ['photo_id', 'person_id'])
