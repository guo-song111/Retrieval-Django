"""
Django 配置项目的设置。

本文件由 Django 6.1 的 startproject 命令生成。

本文件的详细说明请参考：
https://docs.djangoproject.com/en/6.1/topics/settings/

全部配置项及其取值请参考：
https://docs.djangoproject.com/en/6.1/ref/settings/
"""

from pathlib import Path

# 以项目根目录为基准构造其他路径。
BASE_DIR = Path(__file__).resolve().parent.parent


# 快速开发配置，不适合直接用于生产环境。
# 生产部署前请按照 Django 部署检查清单调整。

# 安全提示：生产环境的密钥必须保密。
SECRET_KEY = 'django-insecure-ov$sju4+tgx0i4k4qfvde3#r69b2e!(++nzity6qf-!hg23&0$'

# 安全提示：生产环境不要开启调试模式。
DEBUG = True

ALLOWED_HOSTS = []


# 应用配置。

#Django 功能模块
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

WSGI_APPLICATION = 'config.wsgi.application'


# 数据库配置。
# 配置说明：https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# 静态文件配置（CSS、JavaScript 和图片）。
# 配置说明：https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'


# 邮件配置。
# 配置说明：https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
