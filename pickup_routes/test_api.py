# -*- coding: utf-8 -*-
"""取物路径 JSON 接口的测试。"""

from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import PickupRoute, RoutePoint


class RouteListApiTests(TestCase):
    """测试路径列表接口。"""

    def test_empty_route_list(self) -> None:
        """没有路径时应该返回空列表。"""
        response = self.client.get(
            reverse("pickup_routes:route-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "results": [],
                }
            },
        )

    def test_return_route_summary_and_point_count(self) -> None:
        """接口应该返回路径摘要和轨迹点数量。"""
        route = PickupRoute.objects.create(
            name="接口测试路径",
            source_filename="api-test.txt",
            source_sha256="a" * 64,
            color="#1677ff",
        )

        RoutePoint.objects.create(
            route=route,
            sequence_no=1,
            longitude=Decimal("121.415057"),
            latitude=Decimal("31.282284"),
            description="当前位置",
            status=RoutePoint.Status.CARRIER,
        )
        RoutePoint.objects.create(
            route=route,
            sequence_no=2,
            longitude=Decimal("121.415123"),
            latitude=Decimal("31.280948"),
            description="待取物品",
            status=RoutePoint.Status.NOT_GET,
        )

        response = self.client.get(
            reverse("pickup_routes:route-list")
        )

        result = response.json()["data"]["results"][0]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["id"], route.pk)
        self.assertEqual(result["name"], "接口测试路径")
        self.assertEqual(result["color"], "#1677ff")
        self.assertEqual(result["point_count"], 2)
        self.assertIn("created_at", result)

    def test_reject_post_request(self) -> None:
        """路径列表接口应该拒绝 POST 请求。"""
        response = self.client.post(
            reverse("pickup_routes:route-list")
        )

        self.assertEqual(response.status_code, 405)

    #添加接口测试
    def test_return_route_detail_with_ordered_points(self) -> None:
        """详情接口应该返回按顺序排列的轨迹点。"""
        route = PickupRoute.objects.create(
            name="详情测试路径",
            source_filename="detail-test.txt",
            source_sha256="b" * 64,
            color="#52c41a",
        )

        RoutePoint.objects.create(
            route=route,
            sequence_no=2,
            longitude=Decimal("121.416466"),
            latitude=Decimal("31.285651"),
            description="第二个点",
            status=RoutePoint.Status.NOT_GET,
        )
        RoutePoint.objects.create(
            route=route,
            sequence_no=1,
            longitude=Decimal("121.415057"),
            latitude=Decimal("31.282284"),
            description="第一个点",
            status=RoutePoint.Status.CARRIER,
        )

        response = self.client.get(
            reverse(
                "pickup_routes:route-detail",
                kwargs={"route_id": route.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"]["points"],
            [
                {
                    "id": route.points.get(sequence_no=1).pk,
                    "sequence": 1,
                    "longitude": 121.415057,
                    "latitude": 31.282284,
                    "description": "第一个点",
                    "status": "carrier",
                },
                {
                    "id": route.points.get(sequence_no=2).pk,
                    "sequence": 2,
                    "longitude": 121.416466,
                    "latitude": 31.285651,
                    "description": "第二个点",
                    "status": "notget",
                },
            ],
        )

    def test_route_detail_returns_404_for_missing_route(self) -> None:
        """查询不存在的路径时应该返回 404。"""
        response = self.client.get(
            reverse(
                "pickup_routes:route-detail",
                kwargs={"route_id": 999999},
            )
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "ROUTE_NOT_FOUND",
                    "message": "取物路径不存在",
                }
            },
        )

    def test_import_route_file(self) -> None:
        """上传有效 TXT 文件后应该创建路径和轨迹点。"""
        uploaded_file = SimpleUploadedFile(
            "route-one.txt",
            (
                "121.415057\t31.282284\t当前位置\tcarrier\n"
                "121.415123\t31.280948\t待取物品\tnotget"
            ).encode("utf-8"),
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("pickup_routes:route-import"),
            {
                "file": uploaded_file,
                "route_name": "路线一",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["name"], "路线一")
        self.assertEqual(response.json()["data"]["point_count"], 2)
        self.assertEqual(response.json()["data"]["warnings"], [])
        self.assertEqual(PickupRoute.objects.count(), 1)
        self.assertEqual(RoutePoint.objects.count(), 2)

    def test_import_requires_file(self) -> None:
        """没有上传文件时应该返回错误。"""
        response = self.client.post(
            reverse("pickup_routes:route-import"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "FILE_REQUIRED",
        )

    def test_import_rejects_non_txt_file(self) -> None:
        """上传非 TXT 文件时应该返回错误。"""
        uploaded_file = SimpleUploadedFile(
            "route.csv",
            b"test",
            content_type="text/csv",
        )

        response = self.client.post(
            reverse("pickup_routes:route-import"),
            {"file": uploaded_file},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "FILE_TYPE_INVALID",
        )

    def test_import_returns_parse_details_and_creates_no_data(self) -> None:
        """文件内容错误时应该返回行级详情且不创建数据库数据。"""
        uploaded_file = SimpleUploadedFile(
            "invalid.txt",
            b"121.415057\t31.282284\t\tunknown",
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("pickup_routes:route-import"),
            {"file": uploaded_file},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "FILE_CONTENT_INVALID",
        )
        self.assertGreater(
            len(response.json()["error"]["details"]),
            0,
        )
        self.assertEqual(PickupRoute.objects.count(), 0)
        self.assertEqual(RoutePoint.objects.count(), 0)

    def test_import_rejects_invalid_route_name(self) -> None:
        """路径名称只有空白字符时应该返回参数错误。"""
        uploaded_file = SimpleUploadedFile(
            "valid.txt",
            "121.415057\t31.282284\t当前位置\tcarrier".encode("utf-8"),
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("pickup_routes:route-import"),
            {
                "file": uploaded_file,
                "route_name": "   ",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "IMPORT_PARAMETER_INVALID",
        )
        self.assertEqual(PickupRoute.objects.count(), 0)

    def test_import_rejects_invalid_utf8(self) -> None:
        """非 UTF-8 文件应该返回内容错误。"""
        uploaded_file = SimpleUploadedFile(
            "invalid-encoding.txt",
            b"\xff\xfe",
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("pickup_routes:route-import"),
            {"file": uploaded_file},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "FILE_CONTENT_INVALID",
        )

    def test_import_rejects_get_request(self) -> None:
        """导入接口应该拒绝 GET 请求。"""
        response = self.client.get(
            reverse("pickup_routes:route-import")
        )

        self.assertEqual(response.status_code, 405)

    @override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=10 * 1024 * 1024)
    def test_import_rejects_oversized_file(self) -> None:
        """超过 5 MB 的文件应该被拒绝。"""
        uploaded_file = SimpleUploadedFile(
            "large.txt",
            b"x" * (5 * 1024 * 1024 + 1),
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("pickup_routes:route-import"),
            {"file": uploaded_file},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "FILE_TOO_LARGE",
        )

    def test_import_requires_csrf_token(self) -> None:
        """启用 CSRF 检查时没有令牌的导入请求应该被拒绝。"""
        client = Client(enforce_csrf_checks=True)
        uploaded_file = SimpleUploadedFile(
            "route.txt",
            "121.415057\t31.282284\t当前位置\tcarrier".encode("utf-8"),
            content_type="text/plain",
        )

        response = client.post(
            reverse("pickup_routes:route-import"),
            {"file": uploaded_file},
        )

        self.assertEqual(response.status_code, 403)

    def test_delete_route_cascades_to_points(self) -> None:
        """删除路径时应该级联删除其轨迹点。"""
        route = PickupRoute.objects.create(
            name="待删除路径",
            source_filename="delete-test.txt",
            source_sha256="c" * 64,
            color="#fa8c16",
        )
        RoutePoint.objects.create(
            route=route,
            sequence_no=1,
            longitude=Decimal("121.415057"),
            latitude=Decimal("31.282284"),
            description="待删除点",
            status=RoutePoint.Status.NOT_GET,
        )

        response = self.client.delete(
            reverse(
                "pickup_routes:route-detail",
                kwargs={"route_id": route.pk},
            )
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(PickupRoute.objects.filter(pk=route.pk).exists())
        self.assertEqual(RoutePoint.objects.count(), 0)

    def test_delete_returns_404_for_missing_route(self) -> None:
        """删除不存在的路径时应该返回 404。"""
        response = self.client.delete(
            reverse(
                "pickup_routes:route-detail",
                kwargs={"route_id": 999999},
            )
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "ROUTE_NOT_FOUND",
        )

    def test_delete_requires_csrf_token(self) -> None:
        """启用 CSRF 检查时没有令牌的删除请求应该被拒绝。"""
        route = PickupRoute.objects.create(
            name="CSRF 删除测试路径",
            source_filename="csrf-delete.txt",
            source_sha256="d" * 64,
            color="#722ed1",
        )
        client = Client(enforce_csrf_checks=True)

        response = client.delete(
            reverse(
                "pickup_routes:route-detail",
                kwargs={"route_id": route.pk},
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(PickupRoute.objects.filter(pk=route.pk).exists())

    def test_route_detail_rejects_post_request(self) -> None:
        """路径详情资源应该拒绝 POST 请求。"""
        response = self.client.post(
            reverse(
                "pickup_routes:route-detail",
                kwargs={"route_id": 999999},
            )
        )

        self.assertEqual(response.status_code, 405)
