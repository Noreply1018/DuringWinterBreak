#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - 源代码包

Image Cropping Tool based on GDAL

提供基于GDAL的遥感影像裁剪功能，支持像素坐标和地理坐标两种裁剪方式。

Modules:
    - utils: 工具函数（日志、路径、异常类）
    - image_io: 影像读写模块
    - coord_transform: 坐标转换模块
    - crop_core: 核心裁剪模块
    - cli: 命令行接口

Example:
    # 命令行使用
    python main.py -i input.tif -o output.tif -b 100 100 500 500 -t pixel
    
    # Python代码调用
    from src.crop_core import crop_raster
    crop_raster('input.tif', 'output.tif', (100, 100, 500, 500), 'pixel')
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# 导出核心功能
from .utils import (
    ImageCropError,
    FileNotFoundError,
    InvalidBoundsError,
    CoordinateTransformError,
    GDALError,
    setup_logging,
    logger
)

from .crop_core import (
    crop_raster,
    crop_by_pixel,
    crop_by_geo
)

from .cli import main

__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    # 异常类
    'ImageCropError',
    'FileNotFoundError', 
    'InvalidBoundsError',
    'CoordinateTransformError',
    'GDALError',
    # 核心功能
    'crop_raster',
    'crop_by_pixel',
    'crop_by_geo',
    # 工具
    'setup_logging',
    'logger',
    'main',
]
