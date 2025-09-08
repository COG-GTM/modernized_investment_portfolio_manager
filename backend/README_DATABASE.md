# Database Setup and Persistence Guide

## Current Status
- ✅ Database schema created via Alembic migrations
- ✅ Sample data seeded via `seed_database.py`
- ✅ Database file: `portfolio.db` (106KB with sample data)

## Persistence Options

### Option 1: Commit Database File (Quick & Simple)
```bash
git add portfolio.db
git commit -m "Add seeded portfolio database with sample data"
```
**Pros:** Immediate persistence, works everywhere
**Cons:** Binary file in git, grows over time, merge conflicts

### Option 2: Seeding Script Approach (Recommended)
Keep `seed_database.py` in git, run during setup:
```bash
# After cloning repo
cd backend
alembic upgrade head  # Create schema
python seed_database.py  # Populate data
```
**Pros:** Clean repo, reproducible, version controlled logic
**Cons:** Extra setup step

### Option 3: Automatic Seeding (Best for Production)
Modify the application to auto-seed on startup if database is empty.

## Current Files Created
- `seed_database.py` - Main seeding script
- `verify_persistence.py` - Verification script  
- `check_db.py` - Simple database checker

## Recommended Approach
1. **Development**: Use seeding script approach
2. **Production**: Implement automatic seeding or use proper data migration
3. **Git**: Commit seeding scripts, not the database file

## Usage
```bash
# Fresh setup
alembic upgrade head
python seed_database.py

# Verify data
python verify_persistence.py
```
