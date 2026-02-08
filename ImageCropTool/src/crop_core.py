#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - 核心裁剪模块

提供影像裁剪的核心功能实现。
"""

from typing import Tuple, Optional, Union, List
from osgeo import gdal

from .utils import (
    logger, validate_pixel_bounds, InvalidBoundsError, GDALError
)
from .image_io import (
    open_raster, get_raster_info, create_raster,
    read_band_data, write_band_data, close_raster
)
from .coord_transform import (
    get_geotransform, geo_bounds_to_pixel_bounds, calculate_crop_geotransform
)


def crop_by_pixel(
    input_path: str,
    output_path: str,
    x_off: int,
    y_off: int,
    x_size: int,
    y_size: int,
    output_format: str = 'GTiff'
) -> bool:
    """
    按像素坐标裁剪影像
    
    Args:
        input_path: 输入影像路径
        output_path: 输出影像路径
        x_off: X方向偏移（像素，左上角列号）
        y_off: Y方向偏移（像素，左上角行号）
        x_size: 裁剪宽度（像素）
        y_size: 裁剪高度（像素）
        output_format: 输出格式（默认GeoTIFF）
    
    Returns:
        是否成功
    
    Raises:
        InvalidBoundsError: 裁剪范围无效
        GDALError: GDAL操作失败
    """
    src_ds = None
    dst_ds = None
    
    try:
        # 打开源影像
        src_ds = open_raster(input_path)
        src_info = get_raster_info(src_ds)
        
        logger.info(f"源影像: {src_info['width']}x{src_info['height']}, "
                    f"{src_info['bands']}波段")
        
        # 验证并校正裁剪边界
        bounds = validate_pixel_bounds(
            (x_off, y_off, x_size, y_size),
            src_info['width'],
            src_info['height']
        )
        x_off, y_off, x_size, y_size = bounds
        
        logger.info(f"裁剪范围: 起点({x_off}, {y_off}), 尺寸({x_size}, {y_size})")
        
        # 获取源影像的地理变换参数
        src_gt = get_geotransform(src_ds)
        
        # 计算裁剪后的地理变换参数
        dst_gt = calculate_crop_geotransform(src_gt, x_off, y_off)
        
        # 创建目标影像
        dst_ds = create_raster(
            output_path=output_path,
            width=x_size,
            height=y_size,
            bands=src_info['bands'],
            dtype=src_info['dtype'],
            driver_name=output_format,
            geotransform=dst_gt,
            projection=src_info['projection'],
            nodata=src_info['nodata']
        )
        
        # 逐波段读写数据
        for band_idx in range(1, src_info['bands'] + 1):
            logger.debug(f"处理波段 {band_idx}/{src_info['bands']}")
            
            # 读取源数据
            data = read_band_data(src_ds, band_idx, x_off, y_off, x_size, y_size)
            
            # 写入目标数据
            write_band_data(dst_ds, band_idx, data)
        
        # 刷新缓存
        dst_ds.FlushCache()
        
        logger.info(f"裁剪完成: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"裁剪失败: {e}")
        raise
    
    finally:
        # 关闭数据集
        if src_ds:
            close_raster(src_ds)
        if dst_ds:
            close_raster(dst_ds)


def crop_by_geo(
    input_path: str,
    output_path: str,
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    output_format: str = 'GTiff'
) -> bool:
    """
    按地理坐标裁剪影像
    
    Args:
        input_path: 输入影像路径
        output_path: 输出影像路径
        min_x: 最小X坐标（西边界/左经度）
        min_y: 最小Y坐标（南边界/下纬度）
        max_x: 最大X坐标（东边界/右经度）
        max_y: 最大Y坐标（北边界/上纬度）
        output_format: 输出格式（默认GeoTIFF）
    
    Returns:
        是否成功
    
    Raises:
        InvalidBoundsError: 裁剪范围无效
        GDALError: GDAL操作失败
    """
    src_ds = None
    
    try:
        # 打开源影像获取信息
        src_ds = open_raster(input_path)
        src_info = get_raster_info(src_ds)
        src_gt = get_geotransform(src_ds)
        
        logger.info(f"地理坐标范围: ({min_x}, {min_y}) - ({max_x}, {max_y})")
        
        # 转换地理坐标到像素坐标
        x_off, y_off, x_size, y_size = geo_bounds_to_pixel_bounds(
            src_gt, min_x, min_y, max_x, max_y,
            src_info['width'], src_info['height']
        )
        
        # 关闭源数据集（crop_by_pixel会重新打开）
        close_raster(src_ds)
        src_ds = None
        
        # 调用像素坐标裁剪
        return crop_by_pixel(
            input_path, output_path,
            x_off, y_off, x_size, y_size,
            output_format
        )
    
    except Exception as e:
        logger.error(f"地理坐标裁剪失败: {e}")
        raise
    
    finally:
        if src_ds:
            close_raster(src_ds)


def crop_raster(
    input_path: str,
    output_path: str,
    bounds: Tuple[float, float, float, float],
    coord_type: str = 'pixel',
    output_format: str = 'GTiff'
) -> bool:
    """
    裁剪影像的统一接口
    
    Args:
        input_path: 输入影像路径
        output_path: 输出影像路径
        bounds: 裁剪范围
            - pixel模式: (x_off, y_off, x_size, y_size)
            - geo模式: (min_x, min_y, max_x, max_y)
        coord_type: 坐标类型，'pixel' 或 'geo'
        output_format: 输出格式
    
    Returns:
        是否成功
    """
    if coord_type.lower() == 'pixel':
        x_off, y_off, x_size, y_size = [int(b) for b in bounds]
        return crop_by_pixel(
            input_path, output_path,
            x_off, y_off, x_size, y_size,
            output_format
        )
    elif coord_type.lower() == 'geo':
        min_x, min_y, max_x, max_y = [float(b) for b in bounds]
        return crop_by_geo(
            input_path, output_path,
            min_x, min_y, max_x, max_y,
            output_format
        )
    else:
        raise ValueError(f"不支持的坐标类型: {coord_type}，请使用 'pixel' 或 'geo'")
