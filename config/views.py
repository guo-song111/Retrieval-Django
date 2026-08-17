# -*- coding: utf-8 -*-
"""项目配置层的 HTTP 视图。

@author project team
@version 0.1.0
"""

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """返回用于确认服务正常运行的简单响应。"""
    return JsonResponse({"status": "ok"})
