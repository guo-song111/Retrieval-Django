"""
Django 配置项目的设置。

本文件由 Django 6.1 的 startproject 命令生成。

本文件的详细说明请参考：
https://docs.djangoproject.com/en/6.1/topics/settings/

全部配置项及其取值请参考：
https://docs.djangoproject.com/en/6.1/ref/settings/
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 以项目根目录为基准构造其他路径。
BASE_DIR = Path(__file__).resolve().parent.parent
# 读取项目根目录下的本地环境变量文件。
load_dotenv(BASE_DIR / ".env")

# 快速开发配置，不适合直接用于生产环境。
# 生产部署前请按照 Django 部署检查清单调整。

# 安全提示：生产环境的密钥必须保密。
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "dev-only-key-change-before-deployment",
)

# 安全提示：生产环境不要开启调试模式。
# 将环境变量中的字符串转换为布尔值。
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

# 高德地图 Web 端密钥只从本地环境变量读取，不提交到版本库。
AMAP_JS_KEY = os.getenv("AMAP_JS_KEY", "").strip()
AMAP_SECURITY_JS_CODE = os.getenv("AMAP_SECURITY_JS_CODE", "").strip()

# 将逗号分隔的主机名转换为列表。
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if host.strip()
]


# 应用配置。

#Django 功能模块
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "pickup_routes",
]
#中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
#总路由
ROOT_URLCONF = 'config.urls'
#模板配置
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'


# 数据库配置。
# 配置说明：https://docs.djangoproject.com/en/6.1/ref/settings/#databases

# MySQL 数据库配置。
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DATABASE", "retrieval"),
        "USER": os.getenv("MYSQL_USER", "retrieval_user"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
        "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "PORT": os.getenv("MYSQL_PORT", "3307"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}


# 用户密码校验配置。
# 配置说明：https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# 国际化配置。
# 配置说明：https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# 静态文件配置（CSS、JavaScript 和图片）。
# 配置说明：https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'

# 从项目根目录加载前端静态资源。
STATICFILES_DIRS = [BASE_DIR / 'static']

# 允许导入接口接收不超过 5 MB 的路径文件，并预留 multipart 请求开销。
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024


# 邮件配置。
# 配置说明：https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
