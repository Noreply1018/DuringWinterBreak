#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - 坐标转换模块

提供地理坐标与像素坐标的相互转换功能。
"""

from typing import Tuple
from osgeo import gdal

from .utils import logger, CoordinateTransformError


def get_geotransform(dataset: gdal.Dataset) -> Tuple[float, float, float, float, float, float]:
    """
    获取仿射变换参数
    
    GeoTransform 包含6个参数:
    [0] x_origin: 左上角X坐标
    [1] pixel_width: 像素宽度（X方向分辨率）
    [2] x_rotation: X方向旋转（通常为0）
    [3] y_origin: 左上角Y坐标
    [4] y_rotation: Y方向旋转（通常为0）
    [5] pixel_height: 像素高度（Y方向分辨率，通常为负值）
    
    Args:
        dataset: GDAL Dataset对象
    
    Returns:
        仿射变换参数元组
    """
    gt = dataset.GetGeoTransform()
    if gt == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        logger.warning("影像无地理坐标信息，使用默认变换参数")
    return gt


def geo_to_pixel(
    gt: Tuple[float, float, float, float, float, float],
    geo_x: float,
    geo_y: float
) -> Tuple[int, int]:
    """
    地理坐标转像素坐标
    
    Args:
        gt: 仿射变换参数
        geo_x: 地理X坐标（经度）
        geo_y: 地理Y坐标（纬度）
    
    Returns:
        (pixel_x, pixel_y) 像素坐标（列, 行）
    
    Raises:
        CoordinateTransformError: 转换失败
    """
    try:
        # 仿射变换逆运算
        # pixel_x = (geo_x - x_origin) / pixel_width
        # pixel_y = (geo_y - y_origin) / pixel_height
        
        x_origin, pixel_width, x_rotation, y_origin, y_rotation, pixel_height = gt
        
        # 处理旋转情况（通常为0）
        if x_rotation != 0 or y_rotation != 0:
            # 完整的仿射变换逆运算
            det = pixel_width * pixel_height - x_rotation * y_rotation
            if abs(det) < 1e-10:
                raise CoordinateTransformError("仿射变换矩阵奇异，无法求逆")
            
            pixel_x = (pixel_height * (geo_x - x_origin) - x_rotation * (geo_y - y_origin)) / det
            pixel_y = (pixel_width * (geo_y - y_origin) - y_rotation * (geo_x - x_origin)) / det
        else:
            # 简化计算（无旋转）
            pixel_x = (geo_x - x_origin) / pixel_width
            pixel_y = (geo_y - y_origin) / pixel_height
        
        # 取整（使用floor确保正确的像素位置）
        pixel_x = int(pixel_x)
        pixel_y = int(pixel_y)
        
        logger.debug(f"地理坐标 ({geo_x}, {geo_y}) -> 像素坐标 ({pixel_x}, {pixel_y})")
        
        return (pixel_x, pixel_y)
    
    except Exception as e:
        raise CoordinateTransformError(f"地理坐标转像素坐标失败: {e}")


def pixel_to_geo(
    gt: Tuple[float, float, float, float, float, float],
    pixel_x: int,
    pixel_y: int
) -> Tuple[float, float]:
    """
    像素坐标转地理坐标
    
    Args:
        gt: 仿射变换参数
        pixel_x: 像素X坐标（列）
        pixel_y: 像素Y坐标（行）
    
    Returns:
        (geo_x, geo_y) 地理坐标
    """
    x_origin, pixel_width, x_rotation, y_origin, y_rotation, pixel_height = gt
    
    # 仿射变换正运算
    geo_x = x_origin + pixel_x * pixel_width + pixel_y * x_rotation
    geo_y = y_origin + pixel_x * y_rotation + pixel_y * pixel_height
    
    logger.debug(f"像素坐标 ({pixel_x}, {pixel_y}) -> 地理坐标 ({geo_x}, {geo_y})")
    
    return (geo_x, geo_y)


def calculate_crop_geotransform(
    original_gt: Tuple[float, float, float, float, float, float],
    x_off: int,
    y_off: int
) -> Tuple[float, float, float, float, float, float]:
    """
    计算裁剪后影像的仿射变换参数
    
    Args:
        original_gt: 原始仿射变换参数
        x_off: X方向偏移（像素）
        y_off: Y方向偏移（像素）
    
    Returns:
        新的仿射变换参数
    """
    x_origin, pixel_width, x_rotation, y_origin, y_rotation, pixel_height = original_gt
    
    # 计算新的原点坐标
    new_x_origin = x_origin + x_off * pixel_width + y_off * x_rotation
    new_y_origin = y_origin + x_off * y_rotation + y_off * pixel_height
    
    new_gt = (new_x_origin, pixel_width, x_rotation,
              new_y_origin, y_rotation, pixel_height)
    
    logger.debug(f"新的仿射变换参数: {new_gt}")
    
    return new_gt


def geo_bounds_to_pixel_bounds(
    gt: Tuple[float, float, float, float, float, float],
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    img_width: int,
    img_height: int
) -> Tuple[int, int, int, int]:
    """
    地理坐标范围转像素坐标范围
    
    注意：对于北半球常见的投影，地理Y坐标向北增大，
    但像素Y坐标向下增大，因此需要注意min_y和max_y的对应关系。
    
    Args:
        gt: 仿射变换参数
        min_x: 最小X坐标（西边界）
        min_y: 最小Y坐标（南边界）
        max_x: 最大X坐标（东边界）
        max_y: 最大Y坐标（北边界）
        img_width: 影像宽度
        img_height: 影像高度
    
    Returns:
        (x_off, y_off, x_size, y_size) 像素范围
    """
    # 转换四个角点
    # 左上角（min_x, max_y）对应像素坐标的起始点
    ul_pixel_x, ul_pixel_y = geo_to_pixel(gt, min_x, max_y)
    # 右下角（max_x, min_y）
    lr_pixel_x, lr_pixel_y = geo_to_pixel(gt, max_x, min_y)
    
    # 确保顺序正确
    x_off = min(ul_pixel_x, lr_pixel_x)
    y_off = min(ul_pixel_y, lr_pixel_y)
    x_end = max(ul_pixel_x, lr_pixel_x)
    y_end = max(ul_pixel_y, lr_pixel_y)
    
    # 边界检查
    x_off = max(0, x_off)
    y_off = max(0, y_off)
    x_end = min(img_width, x_end)
    y_end = min(img_height, y_end)
    
    x_size = x_end - x_off
    y_size = y_end - y_off
    
    logger.debug(f"地理范围 ({min_x}, {min_y}, {max_x}, {max_y}) -> "
                 f"像素范围 ({x_off}, {y_off}, {x_size}, {y_size})")
    
    return (x_off, y_off, x_size, y_size)
