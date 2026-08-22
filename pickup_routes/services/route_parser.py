# -*- coding: utf-8 -*-
"""取物路径 TXT 文件的解析服务。"""

from dataclasses import dataclass
from decimal import Decimal
import csv
from decimal import Decimal, InvalidOperation
from io import StringIO

@dataclass(frozen=True, slots=True)
class ParsedRoutePoint:
    """表示从 TXT 文件中解析出的一个轨迹点。"""

    sequence_no: int
    longitude: Decimal
    latitude: Decimal
    description: str
    status: str
    source_line: int


@dataclass(frozen=True, slots=True)
class ParseWarning:
    """表示不阻止导入的文件格式警告。"""

    line: int
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ParseResult:
    """表示一次文件解析的完整结果。"""

    points: tuple[ParsedRoutePoint, ...]
    warnings: tuple[ParseWarning, ...]


@dataclass(frozen=True, slots=True)
class ParseErrorDetail:
    """表示文件中一项具体的格式错误。"""

    line: int | None
    field: str | None
    code: str
    message: str


class RouteParseError(ValueError):
    """表示路径文件无法通过格式或内容校验。"""

    def __init__(
        self,
        message: str,
        details: tuple[ParseErrorDetail, ...],
    ) -> None:
        """保存总体错误信息和具体错误列表。"""
        super().__init__(message)
        self.details = details


VALID_STATUSES = frozenset({"carrier", "notget"})
MAX_POINTS = 10_000
MAX_DESCRIPTION_LENGTH = 500


def _parse_coordinate(
    raw_value: str,
    field: str,
    line: int,
    minimum: Decimal,
    maximum: Decimal,
    errors: list[ParseErrorDetail],
) -> Decimal | None:
    """解析并校验一个经纬度字段。"""
    value_text = raw_value.strip()

    try:
        value = Decimal(value_text)
    except InvalidOperation:
        errors.append(
            ParseErrorDetail(
                line=line,
                field=field,
                code="INVALID_NUMBER",
                message=f"{field}必须是有效数字",
            )
        )
        return None

    if not value.is_finite():
        errors.append(
            ParseErrorDetail(
                line=line,
                field=field,
                code="INVALID_NUMBER",
                message=f"{field}必须是有限数字",
            )
        )
        return None

    if value < minimum or value > maximum:
        errors.append(
            ParseErrorDetail(
                line=line,
                field=field,
                code="OUT_OF_RANGE",
                message=(
                    f"{field}必须在 {minimum} 到 "
                    f"{maximum} 之间"
                ),
            )
        )
        return None

    return value


def parse_route_file(content: bytes) -> ParseResult:
    """解析并校验一个取物路径 TXT 文件。"""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RouteParseError(
            "文件编码错误",
            (
                ParseErrorDetail(
                    line=None,
                    field=None,
                    code="INVALID_ENCODING",
                    message="文件必须使用 UTF-8 编码",
                ),
            ),
        ) from exc

    points: list[ParsedRoutePoint] = []
    warnings: list[ParseWarning] = []
    errors: list[ParseErrorDetail] = []

    reader = csv.reader(
        StringIO(text, newline=""),
        delimiter="\t",
    )

    for source_line, row in enumerate(reader, start=1):
        if not row or all(not field.strip() for field in row):
            warnings.append(
                ParseWarning(
                    line=source_line,
                    code="EMPTY_LINE_IGNORED",
                    message="已忽略空白行",
                )
            )
            continue

        if (
            len(row) == 5
            and not row[3].strip()
            and row[4].strip().lower() in VALID_STATUSES
        ):
            row = [row[0], row[1], row[2], row[4]]
            warnings.append(
                ParseWarning(
                    line=source_line,
                    code="EXTRA_EMPTY_COLUMN_IGNORED",
                    message="已忽略状态字段前的额外空列",
                )
            )

        if len(row) != 4:
            errors.append(
                ParseErrorDetail(
                    line=source_line,
                    field=None,
                    code="COLUMN_COUNT_INVALID",
                    message="每行必须包含四个字段",
                )
            )
            continue

        (
            longitude_text,
            latitude_text,
            description_text,
            status_text,
        ) = row

        longitude = _parse_coordinate(
            longitude_text,
            "经度",
            source_line,
            Decimal("-180"),
            Decimal("180"),
            errors,
        )
        latitude = _parse_coordinate(
            latitude_text,
            "纬度",
            source_line,
            Decimal("-90"),
            Decimal("90"),
            errors,
        )

        description = description_text.strip()
        status = status_text.strip().lower()

        if not description:
            errors.append(
                ParseErrorDetail(
                    line=source_line,
                    field="description",
                    code="DESCRIPTION_REQUIRED",
                    message="说明信息不能为空",
                )
            )
        elif len(description) > MAX_DESCRIPTION_LENGTH:
            errors.append(
                ParseErrorDetail(
                    line=source_line,
                    field="description",
                    code="DESCRIPTION_TOO_LONG",
                    message="说明信息不能超过 500 个字符",
                )
            )

        if status not in VALID_STATUSES:
            errors.append(
                ParseErrorDetail(
                    line=source_line,
                    field="status",
                    code="STATUS_INVALID",
                    message="状态必须是 carrier 或 notget",
                )
            )

        if (
            longitude is None
            or latitude is None
            or not description
            or len(description) > MAX_DESCRIPTION_LENGTH
            or status not in VALID_STATUSES
        ):
            continue

        points.append(
            ParsedRoutePoint(
                sequence_no=len(points) + 1,
                longitude=longitude,
                latitude=latitude,
                description=description,
                status=status,
                source_line=source_line,
            )
        )

    if len(points) > MAX_POINTS:
        errors.append(
            ParseErrorDetail(
                line=None,
                field=None,
                code="TOO_MANY_POINTS",
                message="每条路径最多允许 10000 个轨迹点",
            )
        )

    if not points and not errors:
        errors.append(
            ParseErrorDetail(
                line=None,
                field=None,
                code="EMPTY_FILE",
                message="文件中没有有效轨迹点",
            )
        )

    if errors:
        raise RouteParseError(
            "文件包含无效数据",
            tuple(errors),
        )

    return ParseResult(
        points=tuple(points),
        warnings=tuple(warnings),
    )