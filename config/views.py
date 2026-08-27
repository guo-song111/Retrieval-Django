# -*- coding: utf-8 -*-
"""项目配置层的 HTTP 视图。

@author project team
@version 0.1.0
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """返回用于确认服务正常运行的简单响应。"""
    return JsonResponse({"status": "ok"})


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    """渲染人员取物路径地图首页。"""
    return render(
        request,
        "index.html",
        {
            "map_config": {
                "amap_js_key": settings.AMAP_JS_KEY,
                "amap_security_js_code": settings.AMAP_SECURITY_JS_CODE,
            },
        },
    )
