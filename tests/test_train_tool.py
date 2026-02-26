"""
火车票查询工具单元测试
测试 query_train_schedule, compare_train_routes, get_train_filters 工具
"""

import unittest
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
os.chdir(root_dir)

from tools.train_tool import (
    query_train_schedule,
    compare_train_routes,
    get_train_filters,
)


class TestTrainTool(unittest.TestCase):
    """测试火车票查询工具类"""

    def setUp(self):
        """测试前的准备工作"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 生成一个未来15天内的有效日期
        self.valid_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    def tearDown(self):
        """测试后的清理工作"""
        self.loop.close()

    def run_async(self, coro):
        """运行异步函数"""
        return self.loop.run_until_complete(coro)

    def test_query_train_schedule_simple_format(self):
        """测试查询列车时刻表 - simple格式"""
        result = self.run_async(
            query_train_schedule(
                departure="北京", arrival="上海", date=self.valid_date, format="simple"
            )
        )

        self.assertIsInstance(result, str)

        # 验证包含关键信息
        self.assertIn("北京", result)
        self.assertIn("上海", result)
        self.assertIn(self.valid_date[:10], result)

        print("✅ test_query_train_schedule_simple_format 通过")

    def test_query_train_schedule_detailed_format(self):
        """测试查询列车时刻表 - detailed格式"""
        result = self.run_async(
            query_train_schedule(
                departure="北京",
                arrival="上海",
                date=self.valid_date,
                format="detailed",
            )
        )

        # 可能是字典或字符串，取决于API返回
        if isinstance(result, dict):
            self.assertIn("result", result)
        elif isinstance(result, str):
            self.assertIn("北京", result)

        print("✅ test_query_train_schedule_detailed_format 通过")

    def test_query_train_schedule_with_filter(self):
        """测试带筛选条件的列车查询"""
        result = self.run_async(
            query_train_schedule(
                departure="北京",
                arrival="上海",
                date=self.valid_date,
                filter="G",  # 只查询高铁
                format="simple",
            )
        )

        self.assertIsInstance(result, str)
        self.assertIn("北京", result)

        print("✅ test_query_train_schedule_with_filter 通过")

    def test_query_train_schedule_invalid_date(self):
        """测试无效日期"""
        invalid_date = "2020-01-01"  # 过去的日期

        with self.assertRaises(Exception):
            self.run_async(
                query_train_schedule(
                    departure="北京", arrival="上海", date=invalid_date
                )
            )

        print("✅ test_query_train_schedule_invalid_date 通过")

    def test_query_train_schedule_future_too_far(self):
        """测试超过15天的日期"""
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        with self.assertRaises(Exception):
            self.run_async(
                query_train_schedule(departure="北京", arrival="上海", date=future_date)
            )

        print("✅ test_query_train_schedule_future_too_far 通过")

    def test_query_train_schedule_invalid_station(self):
        """测试无效车站"""
        with self.assertRaises(Exception):
            self.run_async(
                query_train_schedule(
                    departure="这是一个不存在的车站",
                    arrival="上海",
                    date=self.valid_date,
                )
            )

        print("✅ test_query_train_schedule_invalid_station 通过")

    def test_compare_train_routes_two_routes(self):
        """测试对比两条路线"""
        routes = [
            {"departure": "北京", "arrival": "上海"},
            {"departure": "北京", "arrival": "广州"},
        ]

        result = self.run_async(compare_train_routes(routes, self.valid_date))

        self.assertIsInstance(result, str)
        self.assertIn("多路线列车对比", result)

        print("✅ test_compare_train_routes_two_routes 通过")

    def test_compare_train_routes_with_filter(self):
        """测试带筛选的路线对比"""
        routes = [
            {"departure": "北京", "arrival": "上海"},
            {"departure": "上海", "arrival": "深圳"},
        ]

        result = self.run_async(
            compare_train_routes(routes, self.valid_date, filter="G")
        )

        self.assertIsInstance(result, str)

        print("✅ test_compare_train_routes_with_filter 通过")

    def test_compare_train_routes_exceed_limit(self):
        """测试超过5条路线"""
        routes = [
            {"departure": "北京", "arrival": "上海"},
            {"departure": "北京", "arrival": "广州"},
            {"departure": "北京", "arrival": "深圳"},
            {"departure": "北京", "arrival": "杭州"},
            {"departure": "北京", "arrival": "南京"},
            {"departure": "北京", "arrival": "武汉"},  # 第6条
        ]

        with self.assertRaises(ValueError):
            self.run_async(compare_train_routes(routes, self.valid_date))

        print("✅ test_compare_train_routes_exceed_limit 通过")

    def test_compare_train_routes_empty_list(self):
        """测试空路线列表"""
        with self.assertRaises(Exception):
            self.run_async(compare_train_routes([], self.valid_date))

        print("✅ test_compare_train_routes_empty_list 通过")

    def test_compare_train_routes_invalid_route(self):
        """测试无效路线"""
        routes = [
            {"departure": "北京", "arrival": "上海"},
            {"departure": "北京", "arrival": ""},  # 空到达站
        ]

        result = self.run_async(compare_train_routes(routes, self.valid_date))
        self.assertIsInstance(result, str)

        print("✅ test_compare_train_routes_invalid_route 通过")

    def test_get_train_filters(self):
        """测试获取车次筛选说明"""
        result = self.run_async(get_train_filters())

        self.assertIsInstance(result, str)
        self.assertIn("车次筛选说明", result)
        self.assertIn("G", result)  # 高铁
        self.assertIn("D", result)  # 动车
        self.assertIn("出发时间段", result)

        print("✅ test_get_train_filters 通过")


if __name__ == "__main__":
    unittest.main()
