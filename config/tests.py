# -*- coding: utf-8 -*-
"""项目首个健康检查接口的测试。

@author project team
@version 0.1.0
"""

from django.test import TestCase


class HealthCheckTests(TestCase):
    """测试项目配置层的 HTTP 视图。"""

    def test_health_check_returns_ok(self) -> None:
        """GET 请求返回成功的 JSON 响应。"""
        response = self.client.get("/healthz/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_check_rejects_non_get_requests(self) -> None:
        """该接口只接受 GET 请求。"""
        response = self.client.post("/healthz/")

        self.assertEqual(response.status_code, 405)
