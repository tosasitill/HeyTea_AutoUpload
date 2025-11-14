"""
杯贴图像处理模块
包含半调点、Bayer、Floyd-Steinberg等算法的实现
"""

import numpy as np
from PIL import Image
import io

# Bayer 8x8 阈值表 (0..63)
BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21],
], dtype=np.uint8)


def scale_image_to_canvas(image: Image.Image, canvas_width: int, canvas_height: int, scale_percent: float) -> tuple:
    """
    根据缩放百分比将图像缩放并居中放置到画布中
    返回 (缩放后图像数组, 原始宽度, 原始高度, 实际缩放比例)
    """
    img_w, img_h = image.size
    
    # 计算基础缩放比例（使图像适应画布）
    base_scale = min(canvas_width / img_w, canvas_height / img_h)
    
    # 应用用户指定的百分比缩放
    scale_factor = scale_percent / 100.0
    real_scale = base_scale * scale_factor
    
    # 计算新尺寸
    new_w = int(img_w * real_scale)
    new_h = int(img_h * real_scale)
    
    # 缩放图像
    scaled_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # 创建白色背景画布
    canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
    
    # 计算居中位置
    offset_x = (canvas_width - new_w) // 2
    offset_y = (canvas_height - new_h) // 2
    
    # 粘贴图像到画布
    canvas.paste(scaled_img, (offset_x, offset_y))
    
    return np.array(canvas), img_w, img_h, real_scale


def to_grayscale(img_array: np.ndarray) -> np.ndarray:
    """
    将RGB图像转换为灰度图像
    """
    if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        gray = np.round(0.299 * r + 0.587 * g + 0.114 * b).astype(np.uint8)
        return gray
    return img_array.astype(np.uint8)


def apply_gamma_contrast(gray: np.ndarray, contrast: int, gamma: float) -> np.ndarray:
    """
    应用对比度和Gamma调整
    """
    # 对比度调整
    c = np.clip(contrast, -100, 100)
    f = (259 * (c + 255)) / (255 * (259 - c))
    adjusted = f * (gray.astype(float) - 128) + 128
    adjusted = np.clip(adjusted, 0, 255)
    
    # Gamma调整
    g = np.clip(gamma, 0.2, 3.0)
    normalized = adjusted / 255.0
    gamma_corrected = np.power(normalized, g)
    result = np.round(gamma_corrected * 255).astype(np.uint8)
    
    return result


def dither_bayer(gray: np.ndarray) -> np.ndarray:
    """
    Bayer矩阵抖动算法
    """
    h, w = gray.shape
    binary = np.zeros((h, w), dtype=np.uint8)
    
    for y in range(h):
        for x in range(w):
            g = gray[y, x]
            threshold = (BAYER8[y % 8, x % 8] + 0.5) * 4  # 0..255
            binary[y, x] = 255 if g >= threshold else 0
    
    return binary


def dither_floyd_steinberg(gray: np.ndarray, serpentine: bool = True) -> np.ndarray:
    """
    Floyd-Steinberg误差扩散算法
    """
    h, w = gray.shape
    g = gray.astype(np.float32)
    binary = np.zeros((h, w), dtype=np.uint8)
    
    for y in range(h):
        if serpentine:
            left_to_right = (y % 2) == 0
        else:
            left_to_right = True
        
        if left_to_right:
            x_range = range(w)
        else:
            x_range = range(w - 1, -1, -1)
        
        for x in x_range:
            old_val = g[y, x]
            new_val = 0 if old_val < 128 else 255
            binary[y, x] = new_val
            err = old_val - new_val
            
            # 分散误差到周围像素
            if left_to_right:
                if x + 1 < w:
                    g[y, x + 1] += err * 7 / 16
                if y + 1 < h:
                    if x - 1 >= 0:
                        g[y + 1, x - 1] += err * 3 / 16
                    g[y + 1, x] += err * 5 / 16
                    if x + 1 < w:
                        g[y + 1, x + 1] += err * 1 / 16
            else:
                if x - 1 >= 0:
                    g[y, x - 1] += err * 7 / 16
                if y + 1 < h:
                    if x + 1 < w:
                        g[y + 1, x + 1] += err * 3 / 16
                    g[y + 1, x] += err * 5 / 16
                    if x - 1 >= 0:
                        g[y + 1, x - 1] += err * 1 / 16
    
    return binary


