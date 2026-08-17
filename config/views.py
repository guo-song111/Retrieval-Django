# -*- coding: utf-8 -*-
"""HTTP views for the project configuration layer.

@author project team
@version 0.1.0
"""

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """Return a small response used to verify that the service is running."""
    return JsonResponse({"status": "ok"})
