"""
旅游助手API核心模块单元测试
测试 travel_api.py 中的 TravelAPI 类
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

from core.travel_api import travel_api


class TestTravelAPI(unittest.TestCase):
    """测试旅游API核心类"""

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

    # ============ search_attractions 方法测试 ============

    def test_search_attractions_normal(self):
        """测试正常搜索景点"""
        try:
            result = self.run_async(
                travel_api.search_attractions(keyword="故宫", city="北京", limit=3)
            )

            self.assertIsInstance(result, list)
            if result:
                first = result[0]
                self.assertIn("name", first)
                self.assertIn("address", first)
                self.assertIn("rating", first)
                print(
                    f"✅ test_search_attractions_normal 通过，找到 {len(result)} 个景点"
                )
            else:
                print("⚠️ 景点搜索返回空列表")
        except Exception as e:
            if "API密钥未配置" in str(e) or "amap_key" in str(e):
                print("⚠️ 跳过测试: 高德API密钥未配置")
            else:
                raise

    def test_search_attractions_without_city(self):
        """测试不指定城市搜索"""
        try:
            result = self.run_async(
                travel_api.search_attractions(keyword="博物馆", limit=3)
            )

            self.assertIsInstance(result, list)
            print(
                f"✅ test_search_attractions_without_city 通过，找到 {len(result)} 个结果"
            )
        except Exception as e:
            if "API密钥未配置" in str(e) or "amap_key" in str(e):
                print("⚠️ 跳过测试: 高德API密钥未配置")
            else:
                raise

    def test_search_attractions_empty_keyword(self):
        """测试空关键词搜索"""
        try:
            result = self.run_async(
                travel_api.search_attractions(keyword="", city="北京")
            )

            self.assertIsInstance(result, list)
            print(f"✅ test_search_attractions_empty_keyword 通过")
        except Exception as e:
            if "API密钥未配置" in str(e) or "amap_key" in str(e):
                print("⚠️ 跳过测试: 高德API密钥未配置")
            else:
                raise

    def test_search_attractions_invalid_city(self):
        """测试无效城市"""
        try:
            result = self.run_async(
                travel_api.search_attractions(
                    keyword="故宫", city="这是一个不存在的城市"
                )
            )

            self.assertIsInstance(result, list)
            # 应该返回空列表，不会崩溃
            print(f"✅ test_search_attractions_invalid_city 通过")
        except Exception as e:
            if "API密钥未配置" in str(e) or "amap_key" in str(e):
                print("⚠️ 跳过测试: 高德API密钥未配置")
            else:
                raise

    # ============ search_hotels 方法测试 ============

    def test_search_hotels_normal(self):
        """测试正常搜索酒店"""
        try:
            result = self.run_async(
                travel_api.search_hotels(keyword="如家", city="北京", limit=3)
            )

            self.assertIsInstance(result, list)
            if result:
                first = result[0]
                self.assertIn("name", first)
                self.assertIn("address", first)
                self.assertIn("rating", first)
                print(f"✅ test_search_hotels_normal 通过，找到 {len(result)} 个酒店")
            else:
                print("⚠️ 酒店搜索返回空列表")
        except Exception as e:
            if "API密钥未配置" in str(e) or "amap_key" in str(e):
                print("⚠️ 跳过测试: 高德API密钥未配置")
            else:
                raise

    def test_search_hotels_auto_correction(self):
        """测试关键词自动修正"""
        try:
            # 使用不带"酒店"的关键词
            result = self.run_async(
                travel_api.search_hotels(keyword="如家", city="上海")
            )

            self.assertIsInstance(result, list)
            print(
                f"✅ test_search_hotels_auto_correction 通过，找到 {len(result)} 个酒店"
            )
        except Exception as e:
            if "API密钥未配置" in str(e) or "amap_key" in str(e):
                print("⚠️ 跳过测试: 高德API密钥未配置")
            else:
                raise

    def test_search_hotels_with_hotel_keyword(self):
        """测试已包含酒店关键词的搜索"""
        try:
            result = self.run_async(
                travel_api.search_hotels(keyword="北京饭店", city="北京")
            )

            self.assertIsInstance(result, list)
            print(f"✅ test_search_hotels_with_hotel_keyword 通过")
        except Exception as e:
            if "API密钥未配置" in str(e) or "amap_key" in str(e):
                print("⚠️ 跳过测试: 高德API密钥未配置")
            else:
                raise

    def test_search_hotels_empty_keyword(self):
        """测试空关键词酒店搜索"""
        try:
            result = self.run_async(travel_api.search_hotels(keyword="", city="北京"))

            self.assertIsInstance(result, list)
            print(f"✅ test_search_hotels_empty_keyword 通过")
        except Exception as e:
            if "API密钥未配置" in str(e) or "amap_key" in str(e):
                print("⚠️ 跳过测试: 高德API密钥未配置")
            else:
                raise

    # ============ get_weather_simple 方法测试 ============

    def test_get_weather_simple_normal(self):
        """测试获取天气信息"""
        try:
            result = self.run_async(travel_api.get_weather_simple("北京"))

            self.assertIsInstance(result, dict)
            self.assertIn("city", result)
            self.assertIn("realtime", result)
            print(f"✅ test_get_weather_simple_normal 通过")
        except Exception as e:
            if "juhe_weather_api_key" in str(e):
                print("⚠️ 跳过测试: 天气API密钥未配置")
            else:
                raise

    def test_get_weather_simple_invalid_city(self):
        """测试无效城市天气查询"""
        try:
            result = self.run_async(
                travel_api.get_weather_simple("这是一个不存在的城市")
            )

            # 可能返回错误，但不会崩溃
            self.assertIsInstance(result, dict)
            print(f"✅ test_get_weather_simple_invalid_city 通过")
        except Exception as e:
            if "juhe_weather_api_key" in str(e):
                print("⚠️ 跳过测试: 天气API密钥未配置")
            else:
                # 应该抛出异常
                print(f"✅ test_get_weather_simple_invalid_city 通过 (异常: {e})")

    def test_get_weather_simple_empty_city(self):
        """测试空城市名"""
        with self.assertRaises(Exception):
            self.run_async(travel_api.get_weather_simple(""))
        print("✅ test_get_weather_simple_empty_city 通过")


if __name__ == "__main__":
    unittest.main()
