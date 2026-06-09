import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xinfan.settings')

# Ensure logs directory exists
(Path(__file__).resolve().parent.parent / 'logs').mkdir(exist_ok=True)

application = get_wsgi_application()
