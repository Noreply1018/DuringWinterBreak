#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - 测试数据生成脚本

生成多种格式、投影和类型的测试影像。
"""

import os
import sys
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from osgeo import gdal, osr


def create_image(
    path: str,
    width: int,
    height: int,
    bands: int = 3,
    dtype: int = gdal.GDT_Byte,
    format: str = 'GTiff',
    proj_type: str = 'WGS84'
):
    """创建测试影像"""
    driver = gdal.GetDriverByName(format)
    # Check if driver supports Create
    if not driver:
        print(f"Skipping {format}: Driver not found")
        return

    # Use MEM driver for creating the dataset first, then copying
    mem_driver = gdal.GetDriverByName('MEM')
    ds = mem_driver.Create('', width, height, bands, dtype)

    # 设置投影和地理变换
    srs = osr.SpatialReference()
    if proj_type == 'WGS84':
        srs.ImportFromEPSG(4326)
        gt = (116.0, 0.001, 0, 40.0, 0, -0.001)
    elif proj_type == 'UTM':
        srs.ImportFromEPSG(32650) # UTM Zone 50N
        gt = (400000, 30, 0, 4400000, 0, -30)
    else: # Pixel
        srs = None
        gt = (0, 1, 0, 0, 0, 1)

    if srs:
        ds.SetProjection(srs.ExportToWkt())
    ds.SetGeoTransform(gt)

    # 写入数据
    for b in range(1, bands + 1):
        band = ds.GetRasterBand(b)
        
        # Determine max value based on dtype
        max_val = 255
        if dtype == gdal.GDT_UInt16:
            max_val = 65535
        elif dtype == gdal.GDT_Float32:
            max_val = 1.0

        if dtype == gdal.GDT_Float32:
            data = np.random.rand(height, width).astype(np.float32)
        else:
            data = np.random.randint(0, max_val, (height, width))
            if dtype == gdal.GDT_Byte:
                data = data.astype(np.uint8)
            elif dtype == gdal.GDT_UInt16:
                data = data.astype(np.uint16)
        
        # draw grid
        if b == 1:
             grid_val = max_val
             data[::50, :] = grid_val
             data[:, ::50] = grid_val
        
        band.WriteArray(data)
    
    # Save to file
    driver.CreateCopy(path, ds)
    
    ds = None
    print(f"Generated: {os.path.basename(path)} ({width}x{height}, {format}, {proj_type})")


def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, 'data', 'input', 'diverse')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Generating diverse test images...")

    # 1. 标准 GeoTIFF (WGS84)
    create_image(
        os.path.join(output_dir, 'wgs84_rgb.tif'),
        500, 400, 3, gdal.GDT_Byte, 'GTiff', 'WGS84'
    )

    # 2. UTM 投影 GeoTIFF
    create_image(
        os.path.join(output_dir, 'utm_16bit.tif'),
        300, 300, 1, gdal.GDT_UInt16, 'GTiff', 'UTM'
    )

    # 3. 浮点型 GeoTIFF
    create_image(
        os.path.join(output_dir, 'float_dem.tif'),
        200, 200, 1, gdal.GDT_Float32, 'GTiff', 'WGS84'
    )

    # 4. JPEG (通常无地理坐标，或者通过world file/exif)
    create_image(
        os.path.join(output_dir, 'normal.jpg'),
        800, 600, 3, gdal.GDT_Byte, 'JPEG', 'Pixel'
    )

    # 5. PNG
    create_image(
        os.path.join(output_dir, 'map.png'),
        400, 400, 4, gdal.GDT_Byte, 'PNG', 'Pixel'
    )

    print("Done!")

if __name__ == '__main__':
    main()
