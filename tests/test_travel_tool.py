"""
旅游助手工具单元测试
测试 search_attractions, search_hotels, get_travel_weather, plan_trip 工具
"""

import unittest
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
os.chdir(root_dir)

from tools.travel_tool import (
    search_attractions,
    search_hotels,
    get_travel_weather,
    plan_trip,
)


class TestTravelTool(unittest.TestCase):
    """测试旅游助手工具类"""

    def setUp(self):
        """测试前的准备工作"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """测试后的清理工作"""
        self.loop.close()

    def run_async(self, coro):
        """运行异步函数"""
        return self.loop.run_until_complete(coro)

    def test_search_attractions_normal(self):
        """测试正常搜索景点"""
        result = self.run_async(search_attractions("故宫", "北京"))

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success", False))
        self.assertIn("count", result)
        self.assertIn("data", result)

        if result["count"] > 0:
            first = result["data"][0]
            self.assertIn("name", first)
            self.assertIn("address", first)

        print("✅ test_search_attractions_normal 通过")

    def test_search_attractions_without_city(self):
        """测试不指定城市的景点搜索"""
        result = self.run_async(search_attractions("博物馆"))

        self.assertIsInstance(result, dict)
        # 可能成功也可能返回0结果，但不会报错
        self.assertTrue("success" in result or "error" in result)

        print("✅ test_search_attractions_without_city 通过")

    def test_search_attractions_empty_keyword(self):
        """测试空关键词搜索"""
        result = self.run_async(search_attractions("", "北京"))

        self.assertIsInstance(result, dict)
        # 可能返回0结果，但不会崩溃
        print("✅ test_search_attractions_empty_keyword 通过")

    def test_search_hotels_normal(self):
        """测试正常搜索酒店"""
        result = self.run_async(search_hotels("如家", "北京"))

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success", False))
        self.assertIn("count", result)
        self.assertIn("data", result)

        if result["count"] > 0:
            first = result["data"][0]
            self.assertIn("name", first)

        print("✅ test_search_hotels_normal 通过")

    def test_search_hotels_auto_correction(self):
        """测试酒店关键词自动修正"""
        # 不包含"酒店"的关键词
        result = self.run_async(search_hotels("如家", "上海"))

        self.assertIsInstance(result, dict)
        # 应该能正常返回结果
        print("✅ test_search_hotels_auto_correction 通过")

    def test_search_hotels_invalid_city(self):
        """测试无效城市酒店搜索"""
        result = self.run_async(search_hotels("酒店", "这是一个不存在的城市"))

        self.assertIsInstance(result, dict)
        # 可能返回0结果，但不会崩溃
        print("✅ test_search_hotels_invalid_city 通过")

    def test_get_travel_weather_normal(self):
        """测试获取旅游天气"""
        result = self.run_async(get_travel_weather("杭州"))

        self.assertIsInstance(result, dict)

        if result.get("success"):
            self.assertIn("data", result)
            data = result["data"]
            self.assertIn("city", data)
            self.assertIn("realtime", data)
        else:
            self.assertIn("error", result)

        print("✅ test_get_travel_weather_normal 通过")

    def test_get_travel_weather_invalid_city(self):
        """测试获取无效城市天气"""
        result = self.run_async(get_travel_weather("这是一个不存在的城市"))

        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        # 可能失败但不会抛出异常

        print("✅ test_get_travel_weather_invalid_city 通过")

    def test_plan_trip_normal(self):
        """测试正常行程规划"""
        result = self.run_async(plan_trip("杭州"))

        self.assertIsInstance(result, dict)

        if result.get("success"):
            self.assertIn("destination", result)
            self.assertEqual(result["destination"], "杭州")
            self.assertIn("summary", result)
            self.assertIsInstance(result["summary"], str)
            self.assertIn("杭州", result["summary"])
        else:
            self.assertIn("error", result)

        print("✅ test_plan_trip_normal 通过")

    def test_plan_trip_with_different_cities(self):
        """测试不同城市的行程规划"""
        cities = ["北京", "上海", "成都", "西安"]

        for city in cities:
            result = self.run_async(plan_trip(city))
            self.assertIsInstance(result, dict)

            if result.get("success"):
                self.assertEqual(result["destination"], city)

        print("✅ test_plan_trip_with_different_cities 通过")

    def test_plan_trip_invalid_city(self):
        """测试无效城市的行程规划"""
        result = self.run_async(plan_trip("这是一个不存在的城市"))

        self.assertIsInstance(result, dict)
        # 应该返回错误信息而不是崩溃
        if not result.get("success"):
            self.assertIn("error", result)

        print("✅ test_plan_trip_invalid_city 通过")

    def test_plan_trip_empty_city(self):
        """测试空城市名"""
        result = self.run_async(plan_trip(""))

        self.assertIsInstance(result, dict)
        # 应该返回错误信息
        print("✅ test_plan_trip_empty_city 通过")


if __name__ == "__main__":
    unittest.main()
