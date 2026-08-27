# -*- coding: utf-8 -*-
"""项目首个健康检查接口的测试。

@author project team
@version 0.1.0
"""

from django.test import TestCase, override_settings


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


class HomePageTests(TestCase):
    """测试人员取物路径地图首页。"""

    def test_home_page_renders_map_workspace(self) -> None:
        """首页应该返回地图工作台及 CSRF 表单令牌。"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="map"')
        self.assertContains(response, 'id="import-form"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'id="map-config"')

    def test_home_page_rejects_non_get_requests(self) -> None:
        """首页只允许使用 GET 请求。"""
        response = self.client.post("/")

        self.assertEqual(response.status_code, 405)

    @override_settings(
        AMAP_JS_KEY="example-key",
        AMAP_SECURITY_JS_CODE="example-security-code",
    )
    def test_home_page_includes_map_configuration(self) -> None:
        """首页应该将高德配置传给前端。"""
        response = self.client.get("/")

        self.assertContains(response, "example-key")
        self.assertContains(response, "example-security-code")
