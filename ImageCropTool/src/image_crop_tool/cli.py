#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - 命令行接口模块

提供命令行参数解析和主程序入口。
"""

import argparse
import sys
from typing import List, Optional

from .utils import logger, setup_logging, ImageCropError
from .crop_core import crop_raster
from .image_io import open_raster, get_raster_info, close_raster


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    解析命令行参数
    
    Args:
        args: 命令行参数列表，默认使用sys.argv
    
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        prog='image_crop_tool',
        description='影像裁剪小工具 - 基于GDAL的遥感影像裁剪工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  按像素坐标裁剪:
    python main.py -i input.tif -o output.tif -b 100 100 500 500 -t pixel
    
  按地理坐标裁剪:
    python main.py -i input.tif -o output.tif -b 116.0 40.0 117.0 39.0 -t geo
    
  查看影像信息:
    python main.py -i input.tif --info
'''
    )
    
    # 必需参数
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='输入影像路径'
    )
    
    # 可选参数
    parser.add_argument(
        '-o', '--output',
        help='输出影像路径（裁剪时必需）'
    )
    
    parser.add_argument(
        '-b', '--bounds',
        nargs=4,
        type=float,
        metavar=('B1', 'B2', 'B3', 'B4'),
        help='裁剪范围。pixel模式: x_off y_off x_size y_size; geo模式: min_x min_y max_x max_y'
    )
    
    parser.add_argument(
        '-t', '--type',
        choices=['pixel', 'geo'],
        default='pixel',
        help='坐标类型: pixel(像素坐标) 或 geo(地理坐标)，默认pixel'
    )
    
    parser.add_argument(
        '-f', '--format',
        default='GTiff',
        help='输出格式，默认GTiff。支持: GTiff, JPEG, PNG等'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='仅显示输入影像信息，不进行裁剪'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细信息'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='静默模式，只显示错误'
    )
    
    parsed = parser.parse_args(args)
    
    # 验证参数
    if not parsed.info:
        if not parsed.output:
            parser.error("裁剪模式需要指定输出路径 (-o/--output)")
        if not parsed.bounds:
            parser.error("裁剪模式需要指定裁剪范围 (-b/--bounds)")
    
    return parsed


def show_raster_info(input_path: str) -> None:
    """
    显示影像信息
    
    Args:
        input_path: 输入影像路径
    """
    ds = None
    try:
        ds = open_raster(input_path)
        info = get_raster_info(ds)
        gt = ds.GetGeoTransform()
        
        print("\n" + "=" * 50)
        print("影像信息")
        print("=" * 50)
        print(f"文件路径: {input_path}")
        print(f"驱动格式: {info['driver']}")
        print(f"影像尺寸: {info['width']} x {info['height']} 像素")
        print(f"波段数量: {info['bands']}")
        print(f"数据类型: {info['dtype_name']}")
        print(f"NoData值: {info['nodata']}")
        print()
        print("地理变换参数:")
        print(f"  左上角X坐标: {gt[0]}")
        print(f"  像素宽度:    {gt[1]}")
        print(f"  X方向旋转:   {gt[2]}")
        print(f"  左上角Y坐标: {gt[3]}")
        print(f"  Y方向旋转:   {gt[4]}")
        print(f"  像素高度:    {gt[5]}")
        print()
        
        # 计算影像范围
        min_x = gt[0]
        max_y = gt[3]
        max_x = gt[0] + info['width'] * gt[1]
        min_y = gt[3] + info['height'] * gt[5]
        
        print("影像地理范围:")
        print(f"  西边界 (min_x): {min_x}")
        print(f"  东边界 (max_x): {max_x}")
        print(f"  南边界 (min_y): {min_y}")
        print(f"  北边界 (max_y): {max_y}")
        
        if info['projection']:
            print()
            print(f"投影信息: {info['projection'][:100]}...")
        
        print("=" * 50 + "\n")
        
    finally:
        if ds:
            close_raster(ds)


def main(args: Optional[List[str]] = None) -> int:
    """
    主程序入口
    
    Args:
        args: 命令行参数列表
    
    Returns:
        退出码：0表示成功，非0表示失败
    """
    try:
        # 解析参数
        parsed = parse_args(args)
        
        # 配置日志级别
        import logging
        if parsed.quiet:
            setup_logging(logging.ERROR)
        elif parsed.verbose:
            setup_logging(logging.DEBUG)
        else:
            setup_logging(logging.INFO)
        
        # 显示信息模式
        if parsed.info:
            show_raster_info(parsed.input)
            return 0
        
        # 裁剪模式
        logger.info("开始裁剪影像...")
        logger.info(f"输入: {parsed.input}")
        logger.info(f"输出: {parsed.output}")
        logger.info(f"范围: {parsed.bounds}")
        logger.info(f"坐标类型: {parsed.type}")
        
        success = crop_raster(
            input_path=parsed.input,
            output_path=parsed.output,
            bounds=tuple(parsed.bounds),
            coord_type=parsed.type,
            output_format=parsed.format
        )
        
        if success:
            logger.info("裁剪完成！")
            return 0
        else:
            logger.error("裁剪失败")
            return 1
    
    except ImageCropError as e:
        logger.error(f"裁剪错误: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("用户中断")
        return 130
    except Exception as e:
        logger.error(f"未知错误: {e}")
        if parsed.verbose if 'parsed' in dir() else False:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