def sobel_magnitude(gray: np.ndarray) -> np.ndarray:
    """
    Sobel边缘检测：计算梯度幅值
    """
    h, w = gray.shape
    mag = np.zeros((h, w), dtype=np.uint8)
    
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            # Sobel算子
            gx = (-gray[y-1, x-1] + gray[y-1, x+1] - 
                  2*gray[y, x-1] + 2*gray[y, x+1] -
                  gray[y+1, x-1] + gray[y+1, x+1])
            gy = (-gray[y-1, x-1] - 2*gray[y-1, x] - gray[y-1, x+1] +
                  gray[y+1, x-1] + 2*gray[y+1, x] + gray[y+1, x+1])
            
            mag[y, x] = np.clip(np.abs(gx) + np.abs(gy), 0, 255)
    
    return mag


def dilate_mask(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    """
    形态学膨胀操作
    """
    h, w = mask.shape
    result = mask.copy()
    
    for _ in range(iterations):
        new_result = result.copy()
        for y in range(h):
            for x in range(w):
                if result[y, x] > 0:
                    new_result[y, x] = 1
                    continue
                
                # 检查8邻域
                found = False
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w:
                            if result[ny, nx] > 0:
                                found = True
                                break
                    if found:
                        break
                
                new_result[y, x] = 1 if found else 0
        
        result = new_result
    
    return result.astype(np.uint8)


def apply_edge_protection(binary: np.ndarray, gray: np.ndarray, 
                         lo_threshold: int, hi_threshold: int, 
                         tau_threshold: int, dilate_iters: int = 1) -> np.ndarray:
    """
    边缘保护：仅加黑不漂白
    """
    h, w = gray.shape
    edge = sobel_magnitude(gray)
    black_mask = np.zeros((h, w), dtype=np.uint8)
    
    # 检测应该被加黑的区域
    for y in range(h):
        for x in range(w):
            if gray[y, x] <= lo_threshold or (edge[y, x] >= tau_threshold and gray[y, x] < hi_threshold):
                black_mask[y, x] = 1
    
    # 膨胀黑色掩码
    if dilate_iters > 0:
        black_mask = dilate_mask(black_mask, dilate_iters)
    
    # 只加黑，不改白
    result = binary.copy()
    result[black_mask > 0] = 0
    
    return result


def circle_halftone(gray: np.ndarray, canvas_width: int, canvas_height: int,
                   cell: int, angle_deg: float, shape: str) -> np.ndarray:
    """
    圆形半调点网格算法（支持圆形、方形、十字）
    """
    h, w = gray.shape  # 从灰度图获取实际尺寸
    binary = np.ones((h, w), dtype=np.uint8) * 255  # 白色背景
    
    s = max(2, min(60, cell))
    theta = np.deg2rad(angle_deg)
    c, si = np.cos(theta), np.sin(theta)
    cx, cy = w / 2, h / 2
    
    # 坐标变换函数
    def to_xy(i, j):
        x = cx + s * (i * c - j * si)
        y = cy + s * (i * si + j * c)
        return x, y
    
    def to_ij(x, y):
        dx, dy = x - cx, y - cy
        i = (dx * c + dy * si) / s
        j = (-dx * si + dy * c) / s
        return i, j
    
    # 找到需要覆盖的晶格范围
    corners = [(0, 0), (w, 0), (0, h), (w, h)]
    ijs = [to_ij(x, y) for x, y in corners]
    i_vals, j_vals = zip(*ijs)
    
    i_min = int(np.floor(min(i_vals))) - 1
    i_max = int(np.ceil(max(i_vals))) + 1
    j_min = int(np.floor(min(j_vals))) - 1
    j_max = int(np.ceil(max(j_vals))) + 1
    
    # 采样偏移
    offsets = [-0.35, 0, 0.35]
    side_max = s * 0.98
    
    for J in range(j_min, j_max + 1):
        for I in range(i_min, i_max + 1):
            # 晶格中心
            center_x, center_y = to_xy(I + 0.5, J + 0.5)
            
            if center_x < -s or center_x > w + s or center_y < -s or center_y > h + s:
                continue
            
            # 取样周围像素
            sample_sum = 0.0
            count = 0
            for dv in offsets:
                for du in offsets:
                    sx, sy = to_xy(I + 0.5 + du, J + 0.5 + dv)
                    ix = int(np.clip(np.round(sx), 0, w - 1))
                    iy = int(np.clip(np.round(sy), 0, h - 1))
                    sample_sum += float(gray[iy, ix])
                    count += 1
            
            avg = sample_sum / count if count > 0 else 0
            darkness = 1 - (avg / 255.0)
            radius = np.sqrt(max(0, darkness)) * (side_max / 2)
            
            if radius > 0.25:
                # 绘制形状
                if shape == 'square':
                    # 方形
                    half_side = min(side_max / 2, radius)
                    x_min = int(np.round(center_x - half_side))
                    x_max = int(np.round(center_x + half_side))
                    y_min = int(np.round(center_y - half_side))
                    y_max = int(np.round(center_y + half_side))
                    
                    for y in range(max(0, y_min), min(h, y_max)):
                        for x in range(max(0, x_min), min(w, x_max)):
                            binary[y, x] = 0
                
                elif shape == 'cross':
                    # 十字
                    length = side_max
                    thick = max(1, radius * 0.9)
                    
                    # 水平线
                    y_range = range(max(0, int(center_y - thick/2)), 
                                   min(h, int(center_y + thick/2)))
                    x_range = range(max(0, int(center_x - length/2)), 
                                   min(w, int(center_x + length/2)))
                    for y in y_range:
                        for x in x_range:
                            binary[y, x] = 0
                    
                    # 竖线
                    y_range = range(max(0, int(center_y - length/2)), 
                                   min(h, int(center_y + length/2)))
                    x_range = range(max(0, int(center_x - thick/2)), 
                                   min(w, int(center_x + thick/2)))
                    for y in y_range:
                        for x in x_range:
                            binary[y, x] = 0
                
                else:  # circle
                    # 圆形
                    radius_sq = radius ** 2
                    y_min = max(0, int(center_y - radius))
                    y_max = min(h, int(center_y + radius) + 1)
                    x_min = max(0, int(center_x - radius))
                    x_max = min(w, int(center_x + radius) + 1)
                    
                    for y in range(y_min, y_max):
                        for x in range(x_min, x_max):
                            dx = x - center_x
                            dy = y - center_y
                            if dx*dx + dy*dy <= radius_sq:
                                binary[y, x] = 0
    
    return binary


def process_image(image: Image.Image, mode: str, canvas_width: int, canvas_height: int,
                 scale_percent: float, grid_size: int, shape: str, angle: float,
                 gamma: float, contrast: int, edge_protect: bool,
                 lo_threshold: int = 40, hi_threshold: int = 120,
                 tau_threshold: int = 60, dilate_iters: int = 0,
                 fs_serpentine: bool = True) -> tuple:
    """
    主处理函数：处理图像并返回处理后的图像和预览信息
    
    返回: (处理后的二值化图像数组, 原始宽度, 原始高度, 实际缩放比例)
    """
    # 1. 缩放并居中
    img_array, orig_w, orig_h, real_scale = scale_image_to_canvas(image, canvas_width, canvas_height, scale_percent)
    
    # 2. 转灰度
    gray = to_grayscale(img_array)
    
    # 3. 应用Gamma和对比度
    gray = apply_gamma_contrast(gray, contrast, gamma)
    
    # 4. 二值化
    if mode == 'bayer':
        binary = dither_bayer(gray)
    elif mode == 'fs':
        binary = dither_floyd_steinberg(gray, fs_serpentine)
    else:  # circle/square/cross
        binary = circle_halftone(gray, canvas_width, canvas_height, grid_size, angle, shape)
    
    # 5. 边缘保护
    if edge_protect:
        binary = apply_edge_protection(binary, gray, lo_threshold, hi_threshold, tau_threshold, dilate_iters)
    
    return binary, orig_w, orig_h, real_scale


def generate_print_preview(binary: np.ndarray, label_width: int = 360, label_height: int = 760) -> Image.Image:
    """
    生成打印效果预览（模拟36×76mm标签贴）
    对应HTML版本的 downsamplePreview() 函数
    """
    h, w = binary.shape
    
    # 1. 创建标签背景 #eaeaea
    preview = Image.new('RGB', (label_width, label_height), (234, 234, 234))
    
    # 2. 降采样原图（1.01倍降采样率）
    ratio = 1.01
    new_w = int(w / ratio)
    new_h = int(h / ratio)
    
    # 创建降采样数据（灰度）
    downsampled = np.zeros((new_h, new_w), dtype=np.uint8)
    
    for dy in range(new_h):
        for dx in range(new_w):
            # 计算源图像的采样范围
            sx0 = int(np.floor(dx * ratio))
            sy0 = int(np.floor(dy * ratio))
            sx1 = min(w, int(np.ceil((dx + 1) * ratio)))
            sy1 = min(h, int(np.ceil((dy + 1) * ratio)))
            
            # 计算平均值
            sample_sum = 0.0
            count = 0
            for py in range(sy0, sy1):
                for px in range(sx0, sx1):
                    sample_sum += float(binary[py, px])
                    count += 1
            
            avg = sample_sum / count if count > 0 else 255
            
            # 二值化：avg > 128 为白(234=0xEA)，否则为黑(0)
            downsampled[dy, dx] = 234 if avg > 128 else 0
    
    # 转换为PIL Image（灰度）
    down_img = Image.fromarray(downsampled, 'L')
    
    # 3. 计算缩放参数
    scale = label_width / new_w
    scaled_h = int(new_h * scale)
    offset_y = int((label_height - scaled_h) / 2)
    
    # 4. 缩放并粘贴到标签中心
    down_img_resized = down_img.resize((label_width, scaled_h), Image.Resampling.LANCZOS)
    preview.paste(down_img_resized, (0, offset_y))
    
    # 5. 绘制取餐号码（仅当顶部有足够空白时）
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(preview)
    
    if offset_y > 30:
        try:
            # 尝试使用系统字体，大小56
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 56)
        except:
            # 如果找不到，使用默认字体
            font = ImageFont.load_default()
        
        draw.text((30, 40), '8188', fill='black', font=font)
    
    # 6. 绘制打印误差警告区域（左右各6%）
    warning_width = int(label_width * 0.06)
    warning_color = (255, 100, 100, 102)  # 半透明红色
    
    # 转换为RGBA以支持透明度
    preview_rgba = preview.convert('RGBA')
    warning_overlay = Image.new('RGBA', (label_width, label_height), (0, 0, 0, 0))
    warning_draw = ImageDraw.Draw(warning_overlay)
    
    # 左侧警告区域
    warning_draw.rectangle([0, 0, warning_width, label_height], fill=warning_color)
    
    # 右侧警告区域
    warning_draw.rectangle([label_width - warning_width, 0, label_width, label_height], fill=warning_color)
    
    # 合成
    preview_rgba = Image.alpha_composite(preview_rgba, warning_overlay)
    preview = preview_rgba.convert('RGB')
    
    return preview
