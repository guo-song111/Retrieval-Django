"""取物路径和轨迹点的管理后台配置。"""
from django.contrib import admin

from .models import PickupRoute, RoutePoint


@admin.register(PickupRoute)
class PickupRouteAdmin(admin.ModelAdmin):
    """配置取物路径在管理后台中的显示方式。"""

    list_display = (
        "id",
        "name",
        "source_filename",
        "color",
        "created_at",
    )
    search_fields = (
        "name",
        "source_filename",
    )
    ordering = ("-created_at",)


@admin.register(RoutePoint)
class RoutePointAdmin(admin.ModelAdmin):
    """配置轨迹点在管理后台中的显示方式。"""

    list_display = (
        "id",
        "route",
        "sequence_no",
        "longitude",
        "latitude",
        "status",
    )
    list_filter = (
        "status",
        "route",
    )
    search_fields = (
        "description",
        "route__name",
    )
    ordering = (
        "route",
        "sequence_no",
    )
    list_select_related = ("route",)