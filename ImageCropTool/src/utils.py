#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - 工具函数模块

提供日志配置、路径处理、异常类定义等功能。
"""

import os
import sys
import logging
from typing import Tuple, Optional


# ============== 自定义异常类 ==============

class ImageCropError(Exception):
    """影像裁剪工具基础异常类"""
    pass


class FileNotFoundError(ImageCropError):
    """文件未找到异常"""
    pass


class InvalidBoundsError(ImageCropError):
    """无效裁剪范围异常"""
    pass


class CoordinateTransformError(ImageCropError):
    """坐标转换异常"""
    pass


class GDALError(ImageCropError):
    """GDAL操作异常"""
    pass


# ============== 日志配置 ==============

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        level: 日志级别
        log_file: 可选的日志文件路径
    
    Returns:
        配置好的Logger对象
    """
    logger = logging.getLogger('image_crop_tool')
    logger.setLevel(level)
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 默认日志器
logger = setup_logging()


# ============== 路径处理 ==============

def normalize_path(path: str) -> str:
    """
    规范化路径，处理中文路径问题
    
    Args:
        path: 输入路径
    
    Returns:
        规范化后的绝对路径
    """
    # 转换为绝对路径
    abs_path = os.path.abspath(path)
    # 规范化路径分隔符
    normalized = os.path.normpath(abs_path)
    return normalized


def ensure_dir(path: str) -> None:
    """
    确保目录存在，不存在则创建
    
    Args:
        path: 目录路径
    """
    dir_path = os.path.dirname(path) if os.path.splitext(path)[1] else path
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"创建目录: {dir_path}")


def validate_file_exists(path: str) -> None:
    """
    验证文件是否存在
    
    Args:
        path: 文件路径
    
    Raises:
        FileNotFoundError: 文件不存在时抛出
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在: {path}")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"路径不是文件: {path}")


# ============== 边界验证 ==============

def validate_pixel_bounds(
    bounds: Tuple[int, int, int, int],
    img_width: int,
    img_height: int
) -> Tuple[int, int, int, int]:
    """
    验证并校正像素坐标边界
    
    Args:
        bounds: (x_off, y_off, x_size, y_size) 像素坐标边界
        img_width: 影像宽度
        img_height: 影像高度
    
    Returns:
        校正后的边界 (x_off, y_off, x_size, y_size)
    
    Raises:
        InvalidBoundsError: 边界无效时抛出
    """
    x_off, y_off, x_size, y_size = bounds
    
    # 检查起始位置
    if x_off < 0 or y_off < 0:
        raise InvalidBoundsError(f"起始位置不能为负: ({x_off}, {y_off})")
    
    if x_off >= img_width or y_off >= img_height:
        raise InvalidBoundsError(
            f"起始位置超出影像范围: ({x_off}, {y_off}), "
            f"影像大小: ({img_width}, {img_height})"
        )
    
    # 检查尺寸
    if x_size <= 0 or y_size <= 0:
        raise InvalidBoundsError(f"裁剪尺寸必须为正: ({x_size}, {y_size})")
    
    # 校正超出边界的尺寸
    if x_off + x_size > img_width:
        x_size = img_width - x_off
        logger.warning(f"X方向尺寸超出边界，已校正为: {x_size}")
    
    if y_off + y_size > img_height:
        y_size = img_height - y_off
        logger.warning(f"Y方向尺寸超出边界，已校正为: {y_size}")
    
    return (x_off, y_off, x_size, y_size)


# ============== GDAL 配置 ==============

def configure_gdal() -> None:
    """
    配置GDAL环境，静默警告，支持中文路径
    """
    try:
        from osgeo import gdal
        
        # 静默GDAL警告
        gdal.UseExceptions()
        gdal.PushErrorHandler('CPLQuietErrorHandler')
        
        # 配置中文路径支持
        gdal.SetConfigOption('GDAL_FILENAME_IS_UTF8', 'YES')
        gdal.SetConfigOption('SHAPE_ENCODING', 'UTF-8')
        
        logger.debug("GDAL配置完成")
    except ImportError:
        raise GDALError("无法导入GDAL库，请确保已正确安装")


# 模块加载时自动配置GDAL
try:
    configure_gdal()
except Exception as e:
    logger.warning(f"GDAL配置失败: {e}")
