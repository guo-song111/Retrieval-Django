# -*- coding: utf-8 -*-
"""取物路径 TXT 解析器的测试。"""

from decimal import Decimal

from django.test import SimpleTestCase

from .services.route_parser import (
    RouteParseError,
    parse_route_file,
)


class RouteParserTests(SimpleTestCase):
    """测试路径文件的解析和校验。"""

    def test_parse_standard_route_file(self) -> None:
        """标准四字段文件能够解析为有序轨迹点。"""
        content = (
            "121.415057\t31.282284\t当前位置\tcarrier\r\n"
            "121.415123\t31.280948\t待取物品\tnotget"
        ).encode("utf-8")

        result = parse_route_file(content)

        self.assertEqual(len(result.points), 2)
        self.assertEqual(result.points[0].sequence_no, 1)
        self.assertEqual(
            result.points[0].longitude,
            Decimal("121.415057"),
        )
        self.assertEqual(result.points[1].status, "notget")
        self.assertEqual(result.warnings, ())

    def test_parse_official_extra_empty_column(self) -> None:
        """官方样例中的额外空列可以兼容解析。"""
        content = (
            "121.415123\t31.280948\t"
            "(151,118)\t\tnotget"
        ).encode("utf-8")

        result = parse_route_file(content)

        self.assertEqual(len(result.points), 1)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(
            result.warnings[0].code,
            "EXTRA_EMPTY_COLUMN_IGNORED",
        )

    def test_reject_invalid_status(self) -> None:
        """未知的轨迹点状态应该导致解析失败。"""
        content = (
            "121.415057\t31.282284\t测试物品\tunknown"
        ).encode("utf-8")

        with self.assertRaises(RouteParseError) as context:
            parse_route_file(content)

        self.assertEqual(
            context.exception.details[0].code,
            "STATUS_INVALID",
        )


#异常检测
    def test_parse_complete_official_sample(self) -> None:
        """完整官方样例应该解析为六个轨迹点。"""
        content = (
            "121.415057\t31.282284\t"
            "current location\tcarrier\r\n"
            "121.415123\t31.280948\t"
            "(151,118)\t\tnotget\r\n"
            "121.416466\t31.285651\t"
            "(385,124)\t\tnotget\r\n"
            "121.418907\t31.287347\t"
            "(650,124)\t\tnotget\r\n"
            "121.410134\t31.286498\t"
            "(689,124)\t\tnotget\r\n"
            "121.412239\t31.283042\t"
            "(317,244)\t\tnotget"
        ).encode("utf-8")

        result = parse_route_file(content)

        self.assertEqual(len(result.points), 6)
        self.assertEqual(
            [point.sequence_no for point in result.points],
            [1, 2, 3, 4, 5, 6],
        )
        self.assertEqual(result.points[0].status, "carrier")
        self.assertEqual(result.points[5].status, "notget")
        self.assertEqual(len(result.warnings), 5)
        self.assertEqual(
            [warning.line for warning in result.warnings],
            [2, 3, 4, 5, 6],
        )

    def test_accept_utf8_bom(self) -> None:
        """带有 UTF-8 BOM 的文件也应该正常解析。"""
        content = (
            "121.415057\t31.282284\t当前位置\tcarrier"
        ).encode("utf-8-sig")

        result = parse_route_file(content)

        self.assertEqual(len(result.points), 1)
        self.assertEqual(
            result.points[0].description,
            "当前位置",
        )

    def test_ignore_blank_line_with_warning(self) -> None:
        """空白行应该被忽略并生成警告。"""
        content = (
            "\r\n"
            "121.415057\t31.282284\t当前位置\tcarrier"
        ).encode("utf-8")

        result = parse_route_file(content)

        self.assertEqual(len(result.points), 1)
        self.assertEqual(
            result.warnings[0].code,
            "EMPTY_LINE_IGNORED",
        )
        self.assertEqual(result.points[0].source_line, 2)

    def test_reject_out_of_range_coordinate(self) -> None:
        """超出范围的经纬度应该导致解析失败。"""
        content = (
            "181\t31.282284\t测试物品\tnotget"
        ).encode("utf-8")

        with self.assertRaises(RouteParseError) as context:
            parse_route_file(content)

        error_codes = {
            detail.code
            for detail in context.exception.details
        }
        self.assertIn("OUT_OF_RANGE", error_codes)

    def test_reject_non_finite_coordinate(self) -> None:
        """NaN 等非有限数字应该导致解析失败。"""
        content = (
            "NaN\t31.282284\t测试物品\tnotget"
        ).encode("utf-8")

        with self.assertRaises(RouteParseError) as context:
            parse_route_file(content)

        error_codes = {
            detail.code
            for detail in context.exception.details
        }
        self.assertIn("INVALID_NUMBER", error_codes)

    def test_reject_invalid_column_count(self) -> None:
        """字段数量不是四列时应该导致解析失败。"""
        content = (
            "121.415057\t31.282284\t缺少状态"
        ).encode("utf-8")

        with self.assertRaises(RouteParseError) as context:
            parse_route_file(content)

        self.assertEqual(
            context.exception.details[0].code,
            "COLUMN_COUNT_INVALID",
        )

    def test_reject_invalid_encoding(self) -> None:
        """非 UTF-8 编码内容应该导致解析失败。"""
        with self.assertRaises(RouteParseError) as context:
            parse_route_file(b"\xff\xfe\xff")

        self.assertEqual(
            context.exception.details[0].code,
            "INVALID_ENCODING",
        )

    def test_reject_empty_file(self) -> None:
        """没有轨迹点的空文件应该导致解析失败。"""
        with self.assertRaises(RouteParseError) as context:
            parse_route_file(b"")

        self.assertEqual(
            context.exception.details[0].code,
            "EMPTY_FILE",
        )