"""
config 项目的 WSGI 配置。

本文件对外提供名为 application 的 WSGI 应用对象。

详细说明请参考：
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
