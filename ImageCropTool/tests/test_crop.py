#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - 功能测试脚本

创建测试影像并验证裁剪功能。
"""

import os
import sys
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from osgeo import gdal


def create_test_image(output_path: str, width: int = 500, height: int = 400) -> None:
    """创建测试影像"""
    driver = gdal.GetDriverByName('GTiff')
    
    # 创建3波段RGB影像
    ds = driver.Create(output_path, width, height, 3, gdal.GDT_Byte)
    
    # 设置地理变换参数（模拟北京附近区域）
    # 左上角: 116°E, 40°N, 分辨率约0.001度
    gt = (116.0, 0.001, 0, 40.0, 0, -0.001)
    ds.SetGeoTransform(gt)
    
    # 设置投影（WGS84）
    ds.SetProjection('GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]')
    
    # 创建渐变测试数据
    for band_idx in range(1, 4):
        band = ds.GetRasterBand(band_idx)
        
        # 生成渐变数据
        data = np.zeros((height, width), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                if band_idx == 1:  # R - 水平渐变
                    data[y, x] = int(x / width * 255)
                elif band_idx == 2:  # G - 垂直渐变
                    data[y, x] = int(y / height * 255)
                else:  # B - 对角渐变
                    data[y, x] = int((x + y) / (width + height) * 255)
        
        band.WriteArray(data)
    
    ds.FlushCache()
    ds = None
    print(f"Test image created: {output_path}")
    print(f"  Size: {width} x {height}")
    print(f"  Extent: 116.0E - {116.0 + width * 0.001}E, "
          f"{40.0 - height * 0.001}N - 40.0N")


def test_pixel_crop(input_path: str, output_path: str) -> bool:
    """测试像素坐标裁剪"""
    from src.crop_core import crop_by_pixel
    
    print("\nTesting pixel coordinate crop...")
    print(f"  Bounds: x_off=100, y_off=50, x_size=200, y_size=150")
    
    try:
        success = crop_by_pixel(
            input_path=input_path,
            output_path=output_path,
            x_off=100,
            y_off=50,
            x_size=200,
            y_size=150
        )
        
        # 验证结果
        ds = gdal.Open(output_path)
        if ds:
            print(f"  Output size: {ds.RasterXSize} x {ds.RasterYSize}")
            assert ds.RasterXSize == 200, "Width incorrect"
            assert ds.RasterYSize == 150, "Height incorrect"
            ds = None
            print("  [PASS] Pixel crop test passed!")
            return True
        
    except Exception as e:
        print(f"  [FAIL] Test failed: {e}")
        return False


def test_geo_crop(input_path: str, output_path: str) -> bool:
    """测试地理坐标裁剪"""
    from src.crop_core import crop_by_geo
    
    print("\nTesting geo coordinate crop...")
    print(f"  Bounds: 116.1E - 116.3E, 39.7N - 39.9N")
    
    try:
        success = crop_by_geo(
            input_path=input_path,
            output_path=output_path,
            min_x=116.1,
            min_y=39.7,
            max_x=116.3,
            max_y=39.9
        )
        
        # 验证结果
        ds = gdal.Open(output_path)
        if ds:
            print(f"  Output size: {ds.RasterXSize} x {ds.RasterYSize}")
            # 预期尺寸约200x200，允许1像素的浮点精度误差
            assert abs(ds.RasterXSize - 200) <= 1, f"Width incorrect: {ds.RasterXSize}"
            assert abs(ds.RasterYSize - 200) <= 1, f"Height incorrect: {ds.RasterYSize}"
            ds = None
            print("  [PASS] Geo crop test passed!")
            return True
    
    except Exception as e:
        print(f"  [FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试流程"""
    print("=" * 50)
    print("Image Crop Tool - Functional Test")
    print("=" * 50)
    
    # 设置路径
    base_dir = os.path.dirname(os.path.dirname(__file__))
    input_dir = os.path.join(base_dir, 'data', 'input')
    output_dir = os.path.join(base_dir, 'data', 'output')
    
    # 确保目录存在
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    test_input = os.path.join(input_dir, 'test.tif')
    pixel_output = os.path.join(output_dir, 'crop_pixel.tif')
    geo_output = os.path.join(output_dir, 'crop_geo.tif')
    
    # 创建测试影像
    print("\nCreating test image...")
    create_test_image(test_input)
    
    # 运行测试
    results = []
    results.append(test_pixel_crop(test_input, pixel_output))
    results.append(test_geo_crop(test_input, geo_output))
    
    # 总结
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    print(f"Pixel crop: {'PASS' if results[0] else 'FAIL'}")
    print(f"Geo crop:   {'PASS' if results[1] else 'FAIL'}")
    
    if all(results):
        print("\nAll tests passed!")
        return 0
    else:
        print("\nSome tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
