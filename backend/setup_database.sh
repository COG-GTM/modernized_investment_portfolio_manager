#!/bin/bash

echo "🗄️  Setting up database..."

echo "📋 Running database migrations..."
alembic upgrade head

echo "🌱 Seeding database with sample data..."
python seed_database.py

echo "📥 Loading latest nightly position file..."
python load_positions.py

echo "✅ Verifying database setup..."
python verify_persistence.py

echo "🎉 Database setup complete!"
