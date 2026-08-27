# -*- coding: utf-8 -*-
"""取物路径业务接口的路由配置。"""

from django.urls import path

from . import views


app_name = "pickup_routes"

urlpatterns = [
    path(
        "routes/import/",
        views.route_import,
        name="route-import",
    ),
    path(
        "routes/",
        views.route_list,
        name="route-list",
    ),
    path(
        "routes/<int:route_id>/",
        views.route_detail,
        name="route-detail",
    ),
]
