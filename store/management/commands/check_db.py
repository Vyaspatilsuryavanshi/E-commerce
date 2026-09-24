import sys
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Check active database connection and verify PostgreSQL status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  AURA LUXE - DATABASE CONNECTIVITY DIAGNOSTIC"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        db_engine = connection.settings_dict.get('ENGINE', '')
        db_name = connection.settings_dict.get('NAME', '')
        db_user = connection.settings_dict.get('USER', '')
        db_host = connection.settings_dict.get('HOST', '')
        db_port = connection.settings_dict.get('PORT', '')

        self.stdout.write(f"Configured Engine: {db_engine}")
        self.stdout.write(f"Database Name:     {db_name}")
        self.stdout.write(f"Database Host:     {db_host or 'N/A'}")
        self.stdout.write(f"Database Port:     {db_port or 'N/A'}")
        self.stdout.write(f"Database User:     {db_user or 'N/A'}")

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                if row and row[0] == 1:
                    self.stdout.write(self.style.SUCCESS("\n[OK] Connection successful! Database is responding."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n[ERROR] Connection failed: {e}"))

        if 'postgresql' in db_engine:
            self.stdout.write(self.style.SUCCESS("\n>>> Active Backend: PostgreSQL <<<"))
        else:
            self.stdout.write(self.style.WARNING("\n>>> Active Backend: SQLite fallback <<<"))
            self.stdout.write("To connect to PostgreSQL:")
            self.stdout.write("1. Set your PostgreSQL password in .env: DB_PASSWORD=your_password")
            self.stdout.write("2. Make sure the database exists: psql -U postgres -c 'CREATE DATABASE ecommerce_db;'")
            self.stdout.write("3. Run: python manage.py migrate\n")
