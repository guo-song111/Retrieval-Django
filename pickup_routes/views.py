# -*- coding: utf-8 -*-
"""取物路径页面和 JSON 接口视图。"""

from django.db.models import Count
from django.http import HttpRequest, HttpResponse, HttpResponseBase, JsonResponse
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

from .models import PickupRoute
from .services.route_importer import RouteImportError, import_route_file
from .services.route_parser import RouteParseError


MAX_UPLOAD_SIZE = 5 * 1024 * 1024


def _route_not_found_response() -> JsonResponse:
    """构造统一的路径不存在响应。"""
    return JsonResponse(
        {
            "error": {
                "code": "ROUTE_NOT_FOUND",
                "message": "取物路径不存在",
            }
        },
        status=404,
    )


@require_GET
def route_list(request: HttpRequest) -> JsonResponse:
    """返回全部路径的摘要信息。"""
    routes = (
        PickupRoute.objects.annotate(
            point_count=Count("points"),
        )
        .order_by("-created_at")
    )

    results = [
        {
            "id": route.pk,
            "name": route.name,
            "color": route.color,
            "point_count": route.point_count,
            "created_at": route.created_at.isoformat(),
        }
        for route in routes
    ]

    return JsonResponse(
        {
            "data": {
                "results": results,
            }
        }
    )


@require_POST
def route_import(request: HttpRequest) -> JsonResponse:
    """接收 TXT 文件并导入取物路径。"""
    uploaded_file = request.FILES.get("file")

    if uploaded_file is None:
        return JsonResponse(
            {
                "error": {
                    "code": "FILE_REQUIRED",
                    "message": "请上传路径文件",
                }
            },
            status=400,
        )

    if not uploaded_file.name.lower().endswith(".txt"):
        return JsonResponse(
            {
                "error": {
                    "code": "FILE_TYPE_INVALID",
                    "message": "只允许上传 TXT 文件",
                }
            },
            status=400,
        )

    if uploaded_file.size > MAX_UPLOAD_SIZE:
        return JsonResponse(
            {
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "文件大小不能超过 5 MB",
                }
            },
            status=400,
        )

    try:
        result = import_route_file(
            filename=uploaded_file.name,
            content=uploaded_file.read(),
            route_name=request.POST.get("route_name"),
        )
    except RouteParseError as exc:
        return JsonResponse(
            {
                "error": {
                    "code": "FILE_CONTENT_INVALID",
                    "message": str(exc),
                    "details": [
                        {
                            "line": detail.line,
                            "field": detail.field,
                            "code": detail.code,
                            "message": detail.message,
                        }
                        for detail in exc.details
                    ],
                }
            },
            status=400,
        )
    except RouteImportError as exc:
        return JsonResponse(
            {
                "error": {
                    "code": "IMPORT_PARAMETER_INVALID",
                    "message": str(exc),
                }
            },
            status=400,
        )

    return JsonResponse(
        {
            "data": {
                "id": result.route.pk,
                "name": result.route.name,
                "color": result.route.color,
                "point_count": result.route.points.count(),
                "warnings": [
                    {
                        "line": warning.line,
                        "code": warning.code,
                        "message": warning.message,
                    }
                    for warning in result.warnings
                ],
            }
        },
        status=201,
    )


@require_http_methods(["GET", "DELETE"])
def route_detail(
    request: HttpRequest,
    route_id: int,
) -> HttpResponseBase:
    """返回路径详情，或删除一条路径及其轨迹点。"""
    try:
        route_queryset = PickupRoute.objects
        if request.method == "GET":
            route_queryset = route_queryset.prefetch_related("points")
        route = route_queryset.get(pk=route_id)
    except PickupRoute.DoesNotExist:
        return _route_not_found_response()

    if request.method == "DELETE":
        route.delete()
        return HttpResponse(status=204)

    points = [
        {
            "id": point.pk,
            "sequence": point.sequence_no,
            "longitude": float(point.longitude),
            "latitude": float(point.latitude),
            "description": point.description,
            "status": point.status,
        }
        for point in route.points.all()
    ]

    return JsonResponse(
        {
            "data": {
                "id": route.pk,
                "name": route.name,
                "color": route.color,
                "points": points,
            }
        }
    )
