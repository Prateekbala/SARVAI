#!/bin/bash

# Database migration commands for removing email and password_hash

echo "================================================"
echo "SarvAI Database Migration Commands"
echo "================================================"
echo ""
echo "These commands handle the migration to namespace-only authentication"
echo ""

# Activate virtual environment
source venv/bin/activate

echo "1. Checking current migration status..."
alembic current
echo ""

echo "2. Running database migration (remove email and password_hash)..."
alembic upgrade remove_email_password_001
echo ""

echo "3. Verifying final migration status..."
alembic current
echo ""

echo "================================================"
echo "Migration complete!"
echo "Email and password_hash columns have been removed."
echo "================================================"
