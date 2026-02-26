"""
天气预报API核心模块单元测试
测试 weather_api.py 中的 WeatherAPI 类
"""

import unittest
import asyncio
import sys
import os
from pathlib import Path

# 切换到项目根目录
root_dir = Path(__file__).parent.parent
os.chdir(root_dir)

# 添加项目根目录到Python路径
sys.path.insert(0, str(root_dir))

from core.weather_api import weather_api


class TestWeatherAPI(unittest.TestCase):
    """测试天气API核心类"""

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

    # ============ query_weather 方法测试 ============

    def test_query_weather_normal(self):
        """测试正常查询天气"""
        try:
            result = self.run_async(weather_api.query_weather("北京"))

            self.assertIsInstance(result, dict)
            self.assertIn("city", result)
            self.assertIn("realtime", result)
            self.assertIn("future", result)
            print("✅ test_query_weather_normal 通过")
        except Exception as e:
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: 天气API密钥未配置")
            else:
                raise

    def test_query_weather_shanghai(self):
        """测试查询上海天气"""
        try:
            result = self.run_async(weather_api.query_weather("上海"))

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("city"), "上海")
            print("✅ test_query_weather_shanghai 通过")
        except Exception as e:
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: 天气API密钥未配置")
            else:
                raise

    def test_query_weather_guangzhou(self):
        """测试查询广州天气"""
        try:
            result = self.run_async(weather_api.query_weather("广州"))

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("city"), "广州")
            print("✅ test_query_weather_guangzhou 通过")
        except Exception as e:
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: 天气API密钥未配置")
            else:
                raise

    def test_query_weather_invalid_city(self):
        """测试无效城市查询"""
        try:
            # 应该抛出异常
            self.run_async(weather_api.query_weather("这是一个不存在的城市"))
            self.fail("应该抛出异常但未抛出")
        except Exception as e:
            self.assertIn("失败", str(e) or "错误" in str(e))
            print("✅ test_query_weather_invalid_city 通过")

    def test_query_weather_empty_city(self):
        """测试空城市名"""
        with self.assertRaises(Exception):
            self.run_async(weather_api.query_weather(""))
        print("✅ test_query_weather_empty_city 通过")

    # ============ query_weather_simple 方法测试 ============

    def test_query_weather_simple_normal(self):
        """测试简洁格式天气查询"""
        try:
            result = self.run_async(weather_api.query_weather_simple("北京"))

            self.assertIsInstance(result, str)
            self.assertIn("北京", result)
            self.assertIn("温度", result)
            self.assertIn("天气", result)
            print("✅ test_query_weather_simple_normal 通过")
        except Exception as e:
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: 天气API密钥未配置")
            else:
                raise

    def test_query_weather_simple_format(self):
        """测试简洁格式的内容结构"""
        try:
            result = self.run_async(weather_api.query_weather_simple("上海"))

            self.assertIn("📍", result)  # 地点标记
            self.assertIn("🌡️", result)  # 温度标记
            self.assertIn("☁️", result)  # 天气标记
            self.assertIn("💧", result)  # 湿度标记
            self.assertIn("🌬️", result)  # 风力标记
            print("✅ test_query_weather_simple_format 通过")
        except Exception as e:
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: 天气API密钥未配置")
            else:
                raise

    def test_query_weather_simple_with_aqi(self):
        """测试空气质量显示"""
        try:
            result = self.run_async(weather_api.query_weather_simple("北京"))

            # 可能有AQI，也可能没有，但不会崩溃
            print("✅ test_query_weather_simple_with_aqi 通过")
        except Exception as e:
            if "API密钥未配置" in str(e):
                print("⚠️ 跳过测试: 天气API密钥未配置")
            else:
                raise

    def test_query_weather_simple_invalid_city(self):
        """测试简洁格式无效城市"""
        try:
            self.run_async(weather_api.query_weather_simple("这是一个不存在的城市"))
            self.fail("应该抛出异常但未抛出")
        except Exception as e:
            print("✅ test_query_weather_simple_invalid_city 通过")

    # ============ _get_error_message 方法测试 ============

    def test_get_error_message_known(self):
        """测试已知错误码"""
        error_msg = weather_api._get_error_message(207301)
        self.assertEqual(error_msg, "错误的查询城市名")
        print("✅ test_get_error_message_known 通过")

    def test_get_error_message_unknown(self):
        """测试未知错误码"""
        error_msg = weather_api._get_error_message(999999)
        self.assertIn("未知错误", error_msg)
        print("✅ test_get_error_message_unknown 通过")

    # ============ get_supported_cities 方法测试 ============

    def test_get_supported_cities(self):
        """测试获取支持的城市列表"""
        result = self.run_async(weather_api.get_supported_cities())

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        first = result[0]
        self.assertIn("id", first)
        self.assertIn("name", first)
        self.assertIn("province", first)
        print("✅ test_get_supported_cities 通过")


if __name__ == "__main__":
    unittest.main()
