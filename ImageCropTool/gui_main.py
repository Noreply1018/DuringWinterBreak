#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - GUI 启动脚本
"""

import os
import sys

# 设置 GDAL 环境变量，解决 DLL 加载问题
os.environ['USE_PATH_FOR_GDAL_PYTHON'] = 'YES'

# 如果是打包后的环境，将 application_path 添加到 PATH
if getattr(sys, 'frozen', False):
    # PyInstaller one-dir mode: sys.executable is the exe, dependencies are in shell or _internal
    # PyInstaller >= 6.0: dependencies are in _internal
    base_dir = os.path.dirname(sys.executable)
    if os.path.exists(os.path.join(base_dir, '_internal')):
         application_path = os.path.join(base_dir, '_internal')
    else:
         application_path = base_dir

    # Fallback to sys._MEIPASS if available (one-file mode)
    if hasattr(sys, '_MEIPASS'):
        application_path = sys._MEIPASS
        
    print(f"Setting up environment for frozen app at: {application_path}")
    
    os.environ['PATH'] = application_path + os.pathsep + os.environ['PATH']
    
    try:
        os.add_dll_directory(application_path)
    except AttributeError:
        pass # Python < 3.8

    # Also try to add the root of the executable just in case
    if application_path != base_dir:
        os.environ['PATH'] = base_dir + os.pathsep + os.environ['PATH']
        try:
            os.add_dll_directory(base_dir)
        except AttributeError:
            pass

    # Set GDAL_DATA and PROJ_LIB for frozen app
    gdal_data = os.path.join(application_path, 'gdal-data')
    if os.path.exists(gdal_data):
        os.environ['GDAL_DATA'] = gdal_data
        
    proj_data = os.path.join(application_path, 'proj-data')
    if os.path.exists(proj_data):
        os.environ['PROJ_LIB'] = proj_data
        os.environ['PROJ_DATA'] = proj_data

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from src.gui import main

if __name__ == "__main__":
    main()
