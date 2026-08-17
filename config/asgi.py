"""
config 项目的 ASGI 配置。

本文件对外提供名为 application 的 ASGI 应用对象。

详细说明请参考：
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
