import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

_INSECURE_SECRET_KEY = 'django-insecure-dev-key-change-in-production-abc12345'
SECRET_KEY = os.environ.get('SECRET_KEY') or _INSECURE_SECRET_KEY

if not DEBUG and SECRET_KEY == _INSECURE_SECRET_KEY:
    raise RuntimeError(
        'SECRET_KEY 未配置：生产环境（DEBUG=False）必须通过环境变量设置 SECRET_KEY。'
    )

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1 localhost').split()

if not DEBUG and not ALLOWED_HOSTS:
    raise RuntimeError(
        'ALLOWED_HOSTS 未配置：生产环境（DEBUG=False）必须通过环境变量设置 ALLOWED_HOSTS。'
    )

# 生产环境通过 HTTPS（Cloudflare / Nginx）访问
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Cloudflare Turnstile 人机验证密钥（必须通过环境变量配置）
TURNSTILE_SITE_KEY = os.environ.get('TURNSTILE_SITE_KEY', '')
TURNSTILE_SECRET_KEY = os.environ.get('TURNSTILE_SECRET_KEY', '')

_csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')


def _csrf_trusted_origins():
    """CSRF_TRUSTED_ORIGINS 必须是带协议的完整来源（Django 4.0+ 强制要求）。

    未显式配置时从 ALLOWED_HOSTS 推导，并自动补上协议，
    否则 Django 启动时会直接抛 4_0.E001 并导致所有 POST 请求失败。
    """
    items = _csrf_origins.split() if _csrf_origins.strip() else list(ALLOWED_HOSTS)
    default_scheme = 'http' if DEBUG else 'https'
    origins = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        if '://' not in item:
            item = f'{default_scheme}://{item}'
        origins.append(item)
    return origins


CSRF_TRUSTED_ORIGINS = _csrf_trusted_origins()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.core',
    'apps.accounts',
    'apps.flights',
    'apps.mileage',
    'apps.recruitment',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'xinfan.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.turnstile',
            ],
        },
    },
]

WSGI_APPLICATION = 'xinfan.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'xinfan'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Use SQLite for local development if MySQL is not available
if os.environ.get('USE_SQLITE', 'True').lower() == 'true' and not os.environ.get('DB_PASSWORD'):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 必须带前导斜杠：Django 把它当基址直接拼接。
# 写成 'media/' 会生成相对路径 media/avatars/x.png，
# 在 /accounts/profile/ 这类深层页面上浏览器会解析成
# /accounts/media/... 从而 404，导致所有自定义头像显示为破图。
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s'},
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {'handlers': ['file', 'console'], 'level': 'WARNING', 'propagate': True},
        'django.request': {'handlers': ['file', 'console'], 'level': 'ERROR', 'propagate': False},
    },
}
