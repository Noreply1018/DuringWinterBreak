#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
影像裁剪小工具 - GUI 界面模块 (优化增强版)

基于 Tkinter 的可视化影像裁剪工具。
特点：
1. 现代化界面 (深色侧边栏，清晰布局)
2. 强大的图像浏览 (滚轮缩放，右键平移)
3. 实时 RGB 值显示
4. 精确的像素/地理坐标转换
"""

import os
import sys
import tkinter as limited_tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from osgeo import gdal
    GDAL_AVAILABLE = True
except ImportError:
    GDAL_AVAILABLE = False

# ===== 样式常量 =====
FONT_MAIN = ('Microsoft YaHei UI', 10)
FONT_BOLD = ('Microsoft YaHei UI', 10, 'bold')
FONT_TITLE = ('Microsoft YaHei UI', 12, 'bold')
FONT_MONO = ('Consolas', 10)

COLOR_BG_MAIN = '#f5f6f7'       # 主背景
COLOR_BG_SIDE = '#ffffff'       # 侧边栏背景
COLOR_ACCENT = '#0078d7'        # 强调色 (蓝色)
COLOR_ACCENT_HOVER = '#1084e3'
COLOR_TEXT_MAIN = '#333333'
COLOR_TEXT_SEC = '#666666'
COLOR_BORDER = '#e0e0e0'
COLOR_CANVAS = '#2b2b2b'        # 画布深色背景

# 缩放参数
ZOOM_FACTOR = 1.2               # 每次滚轮缩放倍数
MIN_ZOOM = 0.1
MAX_ZOOM = 50.0

# 裁剪框手柄参数
HANDLE_SIZE = 8                 # 手柄大小 (像素)

class ImageCropApp:
    """影像裁剪工具主应用"""
    
    def __init__(self, root):
        self.root = limited_tk.Tk() if root is None else root
        self.setup_window()
        
        # --- 状态与数据 ---
        self.current_file = None
        self.dataset = None
        self.original_image = None   # 原始 PIL Image (完整分辨率)
        self.photo_image = None      # 当前显示的 ImageTk 对象
        
        # 视口变换参数 (Image coords -> Canvas coords)
        # canvas_x = (image_x * scale) + offset_x
        # canvas_y = (image_y * scale) + offset_y
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        
        # 影像元数据
        self.img_width = 0
        self.img_height = 0
        self.img_bands = 0
        self.geo_transform = None
        self.projection = None
        self.has_geo = False
        self.inv_geo_transform = None
        
        # 交互状态
        self.dragging_pan = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        self.dragging_crop = False
        self.crop_start_x = 0
        self.crop_start_y = 0
        self.rect_id = None
        
        # 裁剪框拖拽/调整状态
        self.crop_drag_mode = None   # None, 'move', 'resize'
        self.active_handle = None    # 'nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w'
        self.drag_start_bounds = None
        
        # 裁剪结果 (Image coords)
        self.crop_bounds = None     # (x, y, w, h)
        
        # --- 初始化界面 ---
        self.setup_styles()
        self.create_widgets()
        self.bind_events()
        
        # 初始状态
        self.status_var.set("就绪 - 请打开影像文件")

    def setup_window(self):
        """窗口基础设置"""
        self.root.title("影像裁剪专家 v2.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        # 设置图标 (如果存在)
        # icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        # if os.path.exists(icon_path): self.root.iconbitmap(icon_path)

    def setup_styles(self):
        """配置现代化 TTK 样式"""
        style = ttk.Style()
        style.theme_use('clam')  # 使用 clam 主题作为基础，由我们自定义覆盖
        
        # 通用配置
        style.configure('.', background=COLOR_BG_MAIN, font=FONT_MAIN, foreground=COLOR_TEXT_MAIN)
        
        # 侧边栏框架
        style.configure('Side.TFrame', background=COLOR_BG_SIDE)
        style.configure('Side.TLabelframe', background=COLOR_BG_SIDE, relief='flat', borderwidth=1)
        style.configure('Side.TLabelframe.Label', background=COLOR_BG_SIDE, font=FONT_BOLD, foreground=COLOR_ACCENT)
        
        # 按钮样式
        style.configure('TButton', padding=6, borderwidth=0, background='#e1e1e1')
        style.map('TButton', background=[('active', '#d1d1d1')])
        
        # 强调按钮 (Accent)
        style.configure('Accent.TButton', background=COLOR_ACCENT, foreground='white', font=FONT_BOLD)
        style.map('Accent.TButton', background=[('active', COLOR_ACCENT_HOVER)])
        
        # 标签样式
        style.configure('Title.TLabel', font=FONT_TITLE, foreground=COLOR_TEXT_MAIN)
        style.configure('Info.TLabel', font=FONT_MAIN, foreground=COLOR_TEXT_SEC)
        style.configure('Value.TLabel', font=FONT_MONO, foreground='#000000')
        style.configure('RGB.TLabel', font=('Consolas', 11, 'bold'), foreground=COLOR_ACCENT, background='#e8f4fd', padding=5)

    def create_widgets(self):
        """构建界面布局"""
        # 主布局：左侧画布，右侧控制栏
        main_paned = ttk.PanedWindow(self.root, orient=limited_tk.HORIZONTAL)
        main_paned.pack(fill=limited_tk.BOTH, expand=True)
        
        # 1. 左侧：图像显示区
        self.canvas_frame = ttk.Frame(main_paned)
        main_paned.add(self.canvas_frame, weight=4)
        
        self.canvas = limited_tk.Canvas(
            self.canvas_frame, bg=COLOR_CANVAS, 
            highlightthickness=0, cursor='crosshair'
        )
        self.canvas.pack(fill=limited_tk.BOTH, expand=True)
        
        # 浮动提示：缩放级别
        self.zoom_label = limited_tk.Label(
            self.canvas, text="100%", bg='#333333', fg='white', 
            font=('Segoe UI', 9), padx=6, pady=2
        )
        
        # 浮动提示：裁剪尺寸
        self.dim_label = limited_tk.Label(
            self.canvas, text="", bg='#1a1a1a', fg='#00ff00', 
            font=('Consolas', 10, 'bold'), padx=4, pady=2
        )
        
        # 2. 右侧：控制面板
        side_panel = ttk.Frame(main_paned, style='Side.TFrame', width=320)
        main_paned.add(side_panel, weight=1)
        
        # 内部容器 (带内边距)
        ctrl_container = ttk.Frame(side_panel, style='Side.TFrame', padding=10)
        ctrl_container.pack(fill=limited_tk.BOTH, expand=True)
        
        # -- 标题区 --
        ttk.Label(ctrl_container, text="操作面板", style='Title.TLabel', background=COLOR_BG_SIDE).pack(anchor='w', pady=(0, 10))
        
        # -- 文件操作 --
        file_group = ttk.LabelFrame(ctrl_container, text=" 文件 ", style='Side.TLabelframe', padding=8)
        file_group.pack(fill=limited_tk.X, pady=(0, 10))
        
        btn_grid = ttk.Frame(file_group, style='Side.TFrame')
        btn_grid.pack(fill=limited_tk.X)
        ttk.Button(btn_grid, text="📂 打开影像", command=self.open_image).pack(side=limited_tk.LEFT, fill=limited_tk.X, expand=True, padx=(0, 5))
        ttk.Button(btn_grid, text="💾 保存裁剪", style='Accent.TButton', command=self.save_crop).pack(side=limited_tk.LEFT, fill=limited_tk.X, expand=True, padx=(5, 0))
        
        # -- 信息显示 --
        info_group = ttk.LabelFrame(ctrl_container, text=" 影像信息 ", style='Side.TLabelframe', padding=8)
        info_group.pack(fill=limited_tk.X, pady=(0, 10))
        
        self.info_labels = {}
        for key, name in [('file', '文件名'), ('size', '分辨率'), ('bands', '波段数'), ('proj', '投影')]:
            row = ttk.Frame(info_group, style='Side.TFrame')
            row.pack(fill=limited_tk.X, pady=2)
            ttk.Label(row, text=name, style='Info.TLabel', background=COLOR_BG_SIDE, width=6).pack(side=limited_tk.LEFT)
            lbl = ttk.Label(row, text="-", style='Value.TLabel', background=COLOR_BG_SIDE, wraplength=200)
            lbl.pack(side=limited_tk.RIGHT, expand=True, fill=limited_tk.X)
            self.info_labels[key] = lbl
            
        # -- 当前像素信息 (RGB) --
        pixel_group = ttk.LabelFrame(ctrl_container, text=" 像素信息 ", style='Side.TLabelframe', padding=8)
        pixel_group.pack(fill=limited_tk.X, pady=(0, 10))
        
        # 横向排列 RGB 和 坐标
        pixel_row = ttk.Frame(pixel_group, style='Side.TFrame')
        pixel_row.pack(fill=limited_tk.X)
        
        self.rgb_label = ttk.Label(pixel_row, text="R: -  G: -  B: -", style='RGB.TLabel', anchor='center')
        self.rgb_label.pack(side=limited_tk.LEFT, fill=limited_tk.X, expand=True, padx=(0, 3))
        
        self.pos_label = ttk.Label(pixel_row, text="X: 0, Y: 0", style='Value.TLabel', background='#f0f0f0', anchor='center', padding=5)
        self.pos_label.pack(side=limited_tk.LEFT, fill=limited_tk.X, expand=True, padx=(3, 0))
        
        # -- 缩放控制 --
        zoom_group = ttk.LabelFrame(ctrl_container, text=" 视图 ", style='Side.TLabelframe', padding=8)
        zoom_group.pack(fill=limited_tk.X, pady=(0, 10))
        
        zoom_btns = ttk.Frame(zoom_group, style='Side.TFrame')
        zoom_btns.pack(fill=limited_tk.X)
        ttk.Button(zoom_btns, text="🔍 适应窗口", command=self.zoom_fit).pack(side=limited_tk.LEFT, fill=limited_tk.X, expand=True, padx=(0, 5))
        ttk.Button(zoom_btns, text="100%", command=self.zoom_100).pack(side=limited_tk.LEFT, fill=limited_tk.X, expand=True, padx=(5, 0))
        
        # -- 裁剪设置 --
        crop_group = ttk.LabelFrame(ctrl_container, text=" 裁剪参数 ", style='Side.TLabelframe', padding=8)
        crop_group.pack(fill=limited_tk.X, pady=(0, 10))
        
        # 坐标模式
        mode_frame = ttk.Frame(crop_group, style='Side.TFrame')
        mode_frame.pack(fill=limited_tk.X, pady=(0, 10))
        ttk.Label(mode_frame, text="单位:", style='Info.TLabel', background=COLOR_BG_SIDE).pack(side=limited_tk.LEFT)
        self.coord_mode = limited_tk.StringVar(value="pixel")
        rr_style = ttk.Style()
        rr_style.configure('TRadiobutton', background=COLOR_BG_SIDE)
        ttk.Radiobutton(mode_frame, text="像素", variable=self.coord_mode, value="pixel", command=self.update_crop_inputs).pack(side=limited_tk.LEFT, padx=10)
        self.geo_radio = ttk.Radiobutton(mode_frame, text="地理 (经纬度)", variable=self.coord_mode, value="geo", command=self.update_crop_inputs)
        self.geo_radio.pack(side=limited_tk.LEFT)
        
        # 输入框网格
        grid = ttk.Frame(crop_group, style='Side.TFrame')
        grid.pack(fill=limited_tk.X)
        
        self.entries = {}
        for i, (k, label) in enumerate([('x', 'X / 经度'), ('y', 'Y / 纬度'), ('w', '宽度'), ('h', '高度')]):
            ttk.Label(grid, text=label, style='Info.TLabel', background=COLOR_BG_SIDE).grid(row=i, column=0, sticky='e', pady=4)
            ent = ttk.Entry(grid, font=FONT_MONO)
            ent.grid(row=i, column=1, sticky='ew', padx=5, pady=4)
            ent.bind('<Return>', lambda e: self.apply_input_bounds())
            self.entries[k] = ent
        
        grid.columnconfigure(1, weight=1)
        
        action_frame = ttk.Frame(crop_group, style='Side.TFrame')
        action_frame.pack(fill=limited_tk.X, pady=(10, 0))
        ttk.Button(action_frame, text="应用数值", command=self.apply_input_bounds).pack(side=limited_tk.LEFT, fill=limited_tk.X, expand=True, padx=(0, 5))
        ttk.Button(action_frame, text="重置", command=self.reset_crop).pack(side=limited_tk.LEFT, fill=limited_tk.X, expand=True, padx=(5, 0))

        # -- 底部状态栏 --
        status_bar = ttk.Frame(self.root, relief=limited_tk.SUNKEN, padding=(5, 2))
        status_bar.pack(side=limited_tk.BOTTOM, fill=limited_tk.X)
        self.status_var = limited_tk.StringVar()
        ttk.Label(status_bar, textvariable=self.status_var, font=('Segoe UI', 9)).pack(side=limited_tk.LEFT)
        
        # 提示信息
        ttk.Label(status_bar, text="提示: 滚轮缩放 | 右键平移 | 左键框选 | 拖动框移动/调整", foreground=COLOR_TEXT_SEC, font=('Segoe UI', 9)).pack(side=limited_tk.RIGHT)

    def bind_events(self):
        """绑定交互事件"""
        # Canvas 基础事件
        self.canvas.bind('<ButtonPress-1>', self.on_crop_start)
        self.canvas.bind('<B1-Motion>', self.on_crop_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_crop_end)
        
        self.canvas.bind('<ButtonPress-3>', self.on_pan_start)
        self.canvas.bind('<B3-Motion>', self.on_pan_drag)
        self.canvas.bind('<ButtonRelease-3>', self.on_pan_end)
        
        # 滚轮缩放 (Windows/Linux/Mac 兼容)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)  # Windows
        self.canvas.bind('<Button-4>', self.on_mouse_wheel)    # Linux Scroll Up
        self.canvas.bind('<Button-5>', self.on_mouse_wheel)    # Linux Scroll Down
        
        # 鼠标移动 (RGB取色)
        self.canvas.bind('<Motion>', self.on_mouse_move)
        
        # 窗口重绘
        self.canvas.bind('<Configure>', self.on_resize)
        
        # 键盘快捷键
        self.root.bind('<Control-o>', lambda e: self.open_image())
        self.root.bind('<Control-O>', lambda e: self.open_image())
        self.root.bind('<Control-s>', lambda e: self.save_crop())
        self.root.bind('<Control-S>', lambda e: self.save_crop())
        self.root.bind('<Escape>', lambda e: self.reset_crop())
        self.root.bind('<f>', lambda e: self.zoom_fit())
        self.root.bind('<F>', lambda e: self.zoom_fit())
        self.root.bind('<Key-1>', lambda e: self.zoom_100())
        
        # 缩放快捷键 (+/-)
        self.root.bind('<plus>', lambda e: self.zoom_in())
        self.root.bind('<equal>', lambda e: self.zoom_in())  # 兼容 =
        self.root.bind('<minus>', lambda e: self.zoom_out())
        self.root.bind('<underscore>', lambda e: self.zoom_out()) # 兼容 _
        
        # 裁剪框微调
        self.root.bind('<Left>', lambda e: self.move_crop(-1, 0))
        self.root.bind('<Right>', lambda e: self.move_crop(1, 0))
        self.root.bind('<Up>', lambda e: self.move_crop(0, -1))
        self.root.bind('<Down>', lambda e: self.move_crop(0, 1))
        self.root.bind('<Shift-Left>', lambda e: self.move_crop(-10, 0))
        self.root.bind('<Shift-Right>', lambda e: self.move_crop(10, 0))
        self.root.bind('<Shift-Up>', lambda e: self.move_crop(0, -10))
        self.root.bind('<Shift-Down>', lambda e: self.move_crop(0, 10))

    # ===== 核心逻辑: 坐标变换 =====
    
    def image_to_canvas(self, ix, iy):
        """影像坐标 -> 画布坐标"""
        cx = ix * self.scale + self.offset_x
        cy = iy * self.scale + self.offset_y
        return cx, cy

    def canvas_to_image(self, cx, cy):
        """画布坐标 -> 影像坐标"""
        ix = (cx - self.offset_x) / self.scale
        iy = (cy - self.offset_y) / self.scale
        return ix, iy

    def _geo_to_pixel(self, gx, gy):
        if not self.has_geo: return gx, gy
        
        # 使用逆变换矩阵 (如果可用)
        if self.inv_geo_transform:
            gt = self.inv_geo_transform
            px = gt[0] + gx * gt[1] + gy * gt[2]
            py = gt[3] + gx * gt[4] + gy * gt[5]
            return px, py
            
        # 简单回退 (仅当无旋转时准确)
        gt = self.geo_transform
        px = (gx - gt[0]) / gt[1]
        py = (gy - gt[3]) / gt[5]
        return px, py

    def _pixel_to_geo(self, px, py):
        if not self.has_geo: return px, py
        gt = self.geo_transform
        gx = gt[0] + px * gt[1] + py * gt[2]
        gy = gt[3] + px * gt[4] + py * gt[5]
        return gx, gy

    # ===== 核心逻辑: 图像加载与显示 =====

    def open_image(self):
        filename = filedialog.askopenfilename(
            filetypes=[("图像文件", "*.tif *.jpg *.png *.img *.bmp"), ("所有文件", "*.*")]
        )
        if not filename: return
        
        try:
            self._load_file(filename)
            self.zoom_fit()
            self.status_var.set(f"已加载: {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件: {e}")

    def _load_file(self, filepath):
        self.current_file = filepath
        
        # 1. 尝试 GDAL 加载元数据
        if GDAL_AVAILABLE:
            self.dataset = gdal.Open(filepath)
            if self.dataset:
                self.img_width = self.dataset.RasterXSize
                self.img_height = self.dataset.RasterYSize
                self.img_bands = self.dataset.RasterCount
                self.geo_transform = self.dataset.GetGeoTransform()
                self.projection = self.dataset.GetProjection()
                
                # 判断是否有有效地理坐标
                self.has_geo = (self.geo_transform and self.geo_transform != (0,1,0,0,0,1))
                
                # 计算逆变换矩阵
                if self.has_geo:
                    try:
                        self.inv_geo_transform = gdal.InvGeoTransform(self.geo_transform)
                    except:
                        self.inv_geo_transform = None
                
                # 读取图像数据用于显示 (仅读取 RGB 或 灰度)
                # 为性能考虑，如果图像非常大，应该读取概览(Overview) 或 降采样
                # 这里简单处理: 如果 width > 2000，读取降采样版本用于 display
                # 实际裁剪时再读原始数据
                
                # 简单的读取逻辑
                if self.img_bands >= 3:
                     # 读取前3波段
                     bands = [self.dataset.GetRasterBand(i).ReadAsArray() for i in range(1, 4)]
                     arr = np.dstack(bands)
                else:
                     arr = self.dataset.GetRasterBand(1).ReadAsArray()
                
                # 转为 uint8
                if arr.dtype != np.uint8:
                    # 简单的 2% - 98% 拉伸
                    p2, p98 = np.percentile(arr, 2), np.percentile(arr, 98)
                    if p98 > p2:
                        arr = np.clip((arr - p2) / (p98 - p2) * 255, 0, 255).astype(np.uint8)
                    else:
                        arr = np.zeros_like(arr, dtype=np.uint8)
                
                if len(arr.shape) == 2:
                    self.original_image = Image.fromarray(arr, mode='L')
                else:
                    self.original_image = Image.fromarray(arr, mode='RGB')
            else:
                self._load_fallback(filepath)
        else:
            self._load_fallback(filepath)
            
        # 更新 UI
        self.info_labels['file'].config(text=os.path.basename(filepath))
        self.info_labels['size'].config(text=f"{self.img_width} x {self.img_height}")
        self.info_labels['bands'].config(text=str(self.img_bands))
        
        # 解析 EPSG 代码
        proj_text = "None"
        if self.has_geo and self.projection:
            try:
                from osgeo import osr
                srs = osr.SpatialReference()
                srs.ImportFromWkt(self.projection)
                epsg = srs.GetAuthorityCode(None)
                if epsg:
                    proj_text = f"EPSG:{epsg}"
                else:
                    proj_text = "有投影 (非EPSG)"
            except Exception:
                proj_text = "有投影"
        self.info_labels['proj'].config(text=proj_text)
        
        if self.has_geo:
            self.geo_radio.config(state='normal')
        else:
            self.coord_mode.set('pixel')
            self.geo_radio.config(state='disabled')

    def _load_fallback(self, filepath):
        """PIL 回退加载"""
        self.original_image = Image.open(filepath)
        self.img_width, self.img_height = self.original_image.size
        self.img_bands = len(self.original_image.getbands())
        self.has_geo = False
        self.dataset = None
        self.inv_geo_transform = None

    def zoom_fit(self):
        """适应窗口显示"""
        if not self.original_image: return
        
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10: cw, ch = 800, 600
        
        w_ratio = cw / self.img_width
        h_ratio = ch / self.img_height
        self.scale = min(w_ratio, h_ratio) * 0.95  # 留一点边距
        
        # 居中
        disp_w = self.img_width * self.scale
        disp_h = self.img_height * self.scale
        self.offset_x = (cw - disp_w) / 2
        self.offset_y = (ch - disp_h) / 2
        
        self.redraw()

    def zoom_100(self):
        """100% 原始尺寸显示"""
        if not self.original_image: return
        
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10: cw, ch = 800, 600
        
        self.scale = 1.0
        
        # 居中
        self.offset_x = (cw - self.img_width) / 2
        self.offset_y = (ch - self.img_height) / 2
        
        self.redraw()

    def zoom_in(self):
        self._zoom_view(ZOOM_FACTOR)

    def zoom_out(self):
        self._zoom_view(1.0 / ZOOM_FACTOR)

    def _zoom_view(self, factor):
        if not self.original_image: return
        
        # 中心缩放
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2
        
        new_scale = self.scale * factor
        if new_scale < MIN_ZOOM: new_scale = MIN_ZOOM
        if new_scale > MAX_ZOOM: new_scale = MAX_ZOOM
        real_factor = new_scale / self.scale
        self.scale = new_scale
        
        # Offset adjust based on center
        self.offset_x = cx - (cx - self.offset_x) * real_factor
        self.offset_y = cy - (cy - self.offset_y) * real_factor
        
        self.redraw()

    def redraw(self):
        """重绘图像 (基于视口裁剪优化)"""
        if not self.original_image: return
        
        # 1. 计算可视区域 (Image Coords)
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        # 视口在图像上的四个角点（反解坐标）
        # 只要有一部分在画布内，就绘制
        
        # 简单策略：总是全屏重绘可能会卡，但 PIL crop+resize 很快
        # 让我们计算需要 crop 的原始图像区域
        
        # visible: (0,0) -> (cw, ch) in canvas
        # -> image coords
        ix1, iy1 = self.canvas_to_image(0, 0)
        ix2, iy2 = self.canvas_to_image(cw, ch)
        
        # 取整并约束
        ix1 = max(0, int(ix1))
        iy1 = max(0, int(iy1))
        ix2 = min(self.img_width, int(ix2) + 1)
        iy2 = min(self.img_height, int(iy2) + 1)
        
        if ix2 <= ix1 or iy2 <= iy1:
            self.canvas.delete("img") 
            # 图像完全不可见
            return

        # 2. Crop
        try:
            # 只有当缩放比例很大时（查看细节），Crop 才有意义
            # 如果缩放比例很小（查看全图），全图 Resize
            
            # 为了平滑，我们简单地总是:
            # - 如果 scale < 1.0 (缩小): Resize 全图 (缓存?) -> Crop (其实不用 crop，直接放)
            # - 如果 scale >= 1.0 (放大): Crop ROI -> Resize -> Put
            
            # 但这里为了代码简单且健壮：
            # 总是 Crop visible ROI -> Resize to target screen size
            
            roi = self.original_image.crop((ix1, iy1, ix2, iy2))
            
            # 目标显示大小
            # ROI width in image = (ix2 - ix1)
            # ROI width in screen = (ix2 - ix1) * scale
            # 但要注意 pixel alignment，可能会有细微抖动
            
            target_w = int((ix2 - ix1) * self.scale) + 1 # +1 避免缝隙
            target_h = int((iy2 - iy1) * self.scale) + 1
            
            # 避免 target 尺寸过大 (比如极度放大)
            # PIL resize limite check? usually fine.
            
            disp_img = roi.resize((target_w, target_h), Image.Resampling.NEAREST)
            self.photo_image = ImageTk.PhotoImage(disp_img)
            
            # 放置位置
            # image (ix1, iy1) -> canvas ? 
            dest_x, dest_y = self.image_to_canvas(ix1, iy1)
            
            self.canvas.delete("img")
            self.canvas.create_image(dest_x, dest_y, anchor='nw', image=self.photo_image, tags="img")
            
            # 将图像置于底层
            self.canvas.tag_lower("img")
            
            # 更新 Zoom Label
            self.zoom_label.place(x=10, y=10)
            self.zoom_label.config(text=f"{int(self.scale * 100)}%")
            
            # 重绘裁剪框
            self.draw_crop_rect()
            
        except Exception as e:
            print(f"Redraw error: {e}")

    def draw_crop_rect(self):
        """绘制裁剪框和手柄"""
        self.canvas.delete("crop_rect")
        self.canvas.delete("crop_handle")
        if not self.crop_bounds: return
        
        bx, by, bw, bh = self.crop_bounds
        
        # 转换为 Canvas 坐标
        cx1, cy1 = self.image_to_canvas(bx, by)
        cx2, cy2 = self.image_to_canvas(bx + bw, by + bh)
        
        # 主框
        self.rect_id = self.canvas.create_rectangle(
            cx1, cy1, cx2, cy2, 
            outline='#00FF00', width=2, tags="crop_rect"
        )
        
        # 绘制四角手柄
        hs = HANDLE_SIZE
        handles = [
            ('nw', cx1, cy1), ('ne', cx2, cy1),
            ('sw', cx1, cy2), ('se', cx2, cy2)
        ]
        for name, hx, hy in handles:
            self.canvas.create_rectangle(
                hx - hs, hy - hs, hx + hs, hy + hs,
                fill='#00FF00', outline='#FFFFFF', width=1, tags="crop_handle"
            )
        
        # 绘制尺寸信息标签 (智能定位)
        dim_text = f"{bw} × {bh}"
        label_x = (cx1 + cx2) / 2
        canvas_h = self.canvas.winfo_height()
        
        # 如果底部空间不够，显示在框的上方
        if cy2 + 40 > canvas_h:
            label_y = cy1 - 10
            anchor = 's'
        else:
            label_y = cy2 + 10
            anchor = 'n'
        
        # 确保标签不超出画布左右边界
        label_x = max(50, min(label_x, self.canvas.winfo_width() - 50))
        
        self.dim_label.config(text=dim_text)
        self.dim_label.place(x=label_x, y=label_y, anchor=anchor)

    # ===== 事件处理 =====

    def on_resize(self, event):
        self.redraw()

    def on_mouse_wheel(self, event):
        if not self.original_image: return
        
        # 确定滚轮方向
        if event.num == 5 or event.delta < 0:
            factor = 1.0 / ZOOM_FACTOR
        else:
            factor = ZOOM_FACTOR
            
        # 限制缩放
        new_scale = self.scale * factor
        if new_scale < MIN_ZOOM: new_scale = MIN_ZOOM
        if new_scale > MAX_ZOOM: new_scale = MAX_ZOOM
        real_factor = new_scale / self.scale
        self.scale = new_scale
        
        # 以鼠标为中心缩放
        # Mouse in canvas
        mx, my = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Offset adjust:
        # new_off = mx - (mx - old_off) * factor
        self.offset_x = mx - (mx - self.offset_x) * real_factor
        self.offset_y = my - (my - self.offset_y) * real_factor
        
        self.redraw()

    def on_mouse_move(self, event):
        if not self.original_image: return
        
        mx, my = event.x, event.y
        ix, iy = self.canvas_to_image(mx, my)
        ix, iy = int(ix), int(iy)
        
        if 0 <= ix < self.img_width and 0 <= iy < self.img_height:
            # RGB 取值
            try:
                # 为了性能，不应该每次 move 都去 crop original，但对于单个像素还可以
                pixel = self.original_image.getpixel((ix, iy))
                if isinstance(pixel, int): # Grayscale
                    self.rgb_label.config(text=f"Gray: {pixel}")
                    self.canvas.config(cursor='crosshair')
                else:
                    if len(pixel) >= 3:
                        self.rgb_label.config(text=f"R: {pixel[0]:<3} G: {pixel[1]:<3} B: {pixel[2]:<3}")
                    else:
                        self.rgb_label.config(text=f"Val: {pixel}")
            except Exception:
                self.rgb_label.config(text="R: -  G: -  B: -")
            
            # 光标反馈：检测手柄/裁剪框
            handle = self._get_handle_at(mx, my)
            if handle:
                cursors = {'nw': 'size_nw_se', 'se': 'size_nw_se', 'ne': 'size_ne_sw', 'sw': 'size_ne_sw'}
                self.canvas.config(cursor=cursors.get(handle, 'crosshair'))
            elif self._is_inside_crop(mx, my):
                self.canvas.config(cursor='fleur')
            else:
                self.canvas.config(cursor='crosshair')
            
            # 坐标显示
            if self.coord_mode.get() == 'pixel':
                self.pos_label.config(text=f"X: {ix}  Y: {iy}")
            else:
                gx, gy = self._pixel_to_geo(ix, iy)
                self.pos_label.config(text=f"Lon: {gx:.6f}\nLat: {gy:.6f}")
        else:
            self.rgb_label.config(text="R: -  G: -  B: -")
            self.pos_label.config(text="超出范围")
            self.canvas.config(cursor='arrow')

    # --- 平移 ---
    def on_pan_start(self, event):
        self.dragging_pan = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.config(cursor="fleur")

    def on_pan_drag(self, event):
        if not self.dragging_pan: return
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        self.offset_x += dx
        self.offset_y += dy
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.redraw()

    def on_pan_end(self, event):
        self.dragging_pan = False
        self.canvas.config(cursor="crosshair")

    # --- 裁剪 ---
    def _get_handle_at(self, cx, cy):
        """检测鼠标是否在手柄上"""
        if not self.crop_bounds: return None
        
        bx, by, bw, bh = self.crop_bounds
        hx1, hy1 = self.image_to_canvas(bx, by)
        hx2, hy2 = self.image_to_canvas(bx + bw, by + bh)
        
        hs = HANDLE_SIZE + 4  # 稍微扩大检测范围
        handles = {
            'nw': (hx1, hy1), 'ne': (hx2, hy1),
            'sw': (hx1, hy2), 'se': (hx2, hy2)
        }
        
        for name, (hx, hy) in handles.items():
            if abs(cx - hx) <= hs and abs(cy - hy) <= hs:
                return name
        return None

    def _is_inside_crop(self, cx, cy):
        """检测鼠标是否在裁剪框内"""
        if not self.crop_bounds: return False
        
        bx, by, bw, bh = self.crop_bounds
        cx1, cy1 = self.image_to_canvas(bx, by)
        cx2, cy2 = self.image_to_canvas(bx + bw, by + bh)
        
        return cx1 < cx < cx2 and cy1 < cy < cy2

    def on_crop_start(self, event):
        if not self.original_image: return
        
        cx, cy = event.x, event.y
        
        # 检测是否点击了手柄
        handle = self._get_handle_at(cx, cy)
        if handle:
            self.crop_drag_mode = 'resize'
            self.active_handle = handle
            self.drag_start_bounds = self.crop_bounds
            self.crop_start_x = cx
            self.crop_start_y = cy
            return
        
        # 检测是否点击了裁剪框内部
        if self._is_inside_crop(cx, cy):
            self.crop_drag_mode = 'move'
            self.active_handle = None
            self.drag_start_bounds = self.crop_bounds
            self.crop_start_x = cx
            self.crop_start_y = cy
            return
        
        # 否则开始绘制新框
        self.dragging_crop = True
        self.crop_drag_mode = None
        self.crop_start_x = cx
        self.crop_start_y = cy
        
        # 移除旧框和尺寸标签
        self.crop_bounds = None
        self.canvas.delete("crop_rect")
        self.canvas.delete("crop_handle")
        self.dim_label.place_forget()

    def on_crop_drag(self, event):
        cx, cy = event.x, event.y
        
        if self.crop_drag_mode == 'move' and self.drag_start_bounds:
            # 移动裁剪框
            dx = cx - self.crop_start_x
            dy = cy - self.crop_start_y
            
            ox, oy, ow, oh = self.drag_start_bounds
            # 转换位移到图像坐标
            dx_img = dx / self.scale
            dy_img = dy / self.scale
            
            new_x = int(ox + dx_img)
            new_y = int(oy + dy_img)
            
            # 约束边界
            new_x = max(0, min(new_x, self.img_width - ow))
            new_y = max(0, min(new_y, self.img_height - oh))
            
            self.crop_bounds = (new_x, new_y, ow, oh)
            self.redraw()
            return
            
        if self.crop_drag_mode == 'resize' and self.drag_start_bounds:
            # 调整裁剪框大小
            ox, oy, ow, oh = self.drag_start_bounds
            dx = (cx - self.crop_start_x) / self.scale
            dy = (cy - self.crop_start_y) / self.scale
            
            nx, ny, nw, nh = ox, oy, ow, oh
            h = self.active_handle
            
            if 'e' in h:
                nw = max(10, ow + dx)
            if 'w' in h:
                nx = ox + dx
                nw = max(10, ow - dx)
            if 's' in h:
                nh = max(10, oh + dy)
            if 'n' in h:
                ny = oy + dy
                nh = max(10, oh - dy)
            
            self.crop_bounds = (int(nx), int(ny), int(nw), int(nh))
            self.redraw()
            return
        
        if not self.dragging_crop: return
        
        # 绘制临时框 (Canvas coords)
        self.canvas.delete("crop_rect")
        self.canvas.delete("crop_handle")
        self.canvas.create_rectangle(
            self.crop_start_x, self.crop_start_y, cx, cy,
            outline='#00FF00', width=2, tags="crop_rect"
        )
        
        # 实时显示尺寸 (智能定位)
        ix1, iy1 = self.canvas_to_image(self.crop_start_x, self.crop_start_y)
        ix2, iy2 = self.canvas_to_image(cx, cy)
        tw, th = int(abs(ix2 - ix1)), int(abs(iy2 - iy1))
        self.dim_label.config(text=f"{tw} × {th}")
        
        label_x = (self.crop_start_x + cx) / 2
        bottom_y = max(self.crop_start_y, cy)
        top_y = min(self.crop_start_y, cy)
        canvas_h = self.canvas.winfo_height()
        
        # 如果底部空间不够，显示在框的上方
        if bottom_y + 40 > canvas_h:
            label_y = top_y - 10
            anchor = 's'
        else:
            label_y = bottom_y + 10
            anchor = 'n'
        
        label_x = max(50, min(label_x, self.canvas.winfo_width() - 50))
        self.dim_label.place(x=label_x, y=label_y, anchor=anchor)

    def on_crop_end(self, event):
        if self.crop_drag_mode in ('move', 'resize'):
            self.crop_drag_mode = None
            self.active_handle = None
            self.drag_start_bounds = None
            self.update_crop_inputs()
            return
        
        self.dragging_crop = False
        
        # 计算 Image Coords
        cx1, cy1 = self.crop_start_x, self.crop_start_y
        cx2, cy2 = event.x, event.y
        
        ix1, iy1 = self.canvas_to_image(cx1, cy1)
        ix2, iy2 = self.canvas_to_image(cx2, cy2)
        
        # Normalize
        x = min(ix1, ix2)
        y = min(iy1, iy2)
        w = abs(ix2 - ix1)
        h = abs(iy2 - iy1)
        
        # 约束有效性
        if w < 1 or h < 1:
            self.crop_bounds = None
            self.canvas.delete("crop_rect")
            self.dim_label.place_forget()
            return
            
        # 存为整数像素
        self.crop_bounds = (int(x), int(y), int(w), int(h))
        self.redraw() # 重绘以修正框的位置到整数像素网格
        self.update_crop_inputs()

    def update_crop_inputs(self):
        """更新右侧输入框"""
        mode = self.coord_mode.get()
        
        # 如果没有裁剪框，尝试转换现有输入值
        if not self.crop_bounds:
            try:
                # 获取当前输入值
                v_x = float(self.entries['x'].get())
                v_y = float(self.entries['y'].get())
                v_w = float(self.entries['w'].get())
                v_h = float(self.entries['h'].get())
                
                # 转换逻辑：
                # 如果现在的 mode 是 'geo'，说明之前是 'pixel' (Pixel -> Geo)
                # 如果现在的 mode 是 'pixel'，说明之前是 'geo' (Geo -> Pixel)
                
                vals = {}
                if mode == 'geo': # Pixel -> Geo
                    gx1, gy1 = self._pixel_to_geo(v_x, v_y)
                    gx2, gy2 = self._pixel_to_geo(v_x + v_w, v_y + v_h)
                    vals = {
                        'x': min(gx1, gx2), 'y': min(gy1, gy2),
                        'w': abs(gx1 - gx2), 'h': abs(gy1 - gy2)
                    }
                else: # Geo -> Pixel
                    px1, py1 = self._geo_to_pixel(v_x, v_y)
                    px2, py2 = self._geo_to_pixel(v_x + v_w, v_y + v_h)
                    vals = {
                        'x': min(px1, px2), 'y': min(py1, py2),
                        'w': abs(px1 - px2), 'h': abs(py1 - py2)
                    }
                
                # 更新输入框
                for k, v in vals.items():
                    self.entries[k].delete(0, limited_tk.END)
                    fmt = "{:.0f}" if mode == 'pixel' else "{:.6f}"
                    self.entries[k].insert(0, fmt.format(v))
                    
            except ValueError:
                # 如果输入无效，不做任何事（或者清空）
                pass
            return

        x, y, w, h = self.crop_bounds
        
        mode = self.coord_mode.get()
        vals = {}
        
        if mode == 'pixel':
            vals = {'x': x, 'y': y, 'w': w, 'h': h}
        else:
            # 转换为 Geo
            gx, gy = self._pixel_to_geo(x, y)
            gx2, gy2 = self._pixel_to_geo(x+w, y+h)
            vals = {
                'x': min(gx, gx2), 
                'y': min(gy, gy2),
                'w': abs(gx2 - gx), 
                'h': abs(gy2 - gy)
            }
            
        for k, v in vals.items():
            self.entries[k].delete(0, limited_tk.END)
            fmt = "{:.0f}" if mode == 'pixel' else "{:.6f}"
            self.entries[k].insert(0, fmt.format(v))

    def apply_input_bounds(self):
        """应用手动输入"""
        if not self.original_image: return
        try:
            v_x = float(self.entries['x'].get())
            v_y = float(self.entries['y'].get())
            v_w = float(self.entries['w'].get())
            v_h = float(self.entries['h'].get())
            
            if self.coord_mode.get() == 'pixel':
                self.crop_bounds = (int(v_x), int(v_y), int(v_w), int(v_h))
            else:
                # Geo -> Pixel
                p1_x, p1_y = self._geo_to_pixel(v_x, v_y)
                p2_x, p2_y = self._geo_to_pixel(v_x + v_w, v_y + v_h)
                
                x = min(p1_x, p2_x)
                y = min(p1_y, p2_y)
                w = abs(p2_x - p1_x)
                h = abs(p2_y - p1_y)
                self.crop_bounds = (int(x), int(y), int(w), int(h))
            
            self.redraw()
            
        except ValueError:
            messagebox.showwarning("错误", "请输入有效的数字")

    def move_crop(self, dx, dy):
        """移动裁剪框"""
        if not self.crop_bounds: return
        x, y, w, h = self.crop_bounds
        
        # 移动
        nx = x + dx
        ny = y + dy
        
        # 约束边界
        nx = max(0, min(nx, self.img_width - w))
        ny = max(0, min(ny, self.img_height - h))
        
        self.crop_bounds = (nx, ny, w, h)
        self.redraw()
        self.update_crop_inputs()

    def reset_crop(self):
        self.crop_bounds = None
        self.redraw()
        for v in self.entries.values(): v.delete(0, limited_tk.END)

    def save_crop(self):
        if not self.crop_bounds:
            messagebox.showinfo("提示", "请先选择裁剪区域")
            return
            
        out_path = filedialog.asksaveasfilename(
            defaultextension=".tif",
            filetypes=[("GeoTIFF", "*.tif"), ("PNG", "*.png"), ("JPG", "*.jpg")]
        )
        if not out_path: return
        
        x, y, w, h = self.crop_bounds
        
        try:
            # 优先使用 GDAL 裁剪以保留元数据
            from .crop_core import crop_by_pixel
            if crop_by_pixel(self.current_file, out_path, x, y, w, h):
                messagebox.showinfo("成功", "裁剪并保存成功！")
            else:
                # Fallback
                crp = self.original_image.crop((x, y, x+w, y+h))
                crp.save(out_path)
                messagebox.showinfo("成功", f"保存成功 (PIL模式)\n{out_path}")
        except Exception as e:
            messagebox.showerror("失败", f"保存出错: {e}")

def main():
    root = limited_tk.Tk()
    app = ImageCropApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
