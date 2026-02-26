"""
天气工具单元测试
测试 get_weather 和 get_weather_comparison 工具
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

from tools.weather_tool import get_weather, get_weather_comparison


class TestWeatherTool(unittest.TestCase):
    """测试天气工具类"""

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

    def test_get_weather_simple_format(self):
        """测试获取天气 - simple格式"""
        result = self.run_async(get_weather("北京", "simple"))

        # 验证返回的是字符串
        self.assertIsInstance(result, str)

        # 验证包含关键信息
        self.assertIn("北京", result)
        self.assertIn("温度", result)
        self.assertIn("天气", result)

        print("✅ test_get_weather_simple_format 通过")

    def test_get_weather_detailed_format(self):
        """测试获取天气 - detailed格式"""
        result = self.run_async(get_weather("上海", "detailed"))

        # 验证返回的是字典
        self.assertIsInstance(result, dict)

        # 验证包含必要字段
        self.assertIn("city", result)
        self.assertIn("realtime", result)
        self.assertIn("future", result)

        print("✅ test_get_weather_detailed_format 通过")

    def test_get_weather_invalid_city(self):
        """测试获取天气 - 无效城市"""
        with self.assertRaises(Exception) as context:
            self.run_async(get_weather("这是一个不存在的城市名字"))

        self.assertIn("失败", str(context.exception))
        print("✅ test_get_weather_invalid_city 通过")

    def test_get_weather_empty_city(self):
        """测试获取天气 - 空城市名"""
        with self.assertRaises(Exception):
            self.run_async(get_weather(""))
        print("✅ test_get_weather_empty_city 通过")

    def test_get_weather_comparison_two_cities(self):
        """测试对比两个城市的天气"""
        cities = ["北京", "上海"]
        result = self.run_async(get_weather_comparison(cities))

        self.assertIsInstance(result, str)
        self.assertIn("多城市天气对比", result)
        self.assertIn("北京", result)
        self.assertIn("上海", result)

        print("✅ test_get_weather_comparison_two_cities 通过")

    def test_get_weather_comparison_five_cities(self):
        """测试对比五个城市的天气（最大限制）"""
        cities = ["北京", "上海", "广州", "深圳", "杭州"]
        result = self.run_async(get_weather_comparison(cities))

        self.assertIsInstance(result, str)
        self.assertIn("多城市天气对比", result)

        print("✅ test_get_weather_comparison_five_cities 通过")

    def test_get_weather_comparison_exceed_limit(self):
        """测试超过5个城市的对比（应该抛出异常）"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "南京"]

        with self.assertRaises(ValueError) as context:
            self.run_async(get_weather_comparison(cities))

        self.assertIn("最多支持同时对比5个城市", str(context.exception))
        print("✅ test_get_weather_comparison_exceed_limit 通过")

    def test_get_weather_comparison_empty_list(self):
        """测试空城市列表"""
        with self.assertRaises(Exception):
            self.run_async(get_weather_comparison([]))
        print("✅ test_get_weather_comparison_empty_list 通过")


if __name__ == "__main__":
    unittest.main()
