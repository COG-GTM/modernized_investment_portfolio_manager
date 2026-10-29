#!/bin/bash

echo "🗄️  Setting up database..."

echo "📋 Running database migrations..."
alembic upgrade head

echo "🌱 Seeding database with sample data..."
python seed_database.py

echo "🌍 Loading ESG emissions feed from inbound/esg..."
python -m esg.load_esg_feed --all || exit 1

echo "✅ Verifying database setup..."
python verify_persistence.py

echo "🎉 Database setup complete!"
