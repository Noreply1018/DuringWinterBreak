# 影像裁剪小工具 (Image Crop Tool)

基于 Python + GDAL 的遥感影像裁剪工具，支持按地理坐标或像素坐标进行矩形区域裁剪。

## 功能特性

- ✅ 支持多种栅格格式（GeoTIFF、JPEG、PNG等）
- ✅ 支持多波段影像
- ✅ 支持8位/16位数据类型
- ✅ 保留原始投影信息和元数据
- ✅ 图形化界面（GUI）
- ✅ 命令行接口 (CLI)
- ✅ 边界校验和异常处理
- ✅ 中文路径支持

## 快速开始

### 环境要求

- Python 3.8+
- GDAL

### 安装

推荐使用 `conda` 创建环境以确保 GDAL 正确安装：

```bash
conda create -n image_crop_tool python=3.11 -y
conda activate image_crop_tool
conda install gdal numpy tqdm -y
```

或者使用 `pip` 安装（如果您的系统已配置好 GDAL 库）：

```bash
pip install .
```

### 使用方法

#### 1. 图形化界面 (GUI)

运行以下命令启动 GUI：

```bash
python gui_main.py
```

在界面中选择输入影像、设置输出路径、选择裁剪模式（像素/地理坐标）并输入裁剪范围即可。

#### 2. 命令行 (CLI)

使用 `main.py` 进行批处理或命令行操作：

**基本用法：**

```bash
python main.py -i input.tif -o output.tif -b <bound1> <bound2> <bound3> <bound4> -t <type>
```

**示例 - 像素坐标裁剪：**
裁剪从 (100, 100) 开始，宽 500，高 500 的区域。
```bash
python main.py -i input.tif -o output_pixel.tif -b 100 100 500 500 -t pixel
```
*(参数顺序：x_off y_off x_size y_size)*

**示例 - 地理坐标裁剪：**
裁剪经度 116.0-117.0，纬度 39.0-40.0 的区域。
```bash
python main.py -i input.tif -o output_geo.tif -b 116.0 40.0 117.0 39.0 -t geo
```
*(参数顺序：min_x min_y max_x max_y)*

**查看帮助：**
```bash
python main.py --help
```

### 开发

项目结构遵循标准 Python 包布局：

```
ImageCropTool/
├── src/
│   └── image_crop_tool/    # 核心代码包
├── tests/                  # 测试代码
├── gui_main.py             # GUI 入口脚本
├── main.py                 # CLI 入口脚本
└── pyproject.toml          # 项目配置
```

运行测试：

```bash
python tests/test_crop.py
```

### 打包发布

本项目包含一个自动打包脚本，使用 `PyInstaller` 将程序打包为独立可执行文件（包含 GDAL 依赖）。

1. 确保已安装 `pyinstaller`：
   ```bash
   conda install pyinstaller -y
   ```

2. 运行打包脚本：
   ```bash
   python scripts/package_app.py
   ```

3. 打包结果位于 `build/ImageCropTool` 目录。该目录包含 `.exe` 文件及其所有依赖。
   
   > **注意**：发布时请分发整个 `ImageCropTool` 文件夹，而不仅仅是 `.exe` 文件。

## 许可证

MIT License
