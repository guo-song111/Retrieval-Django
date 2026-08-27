"""
config 项目的总路由配置。

urlpatterns 列表负责将 URL 映射到视图。详细说明请参考：
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
路由示例请参考 Django 官方文档。
"""
from django.contrib import admin
from django.urls import include, path

from .views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", health_check, name="health-check"),
    path(
        "api/v1/",
        include("pickup_routes.urls"),
    ),
]