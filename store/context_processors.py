from django.conf import settings
from .models import Department, StoreLocation

def store_context(request):
    """Global template context for departments, store locator, and database indicators."""
    try:
        departments = Department.objects.prefetch_related('categories').all()
        stores = StoreLocation.objects.filter(is_active=True)[:6]
    except Exception:
        departments = []
        stores = []

    return {
        'all_departments': departments,
        'header_stores': stores,
        'active_db_name': getattr(settings, 'ACTIVE_DB_BACKEND', 'PostgreSQL'),
        'is_postgres': 'PostgreSQL' in getattr(settings, 'ACTIVE_DB_BACKEND', ''),
    }
