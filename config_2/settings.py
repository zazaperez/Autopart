"""
Configuración de Django para el proyecto Motopart (tienda de partes de carros).
Proyecto: tienda
App principal: AppMotopart

Alcance del negocio:
- Catálogo de productos público (visible sin iniciar sesión)
- Compra (carrito/checkout) requiere login
- Roles: Administrador y Cliente
- Proveedores: dato administrativo, sin login propio
"""

from pathlib import Path

from decouple import config  # pip install python-decouple

# ──────────────────────────────────────────────
# Rutas base
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ──────────────────────────────────────────────
# Seguridad
# ──────────────────────────────────────────────
# La SECRET_KEY real vive en tu archivo .env (no se sube a git).
SECRET_KEY = config("SECRET_KEY", default="django-insecure-CAMBIA-ESTO-en-produccion")

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# Railway inyecta esta variable automáticamente con el dominio público
# asignado a tu servicio (ej: autopart-production.up.railway.app).
# La agregamos sola, sin que tengas que tocar ALLOWED_HOSTS a mano.
RAILWAY_PUBLIC_DOMAIN = config("RAILWAY_PUBLIC_DOMAIN", default="")
if RAILWAY_PUBLIC_DOMAIN and RAILWAY_PUBLIC_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)

# Railway (y la mayoría de plataformas en la nube) terminan el HTTPS en su
# propio proxy y le mandan a Django la petición como HTTP simple por dentro.
# Sin esto, Django piensa que la conexión NO es segura y rompe el CSRF
# y las cookies "secure". Esta línea le dice a Django que confíe en el
# encabezado que pone el proxy para saber que en realidad sí es HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CSRF necesita saber explícitamente en qué dominios (con esquema https://)
# confiar. Lo construimos automáticamente a partir de ALLOWED_HOSTS, así no
# hay que mantener dos variables sincronizadas a mano.
CSRF_TRUSTED_ORIGINS = [
    f"https://{host}"
    for host in ALLOWED_HOSTS
    if host not in ("127.0.0.1", "localhost")
]

# ──────────────────────────────────────────────
# Aplicaciones instaladas
# ──────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Tu app principal: catálogo, carrito, ventas, proveedores, usuarios, todo vive aquí.
    "AppMotopart",
]

AUTHENTICATION_BACKENDS = [
    "AppMotopart.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config_2.urls"

# ──────────────────────────────────────────────
# Templates
# ──────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Muestra el contador del carrito en TODAS las páginas (navbar).
                "AppMotopart.context_processors.carrito_contador",
            ],
        },
    },
]

WSGI_APPLICATION = "config_2.wsgi.application"
ASGI_APPLICATION = "config_2.asgi.application"

# ──────────────────────────────────────────────
# Base de datos — MySQL
# ──────────────────────────────────────────────
# Requiere: pip install mysqlclient
# Antes de migrar, crea la base de datos en MySQL:
#   CREATE DATABASE motopart_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        # Si existen DB_NAME/DB_USER/etc (tu .env local) se usan esas.
        # Si no, cae automáticamente a las variables que Railway inyecta
        # solo al conectar el plugin de MySQL (MYSQLHOST, MYSQLUSER, etc).
        "NAME": config(
            "DB_NAME", default=config("MYSQLDATABASE", default="motopart_db")
        ),
        "USER": config("DB_USER", default=config("MYSQLUSER", default="root")),
        "PASSWORD": config("DB_PASSWORD", default=config("MYSQLPASSWORD", default="")),
        "HOST": config("DB_HOST", default=config("MYSQLHOST", default="localhost")),
        "PORT": config("DB_PORT", default=config("MYSQLPORT", default="3306")),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

# ──────────────────────────────────────────────
# Validación de contraseñas
# ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Tendrás 2 roles (Administrador y Cliente). La forma más simple en Django
# es usar el User por defecto + un campo "rol" o un modelo Perfil asociado (OneToOne).
# Si en el Paso 2 decides crear tu propio modelo Usuario desde cero, descomenta:
# AUTH_USER_MODEL = 'AppMotopart.Usuario'

# Backend de autenticación custom (solo si lo necesitas más adelante,
# por ejemplo login con email en vez de username):
# AUTHENTICATION_BACKENDS = [
#     'AppMotopart.backends.NombreDeTuBackend',
#     'django.contrib.auth.backends.ModelBackend',
# ]

# ──────────────────────────────────────────────
# Internacionalización
# ──────────────────────────────────────────────
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────
# Archivos estáticos (CSS, JS, logo de la tienda)
# ──────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # solo se usa en producción (collectstatic)
STATICFILES_DIRS = [BASE_DIR / "static"]  # crea esta carpeta si no existe

# WhiteNoise comprime y sirve los estáticos directamente desde Django,
# sin necesitar un servidor web aparte (nginx, etc). Ideal para Railway.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ──────────────────────────────────────────────
# Archivos de media (fotos de productos subidas por el admin)
# ──────────────────────────────────────────────
MEDIA_URL = "/imagenes/"
MEDIA_ROOT = BASE_DIR / "imagenes"

# ──────────────────────────────────────────────
# Carrito y sesión
# ──────────────────────────────────────────────
# El catálogo es público, pero para comprar exigimos login.
# Esto controla a dónde se redirige a un visitante que intenta
# acceder a una vista protegida (ej: agregar al carrito, checkout)
# sin haber iniciado sesión.
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "catalogo"  # a dónde va el cliente tras loguearse
LOGOUT_REDIRECT_URL = "catalogo"  # a dónde va tras cerrar sesión

# ──────────────────────────────────────────────
# Otros
# ──────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ──────────────────────────────────────────────
# Correo — Brevo
# ──────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
BREVO_API_KEY = config('BREVO_API_KEY', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='tu@correo.com')
PASSWORD_RESET_TIMEOUT = 3600