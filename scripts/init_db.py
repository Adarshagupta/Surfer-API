#!/usr/bin/env python3
"""
Database initialization script.
This script creates the initial database tables and creates a superuser if one doesn't exist.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal, engine
from app.models.user_models import Base, User

def init_db(superuser_username: str, superuser_password: str, superuser_email: str) -> None:
    """
    Initialize the database with tables and create a superuser.
    
    Args:
        superuser_username: Username for the superuser
        superuser_password: Password for the superuser
        superuser_email: Email for the superuser
    """
    print("Running Alembic migrations...")
    try:
        # Run Alembic migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)
    
    # Create superuser if it doesn't exist
    db = SessionLocal()
    try:
        # Check if superuser exists
        superuser = db.query(User).filter(User.username == superuser_username).first()
        
        if not superuser:
            print(f"Creating superuser '{superuser_username}'...")
            
            # Create superuser
            hashed_password = User.get_password_hash(superuser_password)
            superuser = User(
                username=superuser_username,
                email=superuser_email,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True,
                full_name="Admin User"
            )
            
            db.add(superuser)
            db.commit()
            print("Superuser created successfully.")
        else:
            print(f"Superuser '{superuser_username}' already exists.")
    except IntegrityError:
        db.rollback()
        print("Error creating superuser: Username or email already exists.")
    except Exception as e:
        db.rollback()
        print(f"Error creating superuser: {e}")
    finally:
        db.close()

def main() -> None:
    """Main function to parse arguments and initialize the database."""
    parser = argparse.ArgumentParser(description="Initialize the database with tables and create a superuser.")
    parser.add_argument("--username", default="admin", help="Superuser username")
    parser.add_argument("--password", default="Admin123!", help="Superuser password")
    parser.add_argument("--email", default="admin@example.com", help="Superuser email")
    
    args = parser.parse_args()
    
    init_db(args.username, args.password, args.email)

if __name__ == "__main__":
    main() 