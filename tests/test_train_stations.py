"""
车站数据处理核心模块单元测试
测试 train_stations.py 中的 TrainStations 类
"""

import unittest
import sys
import os
from pathlib import Path

# 切换到项目根目录
root_dir = Path(__file__).parent.parent
os.chdir(root_dir)

# 添加项目根目录到Python路径
sys.path.insert(0, str(root_dir))

from core.train_stations import train_stations


class TestTrainStations(unittest.TestCase):
    """测试车站数据处理核心类"""

    def setUp(self):
        """测试前的准备工作"""
        # 确保车站数据已加载
        self.stations = train_stations.get_all_stations()

    def test_load_stations(self):
        """测试车站数据加载"""
        self.assertIsInstance(self.stations, dict)
        print(f"✅ 成功加载 {len(self.stations)} 个车站")

    def test_get_all_stations(self):
        """测试获取所有车站"""
        all_stations = train_stations.get_all_stations()
        self.assertIsInstance(all_stations, dict)
        self.assertEqual(len(all_stations), len(self.stations))
        print("✅ test_get_all_stations 通过")

    def test_get_station_by_name_exists(self):
        """测试查询存在的车站"""
        # 查找第一个存在的车站
        if self.stations:
            first_name = list(self.stations.keys())[0]
            station = train_stations.get_station_by_name(first_name)

            self.assertIsNotNone(station)
            self.assertIsInstance(station, dict)
            self.assertIn("station_code", station)
            self.assertIn("station_name", station)
            self.assertIn("station_city", station)
            print(f"✅ test_get_station_by_name_exists 通过: {first_name}")
        else:
            print("⚠️ 跳过: 无车站数据")

    def test_get_station_by_name_not_exists(self):
        """测试查询不存在的车站"""
        station = train_stations.get_station_by_name("这是一个不存在的车站")
        self.assertIsNone(station)
        print("✅ test_get_station_by_name_not_exists 通过")

    def test_search_stations_by_name(self):
        """测试按名称搜索"""
        if self.stations:
            # 用第一个车站名的前两个字搜索
            first_name = list(self.stations.keys())[0]
            keyword = first_name[:2] if len(first_name) >= 2 else first_name

            results = train_stations.search_stations(keyword, search_by="name")
            self.assertIsInstance(results, list)
            print(f"✅ 按名称搜索 '{keyword}' 找到 {len(results)} 个结果")
        else:
            print("⚠️ 跳过: 无车站数据")

    def test_search_stations_by_code(self):
        """测试按编码搜索"""
        if self.stations:
            # 找第一个有编码的车站
            for info in self.stations.values():
                code = info.get("station_code", "")
                if code:
                    results = train_stations.search_stations(code[:2], search_by="code")
                    self.assertIsInstance(results, list)
                    print(f"✅ 按编码搜索 '{code[:2]}' 找到 {len(results)} 个结果")
                    break
            else:
                print("⚠️ 跳过: 无编码数据")
        else:
            print("⚠️ 跳过: 无车站数据")

    def test_search_stations_by_city(self):
        """测试按城市搜索"""
        if self.stations:
            # 找第一个有城市的车站
            cities = set()
            for info in self.stations.values():
                city = info.get("station_city", "")
                if city and city not in cities:
                    cities.add(city)
                    results = train_stations.search_stations(city, search_by="city")
                    self.assertIsInstance(results, list)
                    self.assertGreater(len(results), 0)
                    print(f"✅ 按城市搜索 '{city}' 找到 {len(results)} 个车站")
                    break
            else:
                print("⚠️ 跳过: 无城市数据")
        else:
            print("⚠️ 跳过: 无车站数据")

    def test_search_stations_by_pinyin(self):
        """测试按拼音搜索"""
        if self.stations:
            # 找第一个有拼音的车站
            for info in self.stations.values():
                pinyin = info.get("station_pinyin", "")
                if pinyin:
                    results = train_stations.search_stations(
                        pinyin[:3], search_by="pinyin"
                    )
                    self.assertIsInstance(results, list)
                    print(f"✅ 按拼音搜索 '{pinyin[:3]}' 找到 {len(results)} 个结果")
                    break
            else:
                print("⚠️ 跳过: 无拼音数据")
        else:
            print("⚠️ 跳过: 无车站数据")

    def test_search_stations_empty_keyword(self):
        """测试空关键词搜索"""
        results = train_stations.search_stations("", search_by="name")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(train_stations.get_all_stations()))
        print("✅ test_search_stations_empty_keyword 通过")

    def test_get_stations_by_city(self):
        """测试获取城市车站"""
        if self.stations:
            # 找第一个有城市的车站
            cities = set()
            for info in self.stations.values():
                city = info.get("station_city", "")
                if city and city not in cities:
                    cities.add(city)
                    results = train_stations.get_stations_by_city(city)
                    self.assertIsInstance(results, list)
                    self.assertGreater(len(results), 0)
                    print(f"✅ 获取城市 '{city}' 车站: {len(results)} 个")
                    break
            else:
                print("⚠️ 跳过: 无城市数据")
        else:
            print("⚠️ 跳过: 无车站数据")

    def test_format_station_info(self):
        """测试格式化单个车站信息"""
        if self.stations:
            first_name = list(self.stations.keys())[0]
            station = train_stations.get_station_by_name(first_name)

            formatted = train_stations.format_station_info(station)
            self.assertIsInstance(formatted, str)
            self.assertIn(first_name, formatted)
            self.assertIn("编码", formatted)
            print(f"✅ test_format_station_info 通过")
        else:
            print("⚠️ 跳过: 无车站数据")

    def test_format_station_list(self):
        """测试格式化车站列表"""
        if self.stations:
            # 获取前5个车站
            stations_list = list(self.stations.values())[:5]

            formatted = train_stations.format_station_list(stations_list)
            self.assertIsInstance(formatted, str)
            self.assertIn("共找到", formatted)
            print(f"✅ test_format_station_list 通过")
        else:
            print("⚠️ 跳过: 无车站数据")

    def test_format_station_list_empty(self):
        """测试格式化空列表"""
        formatted = train_stations.format_station_list([])
        self.assertEqual(formatted, "未找到匹配的车站")
        print("✅ test_format_station_list_empty 通过")


if __name__ == "__main__":
    unittest.main()
