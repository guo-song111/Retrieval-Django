# -*- coding: utf-8 -*-
"""人员取物路径及轨迹点的数据模型。"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PickupRoute(models.Model):
    """表示一次完整的人员取物路径。"""

    name = models.CharField(
        "路径名称",
        max_length=100,
    )
    source_filename = models.CharField(
        "原始文件名",
        max_length=255,
    )
    source_sha256 = models.CharField(
        "文件摘要",
        max_length=64,
    )
    color = models.CharField(
        "路径颜色",
        max_length=7,
        default="#1677ff",
    )
    created_at = models.DateTimeField(
        "导入时间",
        auto_now_add=True,
    )

    class Meta:
        """定义路径模型的数据库行为。"""

        db_table = "pickup_route"
        ordering = ["-created_at"]
        verbose_name = "取物路径"
        verbose_name_plural = "取物路径"

    def __str__(self) -> str:
        """返回便于阅读的路径名称。"""
        return self.name


class RoutePoint(models.Model):
    """表示取物路径中的一个有序轨迹点。"""

    class Status(models.TextChoices):
        """定义轨迹点允许使用的状态。"""

        CARRIER = "carrier", "物品已取"
        NOT_GET = "notget", "物品未取"
#外键关系
    route = models.ForeignKey(
        PickupRoute,
        on_delete=models.CASCADE,
        related_name="points",
        verbose_name="所属路径",
    )
    sequence_no = models.PositiveIntegerField(
        "轨迹点顺序",
    )
    longitude = models.DecimalField(
        "经度",
        max_digits=10,
        decimal_places=6,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180),
        ],
    )
    latitude = models.DecimalField(
        "纬度",
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90),
        ],
    )
    description = models.CharField(
        "说明信息",
        max_length=500,
    )
    status = models.CharField(
        "轨迹点状态",
        max_length=10,
        choices=Status.choices,
    )

    class Meta:
        """定义轨迹点模型的数据库行为。"""

        db_table = "route_point"
        ordering = ["sequence_no"]
        verbose_name = "轨迹点"
        verbose_name_plural = "轨迹点"
        #顺序唯一约束
        constraints = [
            models.UniqueConstraint(
                fields=["route", "sequence_no"],
                name="unique_route_point_sequence",
            ),
        ]

    def __str__(self) -> str:
        """返回包含路径名称和顺序的轨迹点说明。"""
        return f"{self.route.name} - 第 {self.sequence_no} 个点"