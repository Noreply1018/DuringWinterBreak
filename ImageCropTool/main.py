#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - 程序入口

Usage:
    python main.py -i input.tif -o output.tif -b 100 100 500 500 -t pixel
    python main.py -i input.tif -o output.tif -b 116.0 40.0 117.0 39.0 -t geo
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli import main

if __name__ == "__main__":
    main()
