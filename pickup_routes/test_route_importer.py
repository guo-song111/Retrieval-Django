# -*- coding: utf-8 -*-
"""取物路径数据库导入服务的测试。"""

import hashlib
from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase

from pickup_routes.models import PickupRoute, RoutePoint
from pickup_routes.services.route_importer import (
    import_route_file,
)
from pickup_routes.services.route_parser import RouteParseError


class RouteImporterTests(TestCase):
    """测试路径文件的数据库导入过程。"""

    def test_import_route_and_points(self) -> None:
        """有效文件应该创建一条路径和全部轨迹点。"""
        content = (
            "121.415057\t31.282284\t当前位置\tcarrier\r\n"
            "121.415123\t31.280948\t待取物品\tnotget"
        ).encode("utf-8")

        result = import_route_file(
            filename="test-route.txt",
            content=content,
        )

        self.assertEqual(PickupRoute.objects.count(), 1)
        self.assertEqual(RoutePoint.objects.count(), 2)
        self.assertEqual(result.route.name, "test-route")
        self.assertEqual(
            result.route.source_sha256,
            hashlib.sha256(content).hexdigest(),
        )
        self.assertEqual(
            list(
                result.route.points.values_list(
                    "sequence_no",
                    flat=True,
                )
            ),
            [1, 2],
        )

    def test_invalid_file_does_not_create_data(self) -> None:
        """文件解析失败时不应该产生任何数据库数据。"""
        content = (
            "121.415057\t31.282284\t测试物品\tunknown"
        ).encode("utf-8")

        with self.assertRaises(RouteParseError):
            import_route_file(
                filename="invalid.txt",
                content=content,
            )

        self.assertEqual(PickupRoute.objects.count(), 0)
        self.assertEqual(RoutePoint.objects.count(), 0)

    def test_same_file_can_be_imported_more_than_once(self) -> None:
        """同一个文件应该允许作为不同路径重复导入。"""
        content = (
            "121.415057\t31.282284\t当前位置\tcarrier"
        ).encode("utf-8")

        first_result = import_route_file(
            filename="repeat.txt",
            content=content,
        )
        second_result = import_route_file(
            filename="repeat.txt",
            content=content,
        )

        self.assertNotEqual(
            first_result.route.pk,
            second_result.route.pk,
        )
        self.assertEqual(PickupRoute.objects.count(), 2)
        self.assertNotEqual(
            first_result.route.color,
            second_result.route.color,
        )
#添加事务回滚
    def test_database_error_rolls_back_route(self) -> None:
        """轨迹点写入失败时应该回滚已经创建的路径。"""
        content = (
            "121.415057\t31.282284\t当前位置\tcarrier\r\n"
            "121.415123\t31.280948\t待取物品\tnotget"
        ).encode("utf-8")

        with patch(
            (
                "pickup_routes.services.route_importer."
                "RoutePoint.objects.bulk_create"
            ),
            side_effect=DatabaseError("模拟数据库写入失败"),
        ):
            with self.assertRaises(DatabaseError):
                import_route_file(
                    filename="rollback.txt",
                    content=content,
                )

        self.assertEqual(PickupRoute.objects.count(), 0)
        self.assertEqual(RoutePoint.objects.count(), 0)
        #添加安全测试
    def test_remove_directory_from_uploaded_filename(self) -> None:
        """上传文件名中的目录部分不应该保存到数据库。"""
        content = (
            "121.415057\t31.282284\t当前位置\tcarrier"
        ).encode("utf-8")

        result = import_route_file(
            filename="../../private/route.txt",
            content=content,
        )

        self.assertEqual(
            result.route.source_filename,
            "route.txt",
        )
        self.assertEqual(result.route.name, "route")
        #添加警告传递测试
    def test_return_parser_warnings(self) -> None:
        """导入结果应该保留解析器产生的警告。"""
        content = (
            "121.415123\t31.280948\t"
            "(151,118)\t\tnotget"
        ).encode("utf-8")

        result = import_route_file(
            filename="warning.txt",
            content=content,
        )

        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(
            result.warnings[0].code,
            "EXTRA_EMPTY_COLUMN_IGNORED",
        )
        self.assertEqual(PickupRoute.objects.count(), 1)
        self.assertEqual(RoutePoint.objects.count(), 1)