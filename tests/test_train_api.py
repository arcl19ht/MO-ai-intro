"""
火车票API核心模块单元测试
测试 train_api.py 中的 TrainAPI 类
"""

import unittest
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 切换到项目根目录
root_dir = Path(__file__).parent.parent
os.chdir(root_dir)

# 添加项目根目录到Python路径
sys.path.insert(0, str(root_dir))

from core.train_api import train_api


class TestTrainAPI(unittest.TestCase):
    """测试火车票API核心类"""

    def setUp(self):
        """测试前的准备工作"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 生成一个未来7天内的有效日期
        self.valid_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    def tearDown(self):
        """测试后的清理工作"""
        self.loop.close()

    def run_async(self, coro):
        """运行异步函数"""
        return self.loop.run_until_complete(coro)

    # ============ query_trains 方法测试 ============

    def test_query_trains_normal(self):
        """测试正常查询列车"""
        try:
            result = self.run_async(
                train_api.query_trains(
                    departure_station="北京",
                    arrival_station="上海",
                    date=self.valid_date,
                )
            )

            self.assertIsInstance(result, dict)
            self.assertIn("result", result)
            print("✅ test_query_trains_normal 通过")
        except Exception as e:
            # 如果API密钥未配置，跳过测试
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: API密钥未配置")
            else:
                raise

    def test_query_trains_with_filter(self):
        """测试带筛选条件的列车查询"""
        try:
            result = self.run_async(
                train_api.query_trains(
                    departure_station="北京",
                    arrival_station="上海",
                    date=self.valid_date,
                    filter="G",  # 只查高铁
                )
            )

            self.assertIsInstance(result, dict)
            self.assertIn("result", result)
            print("✅ test_query_trains_with_filter 通过")
        except Exception as e:
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: API密钥未配置")
            else:
                raise

    def test_query_trains_invalid_date_format(self):
        """测试无效日期格式"""
        with self.assertRaises(ValueError) as context:
            self.run_async(
                train_api.query_trains(
                    departure_station="北京",
                    arrival_station="上海",
                    date="2025/02/25",  # 错误的格式
                )
            )

        self.assertIn("日期格式错误", str(context.exception))
        print("✅ test_query_trains_invalid_date_format 通过")

    def test_query_trains_past_date(self):
        """测试过去的日期"""
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        with self.assertRaises(ValueError) as context:
            self.run_async(
                train_api.query_trains(
                    departure_station="北京", arrival_station="上海", date=past_date
                )
            )

        self.assertIn("不能早于今天", str(context.exception))
        print("✅ test_query_trains_past_date 通过")

    def test_query_trains_future_too_far(self):
        """测试超过15天的日期"""
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        with self.assertRaises(ValueError) as context:
            self.run_async(
                train_api.query_trains(
                    departure_station="北京", arrival_station="上海", date=future_date
                )
            )

        self.assertIn("只能查询15天内", str(context.exception))
        print("✅ test_query_trains_future_too_far 通过")

    def test_query_trains_invalid_filter(self):
        """测试无效的车次筛选"""
        with self.assertRaises(ValueError) as context:
            self.run_async(
                train_api.query_trains(
                    departure_station="北京",
                    arrival_station="上海",
                    date=self.valid_date,
                    filter="X",  # 无效筛选
                )
            )

        self.assertIn("无效的车次筛选条件", str(context.exception))
        print("✅ test_query_trains_invalid_filter 通过")

    def test_query_trains_invalid_time_range(self):
        """测试无效的时间段"""
        with self.assertRaises(ValueError) as context:
            self.run_async(
                train_api.query_trains(
                    departure_station="北京",
                    arrival_station="上海",
                    date=self.valid_date,
                    departure_time_range="中午",  # 无效时间段
                )
            )

        self.assertIn("无效的时间段", str(context.exception))
        print("✅ test_query_trains_invalid_time_range 通过")

    # ============ query_trains_simple 方法测试 ============

    def test_query_trains_simple_normal(self):
        """测试简洁格式查询"""
        try:
            result = self.run_async(
                train_api.query_trains_simple(
                    departure="北京", arrival="上海", date=self.valid_date
                )
            )

            self.assertIsInstance(result, str)
            self.assertIn("北京", result)
            self.assertIn("上海", result)
            print("✅ test_query_trains_simple_normal 通过")
        except Exception as e:
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: API密钥未配置")
            else:
                raise

    def test_query_trains_simple_with_filter(self):
        """测试带筛选的简洁格式查询"""
        try:
            result = self.run_async(
                train_api.query_trains_simple(
                    departure="北京", arrival="上海", date=self.valid_date, filter="G"
                )
            )

            self.assertIsInstance(result, str)
            print("✅ test_query_trains_simple_with_filter 通过")
        except Exception as e:
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: API密钥未配置")
            else:
                raise

    # ============ compare_routes 方法测试 ============

    def test_compare_routes_normal(self):
        """测试路线对比"""
        try:
            routes = [
                {"departure": "北京", "arrival": "上海"},
                {"departure": "北京", "arrival": "广州"},
            ]

            result = self.run_async(
                train_api.compare_routes(routes=routes, date=self.valid_date)
            )

            self.assertIsInstance(result, str)
            self.assertIn("多路线列车对比", result)
            print("✅ test_compare_routes_normal 通过")
        except Exception as e:
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: API密钥未配置")
            else:
                raise

    def test_compare_routes_exceed_limit(self):
        """测试超过5条路线"""
        routes = [
            {"departure": "北京", "arrival": "上海"},
            {"departure": "北京", "arrival": "广州"},
            {"departure": "北京", "arrival": "深圳"},
            {"departure": "北京", "arrival": "杭州"},
            {"departure": "北京", "arrival": "南京"},
            {"departure": "北京", "arrival": "武汉"},  # 第6条
        ]

        with self.assertRaises(ValueError) as context:
            self.run_async(
                train_api.compare_routes(routes=routes, date=self.valid_date)
            )

        self.assertIn("最多支持同时对比5个路线", str(context.exception))
        print("✅ test_compare_routes_exceed_limit 通过")

    def test_compare_routes_empty(self):
        """测试空路线列表"""
        with self.assertRaises(Exception):
            self.run_async(train_api.compare_routes(routes=[], date=self.valid_date))
        print("✅ test_compare_routes_empty 通过")

    # ============ 常量测试 ============

    def test_constants(self):
        """测试常量定义"""
        self.assertIsInstance(train_api.TRAIN_FILTERS, dict)
        self.assertIsInstance(train_api.TIME_RANGES, dict)
        self.assertIn("G", train_api.TRAIN_FILTERS)
        self.assertIn("D", train_api.TRAIN_FILTERS)
        self.assertIn("上午", train_api.TIME_RANGES)
        print("✅ test_constants 通过")


if __name__ == "__main__":
    unittest.main()
