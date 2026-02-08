# 影像裁剪小工具

基于 Python + GDAL 的遥感影像裁剪工具，支持按地理坐标或像素坐标进行矩形区域裁剪。

## 功能特性

- ✅ 支持多种栅格格式（GeoTIFF、JPEG、PNG等）
- ✅ 支持多波段影像
- ✅ 支持8位/16位数据类型
- ✅ 保留原始投影信息和元数据
- ✅ 图形化界面（GUI）
- ✅ 命令行接口
- ✅ 边界校验和异常处理
- ✅ 中文路径支持

## 快速开始

### 环境要求

- Python 3.8+
- Anaconda/Miniconda
- GDAL

### 安装

```bash
D:\Softwares\Anaconda\Scripts\conda.exe create -n gdal_env python=3.11 -y
D:\Softwares\Anaconda\Scripts\conda.exe install -n gdal_env gdal numpy tqdm -y
```

### 使用

```powershell
cd d:\Desktop\寒假做五个项目\影像裁剪小工具

# GUI 界面
D:\Softwares\Anaconda\envs\gdal_env\python.exe gui_main.py

# 命令行
D:\Softwares\Anaconda\envs\gdal_env\python.exe main.py -i input.tif -o output.tif -b 100 100 500 500 -t pixel
```

### 打包成 exe

双击运行 `packaging\build_exe.bat`，输出在 `dist\影像裁剪工具\`。

## 许可证

MIT License
