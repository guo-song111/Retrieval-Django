# -*- coding: utf-8 -*-
"""取物路径文件的数据库导入服务。"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction

from pickup_routes.models import PickupRoute, RoutePoint

from .route_parser import ParseWarning, parse_route_file


ROUTE_COLORS = (
    "#1677ff",
    "#52c41a",
    "#fa8c16",
    "#722ed1",
    "#eb2f96",
    "#13c2c2",
    "#f5222d",
    "#2f54eb",
)


@dataclass(frozen=True, slots=True)
class RouteImportResult:
    """表示一次路径导入的结果。"""

    route: PickupRoute
    warnings: tuple[ParseWarning, ...]


class RouteImportError(ValueError):
    """表示导入参数不符合要求。"""


def _get_safe_filename(filename: str) -> str:
    """删除文件名中可能存在的目录路径。"""
    safe_filename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    safe_filename = safe_filename.strip()

    if not safe_filename:
        raise RouteImportError("文件名不能为空")

    if len(safe_filename) > 255:
        raise RouteImportError("文件名不能超过 255 个字符")

    return safe_filename


def _get_route_name(
    filename: str,
    route_name: str | None,
) -> str:
    """取得用户指定或从文件名生成的路径名称。"""
    if route_name is None:
        name = Path(filename).stem.strip()
    else:
        name = route_name.strip()

    if not name:
        raise RouteImportError("路径名称不能为空")

    if len(name) > 100:
        raise RouteImportError("路径名称不能超过 100 个字符")

    return name


def _select_route_color() -> str:
    """从预设色板中选择当前尚未使用的颜色。"""
    used_colors = set(
        PickupRoute.objects.values_list(
            "color",
            flat=True,
        )
    )

    for color in ROUTE_COLORS:
        if color not in used_colors:
            return color

    route_count = PickupRoute.objects.count()
    return ROUTE_COLORS[route_count % len(ROUTE_COLORS)]


def import_route_file(
    *,
    filename: str,
    content: bytes,
    route_name: str | None = None,
) -> RouteImportResult:
    """解析路径文件，并在一个事务中保存路径和轨迹点。"""
    safe_filename = _get_safe_filename(filename)
    name = _get_route_name(safe_filename, route_name)

    parse_result = parse_route_file(content)
    source_sha256 = hashlib.sha256(content).hexdigest()

    with transaction.atomic():
        route = PickupRoute.objects.create(
            name=name,
            source_filename=safe_filename,
            source_sha256=source_sha256,
            color=_select_route_color(),
        )

        points = [
            RoutePoint(
                route=route,
                sequence_no=point.sequence_no,
                longitude=point.longitude,
                latitude=point.latitude,
                description=point.description,
                status=point.status,
            )
            for point in parse_result.points
        ]

        RoutePoint.objects.bulk_create(points)

    return RouteImportResult(
        route=route,
        warnings=parse_result.warnings,
    )