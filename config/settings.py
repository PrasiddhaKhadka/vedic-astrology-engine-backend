"""
Django settings for AstroGyan.
Reads from environment variables (Render env vars) or .env file locally.
"""

from pathlib import Path
import dj_database_url
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent


# ─── Core ──────────────────────────────────────────────────────────────────────

SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-change-me-in-production')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost',
    cast=Csv(),
)


# ─── Installed Apps ────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    'core',
]


# ─── Middleware ────────────────────────────────────────────────────────────────

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',        # ← static files (right after security)
    'corsheaders.middleware.CorsMiddleware',             # ← CORS (before CommonMiddleware)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.SecurityHeadersMiddleware',         # ← custom security headers
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'


# ─── Templates ────────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ─── Database ──────────────────────────────────────────────────────────────────
# Render injects DATABASE_URL automatically from the linked PostgreSQL database.
# Locally, set DATABASE_URL in your .env file.
# Example local MySQL: mysql://root:password@localhost:3306/astrogyan
# Example Render PG:   postgres://user:pass@host/dbname  (auto-injected)

DATABASE_URL = config(
    'DATABASE_URL',
    default=f"mysql://root:password2025@localhost:3306/astrogyan",
)

DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,        # keep connections alive for 10 min
        conn_health_checks=True,
    )
}


# ─── Ephemeris ─────────────────────────────────────────────────────────────────
# The ephemeris/ folder must be committed to your repo.
# Render's filesystem is ephemeral but the repo files are always available.
EPHE_PATH = BASE_DIR / 'ephemeris'


# ─── DRF + Spectacular ─────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon':          '100/hour',
        'user':          '1000/hour',
        'chart':         '30/minute',
        'compatibility': '20/minute',
        'transits':      '60/minute',
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE':       'AstroGyan API',
    'DESCRIPTION': 'Open-source Vedic Astrology (Jyotish) REST API — Lahiri ayanamsa, Swiss Ephemeris',
    'VERSION':     '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': 'Chart',         'description': 'Birth chart — planets, ascendant, houses'},
        {'name': 'Panchang',      'description': 'Nakshatra, Tithi, Vara, Yoga, Karana'},
        {'name': 'Dasha',         'description': 'Vimshottari Mahadasha & Antardasha'},
        {'name': 'Divisional',    'description': 'D-series charts (D2–D60)'},
        {'name': 'Yogas',         'description': 'Vedic yoga detection'},
        {'name': 'Ashtakavarga',  'description': 'Planetary strength scoring'},
        {'name': 'Compatibility', 'description': 'Kundali Milan — Guna matching & Mangal Dosha'},
        {'name': 'Transits',      'description': 'Gochar — current & date-specific transits'},
    ],
}


# ─── CORS ──────────────────────────────────────────────────────────────────────
# CORS_ALLOW_ALL_ORIGINS is read from the env var set in render.yaml.
#
# Current state  → True  (no frontend yet — devs test from localhost)
# When you have a frontend URL, update render.yaml to:
#   CORS_ALLOW_ALL_ORIGINS = False
#   CORS_ALLOWED_ORIGINS   = "https://yourfrontend.com"

CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)

# Only used when CORS_ALLOW_ALL_ORIGINS = False
# Safe to leave as-is until you have a real frontend URL
_cors_origins = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000', cast=Csv())
CORS_ALLOWED_ORIGINS = _cors_origins

CORS_ALLOW_METHODS = ['GET', 'POST', 'OPTIONS']
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'origin',
    'x-requested-with',
    'x-api-key',
]
CORS_ALLOW_CREDENTIALS = False
CORS_PREFLIGHT_MAX_AGE  = 86400     # cache preflight for 24 hours


# ─── Security Headers ──────────────────────────────────────────────────────────

SECURE_BROWSER_XSS_FILTER   = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS             = 'DENY'

# Production HTTPS settings — Render handles SSL termination
if not DEBUG:
    SECURE_PROXY_SSL_HEADER        = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT            = True
    SECURE_HSTS_SECONDS            = 31536000    # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True
    CSRF_COOKIE_HTTPONLY           = True


# ─── Content Security Policy ───────────────────────────────────────────────────
# Allows Swagger UI assets from jsdelivr CDN

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC  = ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")
CSP_STYLE_SRC   = ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")
CSP_IMG_SRC     = ("'self'", "data:", "cdn.jsdelivr.net")
CSP_FONT_SRC    = ("'self'", "cdn.jsdelivr.net")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_SRC   = ("'none'",)
CSP_OBJECT_SRC  = ("'none'",)
CSP_BASE_URI    = ("'self'",)
CSP_FORM_ACTION = ("'self'",)


# ─── Static Files (WhiteNoise) ─────────────────────────────────────────────────

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ─── Password Validation ───────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─── Localisation ─────────────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─── Logging ───────────────────────────────────────────────────────────────────

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}