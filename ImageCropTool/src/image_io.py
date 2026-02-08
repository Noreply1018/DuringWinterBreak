#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - 影像读写模块

提供影像打开、读取、创建和保存功能。
"""

from typing import Dict, Any, Optional, Tuple, List
from osgeo import gdal, osr
import numpy as np

from .utils import (
    logger, normalize_path, validate_file_exists, ensure_dir,
    GDALError, FileNotFoundError
)


# 支持的数据类型映射
GDAL_DTYPE_MAP = {
    gdal.GDT_Byte: np.uint8,
    gdal.GDT_UInt16: np.uint16,
    gdal.GDT_Int16: np.int16,
    gdal.GDT_UInt32: np.uint32,
    gdal.GDT_Int32: np.int32,
    gdal.GDT_Float32: np.float32,
    gdal.GDT_Float64: np.float64,
}


def open_raster(file_path: str, mode: int = gdal.GA_ReadOnly) -> gdal.Dataset:
    """
    打开栅格文件
    
    Args:
        file_path: 影像文件路径
        mode: 打开模式，gdal.GA_ReadOnly 或 gdal.GA_Update
    
    Returns:
        GDAL Dataset对象
    
    Raises:
        FileNotFoundError: 文件不存在
        GDALError: GDAL打开失败
    """
    path = normalize_path(file_path)
    validate_file_exists(path)
    
    try:
        dataset = gdal.Open(path, mode)
        if dataset is None:
            raise GDALError(f"GDAL无法打开文件: {path}")
        logger.info(f"成功打开影像: {path}")
        return dataset
    except Exception as e:
        raise GDALError(f"打开影像失败: {e}")


def get_raster_info(dataset: gdal.Dataset) -> Dict[str, Any]:
    """
    获取影像元信息
    
    Args:
        dataset: GDAL Dataset对象
    
    Returns:
        包含影像信息的字典
    """
    info = {
        'width': dataset.RasterXSize,
        'height': dataset.RasterYSize,
        'bands': dataset.RasterCount,
        'driver': dataset.GetDriver().ShortName,
        'projection': dataset.GetProjection(),
        'geotransform': dataset.GetGeoTransform(),
        'dtype': None,
        'nodata': None,
    }
    
    # 获取第一个波段的数据类型和NoData值
    if dataset.RasterCount > 0:
        band = dataset.GetRasterBand(1)
        info['dtype'] = band.DataType
        info['dtype_name'] = gdal.GetDataTypeName(band.DataType)
        info['nodata'] = band.GetNoDataValue()
    
    logger.debug(f"影像信息: {info['width']}x{info['height']}, "
                 f"{info['bands']}波段, {info['dtype_name']}")
    
    return info


def create_raster(
    output_path: str,
    width: int,
    height: int,
    bands: int = 1,
    dtype: int = gdal.GDT_Byte,
    driver_name: str = 'GTiff',
    geotransform: Optional[Tuple] = None,
    projection: Optional[str] = None,
    nodata: Optional[float] = None,
    options: Optional[List[str]] = None
) -> gdal.Dataset:
    """
    创建新的栅格文件
    
    Args:
        output_path: 输出文件路径
        width: 影像宽度（像素）
        height: 影像高度（像素）
        bands: 波段数
        dtype: GDAL数据类型
        driver_name: 驱动名称（默认GeoTIFF）
        geotransform: 仿射变换参数
        projection: 投影信息
        nodata: NoData值
        options: 创建选项
    
    Returns:
        GDAL Dataset对象
    
    Raises:
        GDALError: 创建失败
    """
    path = normalize_path(output_path)
    ensure_dir(path)
    
    # 获取驱动
    driver = gdal.GetDriverByName(driver_name)
    if driver is None:
        raise GDALError(f"不支持的驱动类型: {driver_name}")
    
    # 创建选项
    if options is None:
        options = ['COMPRESS=LZW', 'BIGTIFF=IF_SAFER']
    
    try:
        # 创建数据集
        dataset = driver.Create(path, width, height, bands, dtype, options)
        if dataset is None:
            raise GDALError(f"无法创建文件: {path}")
        
        # 设置地理变换
        if geotransform:
            dataset.SetGeoTransform(geotransform)
        
        # 设置投影
        if projection:
            dataset.SetProjection(projection)
        
        # 设置NoData值
        if nodata is not None:
            for i in range(1, bands + 1):
                band = dataset.GetRasterBand(i)
                band.SetNoDataValue(nodata)
        
        logger.info(f"成功创建影像: {path}")
        return dataset
    
    except Exception as e:
        raise GDALError(f"创建影像失败: {e}")


def read_band_data(
    dataset: gdal.Dataset,
    band_index: int,
    x_off: int = 0,
    y_off: int = 0,
    x_size: Optional[int] = None,
    y_size: Optional[int] = None
) -> np.ndarray:
    """
    读取波段数据
    
    Args:
        dataset: GDAL Dataset对象
        band_index: 波段索引（从1开始）
        x_off: X方向偏移
        y_off: Y方向偏移
        x_size: 读取宽度（默认到边界）
        y_size: 读取高度（默认到边界）
    
    Returns:
        numpy数组
    """
    if x_size is None:
        x_size = dataset.RasterXSize - x_off
    if y_size is None:
        y_size = dataset.RasterYSize - y_off
    
    band = dataset.GetRasterBand(band_index)
    data = band.ReadAsArray(x_off, y_off, x_size, y_size)
    
    return data


def write_band_data(
    dataset: gdal.Dataset,
    band_index: int,
    data: np.ndarray,
    x_off: int = 0,
    y_off: int = 0
) -> None:
    """
    写入波段数据
    
    Args:
        dataset: GDAL Dataset对象
        band_index: 波段索引（从1开始）
        data: 要写入的numpy数组
        x_off: X方向偏移
        y_off: Y方向偏移
    """
    band = dataset.GetRasterBand(band_index)
    band.WriteArray(data, x_off, y_off)


def close_raster(dataset: gdal.Dataset) -> None:
    """
    安全关闭数据集
    
    Args:
        dataset: GDAL Dataset对象
    """
    if dataset:
        dataset.FlushCache()
        dataset = None
        logger.debug("数据集已关闭")


def copy_raster_metadata(
    src_dataset: gdal.Dataset,
    dst_dataset: gdal.Dataset,
    copy_nodata: bool = True
) -> None:
    """
    复制影像元数据
    
    Args:
        src_dataset: 源数据集
        dst_dataset: 目标数据集
        copy_nodata: 是否复制NoData值
    """
    # 复制投影
    dst_dataset.SetProjection(src_dataset.GetProjection())
    
    # 复制NoData
    if copy_nodata:
        for i in range(1, min(src_dataset.RasterCount, dst_dataset.RasterCount) + 1):
            src_band = src_dataset.GetRasterBand(i)
            dst_band = dst_dataset.GetRasterBand(i)
            nodata = src_band.GetNoDataValue()
            if nodata is not None:
                dst_band.SetNoDataValue(nodata)
    
    logger.debug("元数据复制完成")
