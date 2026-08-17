from django.test import TestCase

# Create your tests here.
# -*- coding: utf-8 -*-
"""取物路径和轨迹点模型的测试。"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from .models import PickupRoute, RoutePoint


class PickupRouteModelTests(TestCase):
    """测试取物路径模型。"""

    def test_route_can_contain_ordered_points(self) -> None:
        """一条路径可以包含多个有顺序的轨迹点。"""
        route = PickupRoute.objects.create(
            name="测试路径",
            source_filename="test.txt",
            source_sha256="a" * 64,
            color="#1677ff",
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

        sequence_numbers = list(
            route.points.order_by("sequence_no").values_list(
                "sequence_no",
                flat=True,
            )
        )

        self.assertEqual(sequence_numbers, [1, 2])

    def test_same_route_cannot_have_duplicate_sequence_numbers(self) -> None:
        """同一条路径不能有两个相同顺序的轨迹点。"""
        route = PickupRoute.objects.create(
            name="重复顺序测试",
            source_filename="duplicate.txt",
            source_sha256="b" * 64,
            color="#ff0000",
        )

        RoutePoint.objects.create(
            route=route,
            sequence_no=1,
            longitude=Decimal("121.415057"),
            latitude=Decimal("31.282284"),
            description="第一个点",
            status=RoutePoint.Status.CARRIER,
        )

        with self.assertRaises(IntegrityError):
            RoutePoint.objects.create(
                route=route,
                sequence_no=1,
                longitude=Decimal("121.416466"),
                latitude=Decimal("31.285651"),
                description="重复顺序的点",
                status=RoutePoint.Status.NOT_GET,
            )

    def test_deleting_route_deletes_its_points(self) -> None:
        """删除路径时应该级联删除属于它的轨迹点。"""
        route = PickupRoute.objects.create(
            name="级联删除测试",
            source_filename="cascade.txt",
            source_sha256="c" * 64,
            color="#00aa00",
        )
        point = RoutePoint.objects.create(
            route=route,
            sequence_no=1,
            longitude=Decimal("121.415057"),
            latitude=Decimal("31.282284"),
            description="待删除的点",
            status=RoutePoint.Status.NOT_GET,
        )

        route.delete()

        self.assertFalse(
            RoutePoint.objects.filter(pk=point.pk).exists()
        )

    def test_longitude_cannot_exceed_valid_range(self) -> None:
        """经度超过 180 度时，模型校验应该失败。"""
        route = PickupRoute.objects.create(
            name="坐标校验测试",
            source_filename="coordinate.txt",
            source_sha256="d" * 64,
            color="#0000ff",
        )
        point = RoutePoint(
            route=route,
            sequence_no=1,
            longitude=Decimal("181"),
            latitude=Decimal("31.282284"),
            description="非法经度",
            status=RoutePoint.Status.NOT_GET,
        )

        with self.assertRaises(ValidationError):
            point.full_clean()