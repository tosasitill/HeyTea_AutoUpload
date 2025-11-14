import json
import time
import heytea_cryption
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
from heytea_api_config import *
import requests
import json
import os
import sys
import subprocess
import numpy as np
from cup_image_processor import process_image, generate_print_preview

# 版本号：从环境变量读取（打包时注入），否则显示git commit hash
def get_version():
    # 优先使用环境变量（打包时注入）
    version = os.environ.get('APP_VERSION')
    if version:
        return version
    
    # 开发环境：尝试获取git commit hash
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return f"dev-{result.stdout.strip()}"
    except:
        pass
    
    return "dev"

VERSION = get_version()


def run_captcha_window(captcha_app_id):
    """运行验证码窗口（子进程模式）"""
    import webview
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-cn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>人机验证</title>
    <script src="https://turing.captcha.qcloud.com/TJCaptcha.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            font-family: Arial, sans-serif;
            background: #ffffff;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 24px;
        }}
        p {{
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }}
        #CaptchaBtn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 40px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}
        #CaptchaBtn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}
        #CaptchaBtn:active {{
            transform: translateY(0);
        }}
        .status {{
            margin-top: 20px;
            padding: 12px;
            border-radius: 6px;
            font-size: 14px;
            display: none;
        }}
        .status.success {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .status.error {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        .loading {{
            display: none;
            margin-top: 20px;
        }}
        .spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 人机验证</h1>
        <p>为了保护您的账号安全，请完成以下验证</p>
        <button id="CaptchaBtn">点击验证</button>
        <div class="loading" id="loading">
            <div class="spinner"></div>
        </div>
        <div class="status" id="status"></div>
    </div>

    <script>
        var captchaInstance = null;
        
        function showStatus(message, isSuccess) {{
            var statusEl = document.getElementById('status');
            statusEl.textContent = message;
            statusEl.className = 'status ' + (isSuccess ? 'success' : 'error');
            statusEl.style.display = 'block';
        }}
        
        function showLoading(show) {{
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }}
        
        function callback(res) {{
            console.log('Captcha callback:', res);
            
            if (res.ret === 0) {{
                showLoading(true);
                showStatus('验证成功！正在处理...', true);
                
                window.pywebview.api.on_captcha_success(res.ticket, res.randstr).then(function() {{
                    setTimeout(function() {{}}, 1000);
                }});
            }} else if (res.ret === 2) {{
                showStatus('已取消验证', false);
                window.pywebview.api.on_captcha_close();
            }} else {{
                showStatus('验证失败: ' + (res.errorMessage || '未知错误'), false);
                if (res.errorCode) {{
                    console.error('Error code:', res.errorCode);
                }}
            }}
        }}
        
        function loadErrorCallback() {{
            showStatus('验证码加载失败，请检查网络连接', false);
            console.error('Captcha load error');
        }}
        
        document.getElementById('CaptchaBtn').addEventListener('click', function() {{
            try {{
                if (!captchaInstance) {{
                    captchaInstance = new TencentCaptcha('{captcha_app_id}', callback, {{
                        userLanguage: 'zh-cn'
                    }});
                }}
                captchaInstance.show();
            }} catch (error) {{
                console.error('Captcha error:', error);
                loadErrorCallback();
            }}
        }});
        
        window.onload = function() {{
            setTimeout(function() {{
                document.getElementById('CaptchaBtn').click();
            }}, 500);
        }};
    </script>
</body>
</html>
"""
    
    class Api:
        def on_captcha_success(self, ticket, randstr):
            result = {'success': True, 'ticket': ticket, 'randstr': randstr}
            print(json.dumps(result), flush=True)
            threading.Timer(0.1, lambda: os._exit(0)).start()
        
        def on_captcha_close(self):
            result = {'success': False}
            print(json.dumps(result), flush=True)
            threading.Timer(0.1, lambda: os._exit(0)).start()
    
    window = webview.create_window('人机验证', html=html_content, width=500, height=600, resizable=False, js_api=Api())
    webview.start()


def show_captcha(captcha_app_id, on_success, on_close=None):
    """显示验证码窗口"""
    import subprocess
    
    # 获取当前执行文件路径（适配打包后的情况）
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        current_executable = sys.executable
        cmd = [current_executable, '--captcha', captcha_app_id]
    else:
        # 如果是开发环境的Python脚本
        cmd = [sys.executable, __file__, '--captcha', captcha_app_id]
    
    # 启动当前程序的子进程，传入特殊参数
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    def monitor_output():
        try:
            for line in process.stdout:
                line = line.strip()
                if line:
                    try:
                        result = json.loads(line)
                        if result.get('success'):
                            if on_success:
                                on_success(result.get('ticket'), result.get('randstr'))
                        else:
                            if on_close:
                                on_close()
                        break
                    except json.JSONDecodeError:
                        continue
            process.wait(timeout=5)
        except Exception as e:
            print(f"Monitor error: {e}")
            if on_close:
                on_close()
        finally:
            try:
                process.terminate()
            except:
                pass
    
    threading.Thread(target=monitor_output, daemon=True).start()


class HeyTeaUploader:
    def __init__(self, root, scale_factor=1.0):
        self.root = root
        self.root.title("喜茶自定义杯贴上传工具")
        # geometry 已经在 main() 中根据 DPI 设置
        self.root.resizable(True, True)  # 允许用户拖动缩放窗口
        self.root.minsize(800, 600)  # 设置最小窗口尺寸
        
        self.token = None
        self.selected_image_path = None
        self.current_mobile = None  # 存储当前正在验证的手机号
        self.captcha_ticket = None  # 存储验证码ticket
        self.captcha_randstr = None  # 存储验证码randstr

        self.nicknake = None
        self.user_main_id = None
        self.config_file = "heytea_config.json"  # 配置文件路径
        
        # 验证码冷却相关
        self.cooldown_seconds = 0  # 剩余冷却秒数
        self.cooldown_timer = None  # 冷却定时器

        self.scale_factor = scale_factor
        
        # 杯贴相关变量
        self.cup_current_file = None
        self.cup_current_image = None
        self.cup_render_timer = None
        self.cup_canvas_images = {}  # 缓存PhotoImage对象
        
        self.create_widgets()
        self.load_config()  # 加载保存的配置
    
    def create_widgets(self):
        # 创建笔记本（Tab控件）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 登录Tab
        self.login_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.login_frame, text="登录")
        
        # 上传Tab
        self.upload_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.upload_frame, text="上传图片")
        
        # 杯贴小助手Tab
        self.cup_sticker_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cup_sticker_frame, text="杯贴小助手")
        
        # 关于Tab
        self.about_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.about_frame, text="关于")
        
        self.create_login_tab()
        self.create_upload_tab()
        self.create_cup_sticker_tab()
        self.create_about_tab()
    
    def create_login_tab(self):
        """创建登录Tab"""
        # 主框架
        main_frame = ttk.Frame(self.login_frame, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="喜茶登录", font=("", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 短信验证码登录区域
        sms_frame = ttk.LabelFrame(main_frame, text="短信验证码登录", padding="15")
        sms_frame.pack(fill='x', pady=(0, 15))
        
        # 手机号
        ttk.Label(sms_frame, text="手机号:").grid(row=0, column=0, sticky='w', pady=5)
        self.mobile_entry = ttk.Entry(sms_frame, width=30)
        self.mobile_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        
        # 获取验证码按钮
        self.get_code_btn = ttk.Button(sms_frame, text="获取验证码", command=self.get_verification_code)
        self.get_code_btn.grid(row=0, column=2, padx=(10, 0), pady=5)
        
        # 验证码
        ttk.Label(sms_frame, text="验证码:").grid(row=1, column=0, sticky='w', pady=5)
        self.code_entry = ttk.Entry(sms_frame, width=30)
        self.code_entry.grid(row=1, column=1, padx=(10, 0), pady=5)
        
        # 登录按钮
        self.login_btn = ttk.Button(sms_frame, text="登录", command=self.login_with_sms)
        self.login_btn.grid(row=2, column=1, pady=(10, 0))
        
        # 分割线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill='x', pady=15)
        
        # Token直接登录区域
        key_frame = ttk.LabelFrame(main_frame, text="Token登录", padding="15")
        key_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(key_frame, text="Token:").grid(row=0, column=0, sticky='w', pady=5)
        self.token_entry = ttk.Entry(key_frame, width=40)
        self.token_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        
        self.key_login_btn = ttk.Button(key_frame, text="使用Token登录", command=self.login_with_key)
        self.key_login_btn.grid(row=1, column=1, pady=(10, 0))
        
        # 保存登录信息复选框（独立区域）
        self.save_login_var = tk.BooleanVar(value=True)
        self.save_login_checkbox = ttk.Checkbutton(
            main_frame, 
            text="记住登录信息", 
            variable=self.save_login_var
        )
        self.save_login_checkbox.pack()
        
        # 状态显示和退出登录按钮区域
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="未登录", foreground="red")
        self.status_label.pack(side='left', padx=(0, 10))
        
        self.logout_btn = ttk.Button(status_frame, text="退出登录", command=self.logout, state='disabled')
        self.logout_btn.pack(side='left')
    
    def create_upload_tab(self):
        """创建上传Tab"""
        main_frame = ttk.Frame(self.upload_frame, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="上传自定义杯贴", font=("", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 图片预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="图片预览", padding="10")
        preview_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        self.preview_label = ttk.Label(preview_frame, text="未选择图片", background="#f0f0f0")
        self.preview_label.pack(fill='both', expand=True)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        self.select_image_btn = ttk.Button(button_frame, text="选择图片", command=self.select_image)
        self.select_image_btn.pack(side='left', padx=(0, 10))
        
        self.upload_btn = ttk.Button(button_frame, text="上传图片", command=self.upload_image, state='disabled')
        self.upload_btn.pack(side='left')
        
        # 上传状态
        self.upload_status_label = ttk.Label(main_frame, text="")
        self.upload_status_label.pack(pady=(10, 0))
    
    def create_about_tab(self):
        """创建关于Tab"""
        main_frame = ttk.Frame(self.about_frame, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="喜茶自定义杯贴上传工具", font=("", 18, "bold"))
        title_label.pack(pady=(20, 10))
        
        # 版本信息
        version_label = ttk.Label(main_frame, text=f"Version {VERSION}", font=("", 10))
        version_label.pack(pady=(0, 20))
        
        # 描述
        desc_label = ttk.Label(
            main_frame, 
            text="一个便捷的GUI工具，用于上传自定义杯贴图片到喜茶服务器",
            font=("", 10),
            wraplength=500,
            justify='center'
        )
        desc_label.pack(pady=(0, 20))
        
        # GitHub链接
        github_frame = ttk.Frame(main_frame)
        github_frame.pack(pady=(10, 0))
        
        github_label = ttk.Label(github_frame, text="项目地址：", font=("", 10))
        github_label.pack(side='left')
        
        github_link = ttk.Label(
            github_frame, 
            text="https://github.com/FuQuan233/HeyTea_AutoUpload",
            font=("", 10),
            foreground="blue",
            cursor="hand2"
        )
        github_link.pack(side='left')
        
        # 绑定点击事件打开浏览器
        def open_github(event):
            import webbrowser
            webbrowser.open("https://github.com/FuQuan233/HeyTea_AutoUpload")
        
        github_link.bind("<Button-1>", open_github)
        
        # 作者信息
        author_label = ttk.Label(main_frame, text="© 2025 FuQuan233", font=("", 9), foreground="gray")
        author_label.pack(pady=(20, 0))
    
    def create_cup_sticker_tab(self):
        """创建杯贴小助手Tab"""
        # 创建主容器
        main_container = ttk.Frame(self.cup_sticker_frame)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建标题
        title_label = ttk.Label(main_container, text="喜茶杯贴小助手", font=("", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 创建两列布局框架
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill='both', expand=True)
        
        # 左侧：控制面板
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # 右侧：预览面板
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # ===== 左侧控制面板 =====
        # 文件上传区域
        drop_frame = ttk.LabelFrame(left_frame, text="选择图片", padding="10")
        drop_frame.pack(fill='x', pady=(0, 10))
        
        self.cup_file_label = ttk.Label(drop_frame, text="点击选择文件或拖放", 
                                        background="#f0f0f0", foreground="#999", justify='center')
        self.cup_file_label.pack(fill='both', expand=True, ipady=30)
        self.cup_file_label.bind('<Button-1>', lambda e: self.cup_select_image())
        
        # 参数控制面板
        params_frame = ttk.LabelFrame(left_frame, text="处理参数", padding="10")
        params_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # 创建内部滚动框架以支持macOS滚动
        canvas = tk.Canvas(params_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(params_frame, orient='vertical', command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # 创建窗口时设置宽度以消除左侧空白
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 当canvas大小改变时更新window宽度
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        
        # 支持鼠标滚轮（macOS）
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        
        # 在scroll_frame中添加参数控制
        # 模式选择
        mode_frame = ttk.Frame(scroll_frame)
        mode_frame.pack(fill='x', pady=2, padx=0)
        ttk.Label(mode_frame, text="处理模式:").pack(side='left')
        self.cup_mode_var = tk.StringVar(value="circle")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.cup_mode_var, 
                                   values=["circle", "bayer", "fs"], state='readonly', width=15)
        mode_combo.pack(side='right', fill='x', expand=True)
        mode_combo.bind('<<ComboboxSelected>>', lambda e: self.cup_schedule_render())
        
        # 图像缩放
        scale_frame = ttk.Frame(scroll_frame)
        scale_frame.pack(fill='x', pady=2, padx=0)
        ttk.Label(scale_frame, text="图像缩放 (%):").pack(side='left')
        self.cup_scale_var = tk.IntVar(value=100)
        self.cup_scale_label = ttk.Label(scale_frame, text="100")
        self.cup_scale_label.pack(side='right', padx=(5, 0))
        scale_slider = ttk.Scale(scale_frame, from_=25, to=300, orient='horizontal',
                                 variable=self.cup_scale_var, command=lambda v: self.cup_update_scale_label())
        scale_slider.pack(side='right', fill='x', expand=True, padx=(0, 5))
        scale_slider.bind('<B1-Motion>', lambda e: self.cup_schedule_render())
        scale_slider.bind('<ButtonRelease-1>', lambda e: self.cup_schedule_render())
        
        # 网格参数（仅圆形模式）
        grid_frame = ttk.Frame(scroll_frame)
        grid_frame.pack(fill='x', pady=2, padx=0)
        ttk.Label(grid_frame, text="网格大小 (px):").pack(side='left')
        self.cup_grid_var = tk.IntVar(value=4)
        self.cup_grid_label = ttk.Label(grid_frame, text="4")
        self.cup_grid_label.pack(side='right', padx=(5, 0))
        grid_slider = ttk.Scale(grid_frame, from_=2, to=16, orient='horizontal',
                               variable=self.cup_grid_var, command=lambda v: self.cup_update_grid_label())
        grid_slider.pack(side='right', fill='x', expand=True, padx=(0, 5))
        grid_slider.bind('<B1-Motion>', lambda e: self.cup_schedule_render())
        grid_slider.bind('<ButtonRelease-1>', lambda e: self.cup_schedule_render())
        
        # 图案形状
        shape_frame = ttk.Frame(scroll_frame)
        shape_frame.pack(fill='x', pady=2, padx=0)
        ttk.Label(shape_frame, text="图案形状:").pack(side='left')
        self.cup_shape_var = tk.StringVar(value="circle")
        shape_combo = ttk.Combobox(shape_frame, textvariable=self.cup_shape_var,
                                  values=["circle", "square", "cross"], state='readonly', width=15)
        shape_combo.pack(side='right', fill='x', expand=True)
        shape_combo.bind('<<ComboboxSelected>>', lambda e: self.cup_schedule_render())
        
        # 网格角度
        angle_frame = ttk.Frame(scroll_frame)
        angle_frame.pack(fill='x', pady=2, padx=0)
        ttk.Label(angle_frame, text="网格角度 (°):").pack(side='left')
        self.cup_angle_var = tk.IntVar(value=45)
        self.cup_angle_label = ttk.Label(angle_frame, text="45")
        self.cup_angle_label.pack(side='right', padx=(5, 0))
        angle_slider = ttk.Scale(angle_frame, from_=0, to=90, orient='horizontal',
                                variable=self.cup_angle_var, command=lambda v: self.cup_update_angle_label())
        angle_slider.pack(side='right', fill='x', expand=True, padx=(0, 5))
        angle_slider.bind('<B1-Motion>', lambda e: self.cup_schedule_render())
        angle_slider.bind('<ButtonRelease-1>', lambda e: self.cup_schedule_render())
        
        # Gamma 调整
        gamma_frame = ttk.Frame(scroll_frame)
        gamma_frame.pack(fill='x', pady=2, padx=0)
        ttk.Label(gamma_frame, text="Gamma:").pack(side='left')
        self.cup_gamma_var = tk.DoubleVar(value=1.0)
        self.cup_gamma_label = ttk.Label(gamma_frame, text="1.00")
        self.cup_gamma_label.pack(side='right', padx=(5, 0))
        gamma_slider = ttk.Scale(gamma_frame, from_=0.2, to=3.0, orient='horizontal',
                                variable=self.cup_gamma_var, command=lambda v: self.cup_update_gamma_label())
        gamma_slider.pack(side='right', fill='x', expand=True, padx=(0, 5))
        gamma_slider.bind('<B1-Motion>', lambda e: self.cup_schedule_render())
        gamma_slider.bind('<ButtonRelease-1>', lambda e: self.cup_schedule_render())
        
        # 对比度
        contrast_frame = ttk.Frame(scroll_frame)
        contrast_frame.pack(fill='x', pady=2, padx=0)
        ttk.Label(contrast_frame, text="对比度:").pack(side='left')
        self.cup_contrast_var = tk.IntVar(value=0)
        self.cup_contrast_label = ttk.Label(contrast_frame, text="0")
        self.cup_contrast_label.pack(side='right', padx=(5, 0))
        contrast_slider = ttk.Scale(contrast_frame, from_=-100, to=100, orient='horizontal',
                                   variable=self.cup_contrast_var, command=lambda v: self.cup_update_contrast_label())
        contrast_slider.pack(side='right', fill='x', expand=True, padx=(0, 5))
        contrast_slider.bind('<B1-Motion>', lambda e: self.cup_schedule_render())
        contrast_slider.bind('<ButtonRelease-1>', lambda e: self.cup_schedule_render())
        
        # 边缘保护
        edge_frame = ttk.Frame(scroll_frame)
        edge_frame.pack(fill='x', pady=2, padx=0)
        self.cup_edge_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(edge_frame, text="边缘保护", variable=self.cup_edge_var,
                       command=self.cup_schedule_render).pack(side='left')
        
        # 边缘参数
        lo_frame = ttk.Frame(scroll_frame)
        lo_frame.pack(fill='x', pady=2, padx=0)
        ttk.Label(lo_frame, text="更黑阈值:").pack(side='left')
        self.cup_lo_var = tk.IntVar(value=40)
        self.cup_lo_label = ttk.Label(lo_frame, text="40")
        self.cup_lo_label.pack(side='right', padx=(5, 0))
        lo_slider = ttk.Scale(lo_frame, from_=0, to=255, orient='horizontal',
                             variable=self.cup_lo_var, command=lambda v: self.cup_update_lo_label())
        lo_slider.pack(side='right', fill='x', expand=True, padx=(0, 5))
        lo_slider.bind('<B1-Motion>', lambda e: self.cup_schedule_render())
        lo_slider.bind('<ButtonRelease-1>', lambda e: self.cup_schedule_render())
        
        # ===== 右侧预览面板 =====
        preview_frame = ttk.LabelFrame(right_frame, text="预览", padding="5")
        preview_frame.pack(fill='both', expand=False)
        
        # 创建两列预览布局（平行展示）
        preview_content = ttk.Frame(preview_frame)
        preview_content.pack()
        
        # 左侧：主图像预览（596×832 -> 缩放到 300×400）
        main_preview_frame = ttk.LabelFrame(preview_content, text="处理结果", padding="2")
        main_preview_frame.pack(side='left', padx=(0, 10))
        
        self.cup_preview_canvas = tk.Canvas(main_preview_frame, bg='white',
                                            relief='sunken', bd=1, width=300, height=400)
        self.cup_preview_canvas.pack()
        self.cup_preview_label = tk.PhotoImage()
        self.cup_canvas_item = self.cup_preview_canvas.create_image(0, 0, image=self.cup_preview_label, anchor='nw')
        
        # 右侧：最终打印效果预览（360×760 -> 缩放到 180×380）
        print_preview_frame = ttk.LabelFrame(preview_content, text="标签效果", padding="2")
        print_preview_frame.pack(side='left')
        
        self.cup_print_canvas = tk.Canvas(print_preview_frame, bg='#eaeaea',
                                         relief='sunken', bd=1, width=180, height=380)
        self.cup_print_canvas.pack()
        self.cup_print_label = tk.PhotoImage()
        self.cup_print_item = self.cup_print_canvas.create_image(0, 0, image=self.cup_print_label, anchor='nw')
        
        # ===== 按钮区域 =====
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill='x', pady=(10, 0))
        
        self.cup_export_btn = ttk.Button(button_frame, text="导出成品 PNG", 
                                        command=self.cup_export_image, state='disabled')
        self.cup_export_btn.pack(side='right', padx=(5, 0))
        
        self.cup_clear_btn = ttk.Button(button_frame, text="清空", command=self.cup_clear)
        self.cup_clear_btn.pack(side='right')
    
    def cup_select_image(self):
        """选择杯贴图片"""
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                self.cup_current_file = file_path
                self.cup_current_image = Image.open(file_path)
                self.cup_file_label.config(text=f"已选择: {os.path.basename(file_path)}", foreground="#000")
                self.cup_export_btn.config(state='normal')
                self.cup_schedule_render()
            except Exception as e:
                messagebox.showerror("错误", f"无法打开图片: {e}")
    
    def cup_update_scale_label(self):
        """更新缩放标签"""
        self.cup_scale_label.config(text=str(self.cup_scale_var.get()))
    
    def cup_update_grid_label(self):
        """更新网格标签"""
        self.cup_grid_label.config(text=str(self.cup_grid_var.get()))
    
    def cup_update_angle_label(self):
        """更新角度标签"""
        self.cup_angle_label.config(text=str(self.cup_angle_var.get()))
    
    def cup_update_gamma_label(self):
        """更新Gamma标签"""
        self.cup_gamma_label.config(text=f"{self.cup_gamma_var.get():.2f}")
    
    def cup_update_contrast_label(self):
        """更新对比度标签"""
        self.cup_contrast_label.config(text=str(self.cup_contrast_var.get()))
    
    def cup_update_lo_label(self):
        """更新Lo阈值标签"""
        self.cup_lo_label.config(text=str(self.cup_lo_var.get()))
    
    def cup_schedule_render(self):
        """计划渲染（防止频繁重新绘制）"""
        if not self.cup_current_image:
            return
        
        if self.cup_render_timer:
            self.root.after_cancel(self.cup_render_timer)
        
        self.cup_render_timer = self.root.after(300, self.cup_render)
    
    def cup_render(self):
        """渲染图像预览"""
        if not self.cup_current_image:
            return
        
        try:
            # 处理图像
            binary_array, orig_w, orig_h, real_scale = process_image(
                self.cup_current_image,
                mode=self.cup_mode_var.get(),
                canvas_width=596,
                canvas_height=832,
                scale_percent=self.cup_scale_var.get(),
                grid_size=self.cup_grid_var.get(),
                shape=self.cup_shape_var.get(),
                angle=self.cup_angle_var.get(),
                gamma=self.cup_gamma_var.get(),
                contrast=self.cup_contrast_var.get(),
                edge_protect=self.cup_edge_var.get(),
                lo_threshold=self.cup_lo_var.get(),
                hi_threshold=120,
                tau_threshold=60,
                dilate_iters=0,
                fs_serpentine=True
            )
            
            # 转换为PIL图像用于显示
            binary_img = Image.fromarray(binary_array, 'L')
            
            # 主预览框：缩放到300x400（对应Canvas宽高）
            # 保持596:832的比例 -> 300:400
            binary_img_display = binary_img.resize((300, 400), Image.Resampling.LANCZOS)
            
            # 转为PhotoImage
            photo = ImageTk.PhotoImage(binary_img_display)
            self.cup_canvas_images['main'] = photo
            self.cup_preview_canvas.itemconfig(self.cup_canvas_item, image=photo)
            
            # 生成打印预览（最终效果 - 360x760的标签模拟）
            print_preview = generate_print_preview(binary_array)
            
            # 打印预览框：缩放到180x380（对应Canvas宽高）
            # 保持360:760的比例 -> 180:380
            print_preview_display = print_preview.resize((180, 380), Image.Resampling.LANCZOS)
            
            # 转为PhotoImage
            print_photo = ImageTk.PhotoImage(print_preview_display)
            self.cup_canvas_images['print'] = print_photo
            self.cup_print_canvas.itemconfig(self.cup_print_item, image=print_photo)
            
            # 存储处理后的二值化图像供导出使用
            self.cup_processed_binary = binary_img
            
        except Exception as e:
            messagebox.showerror("错误", f"处理图像失败: {e}")
            import traceback
            traceback.print_exc()
    
    def cup_export_image(self):
        """导出成品PNG - 导出最后修改的处理结果"""
        if not hasattr(self, 'cup_processed_binary') or self.cup_processed_binary is None:
            messagebox.showwarning("提示", "请先处理图像")
            return
        
        if not self.cup_current_file:
            messagebox.showwarning("提示", "没有选择源文件")
            return
        
        # 生成默认文件名
        source_filename = os.path.splitext(os.path.basename(self.cup_current_file))[0]
        default_filename = f"{source_filename}_596x832_bw.png"
        
        file_path = filedialog.asksaveasfilename(
            title="导出处理后的图片",
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png"), ("所有文件", "*.*")],
            initialfile=default_filename
        )
        
        if file_path:
            try:
                # 导出当前处理后的二值化图像
                self.cup_processed_binary.save(file_path, 'PNG')
                messagebox.showinfo("导出成功", f"图片已保存到:\n{file_path}\n\n图片尺寸: 596×832 像素")
            except Exception as e:
                messagebox.showerror("导出失败", f"保存失败: {e}")
    
    def cup_clear(self):
        """清空杯贴数据"""
        self.cup_current_file = None
        self.cup_current_image = None
        self.cup_file_label.config(text="点击选择文件或拖放", foreground="#999")
        self.cup_preview_canvas.delete('all')
        self.cup_print_canvas.delete('all')
        self.cup_export_btn.config(state='disabled')
        if hasattr(self, 'cup_processed_binary'):
            self.cup_processed_binary = None

    def get_verification_code(self):
        """获取验证码"""
        # 检查是否在冷却期
        if self.cooldown_seconds > 0:
            messagebox.showwarning("提示", f"请等待 {self.cooldown_seconds} 秒后再试")
            return
        
        mobile = self.mobile_entry.get().strip()
        if not mobile:
            messagebox.showerror("错误", "请输入手机号")
            return
        
        if len(mobile) != 11:
            messagebox.showerror("错误", "请输入正确的手机号")
            return
        
        # 启动冷却
        self.start_cooldown()
        
        threading.Thread(target=self.send_verification_code, args=(mobile,), daemon=True).start()
    
    def start_cooldown(self):
        """开始验证码冷却倒计时"""
        self.cooldown_seconds = 120
        self.update_cooldown_button()
    
    def update_cooldown_button(self):
        """更新冷却按钮状态"""
        if self.cooldown_seconds > 0:
            self.get_code_btn.config(text=f"重新获取({self.cooldown_seconds}s)", state='disabled')
            self.cooldown_seconds -= 1
            # 1秒后再次调用
            self.cooldown_timer = self.root.after(1000, self.update_cooldown_button)
        else:
            self.get_code_btn.config(text="获取验证码", state='normal')
            if self.cooldown_timer:
                self.root.after_cancel(self.cooldown_timer)
                self.cooldown_timer = None
    
    
    def send_verification_code(self, mobile, ticket=None, randstr=None):
        """发送验证码"""
        try:
            self.current_mobile = mobile
            encrypted_mobile = heytea_cryption.encrypt_heytea_mobile(mobile)
            
            headers = HEYTEA_HEADER.copy()
            headers["current-page"] = "/pages/login/login_app/index"
            endpoint = f"{HEYTEA_API_BASE}/api/service-member/openapi/vip/user/sms/verifiyCode/send"
            
            # 构建请求参数
            request_data = {
                "client": "app",
                "brandId": "1000001",
                "mobile": encrypted_mobile,
                "zone": "86",
                "cryptoLevel": 2,
                "ticketFrom": "min"
            }
            
            # 如果有验证码票据，添加到请求中
            if ticket and randstr:
                request_data["ticket"] = ticket
                request_data["randstr"] = randstr

            response = requests.post(endpoint, headers=headers, json=request_data)
            print(response.text)
            
            resp = response.json()
            
            # 检查是否需要人机验证
            if resp.get("code") == 4005021:                
                # 在主线程中提示用户
                self.root.after(0, lambda: messagebox.showinfo("提示", "需要进行人机验证"))
                
                # 显示验证码窗口
                self.root.after(0, lambda: show_captcha(
                    CAPTCHA_APP_ID,
                    on_success=self.on_captcha_success,
                    on_close=self.on_captcha_close
                ))
                return
            
            # 检查其他错误
            if resp.get("code") != 0 or resp.get("message") != "SUCCESS":
                raise Exception(resp.get("message", "未知错误"))
            
            # 发送成功
            self.root.after(0, lambda: messagebox.showinfo("成功", "验证码已发送"))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"发送验证码失败: {msg}"))
    
    def on_captcha_success(self, ticket, randstr):
        """验证码验证成功的回调"""
        print(f"Captcha success - ticket: {ticket}, randstr: {randstr}")
        self.captcha_ticket = ticket
        self.captcha_randstr = randstr
        
        # 验证成功后重新发送验证码
        if self.current_mobile:
            threading.Thread(
                target=self.send_verification_code,
                args=(self.current_mobile, ticket, randstr),
                daemon=True
            ).start()
    
    def on_captcha_close(self):
        """验证码窗口关闭的回调"""
        print("Captcha window closed")
        self.root.after(0, lambda: messagebox.showwarning("提示", "已取消人机验证"))
    
    def login_with_sms(self):
        """使用短信验证码登录"""
        mobile = self.mobile_entry.get().strip()
        code = self.code_entry.get().strip()
        
        if not mobile or not code:
            messagebox.showerror("错误", "请输入手机号和验证码")
            return
        
        # 这里调用你实现的登录接口
        threading.Thread(target=self.do_login_with_sms, args=(mobile, code), daemon=True).start()
    
    def do_login_with_sms(self, mobile, code):
        """执行登录（需要你实现具体逻辑）"""
        try:
            encrypted_mobile = heytea_cryption.encrypt_heytea_mobile(mobile)

            headers = HEYTEA_HEADER.copy()
            headers["current-page"] = "/pages/login/login_app/verify_code/index"
            endpoint = f"{HEYTEA_API_BASE}/api/service-login/openapi/vip/user/login_v1"

            response = requests.post(endpoint, headers=headers, json={
                "channel":"A",
                "client":"app",
                "loginType":"APP_CODE",
                "brand":"1000001",
                "phone":encrypted_mobile,
                "email":None,
                "smsCode":code,
                "zone":"86",
                "cryptoLevel":2,
                "ticketFrom":"min"
            })

            print(response.text)
            resp = response.json()

            if resp.get("code") != 0 or resp.get("message") != "SUCCESS":
                raise Exception(resp.get("message", "未知错误"))

            token = resp.get("data", {}).get("token")
            
            self.token = token
            self.root.after(0, self.on_login_success)
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"登录失败: {msg}"))
    
    def login_with_key(self):
        """使用Token直接登录"""
        token = self.token_entry.get().strip()
        
        if not token:
            messagebox.showerror("错误", "请输入Token")
            return
        
        self.token = token
        self.on_login_success()
    
    def on_login_success(self):
        """登录成功后的处理"""

        self.get_user_info()

        if self.user_main_id:
            self.status_label.config(text=f"已登录 {self.nickname} ({self.user_main_id})", foreground="green")
            self.upload_btn.config(state='normal' if self.selected_image_path else 'disabled')
            self.logout_btn.config(state='normal')  # 启用退出登录按钮
            
            # 保存配置
            self.save_config()
            
            messagebox.showinfo("成功", "登录成功！")
        else:
            messagebox.showinfo("成功", "登录失败，无法获取用户信息！")
    
    def logout(self):
        """退出登录"""
        result = messagebox.askyesno("确认", "确定要退出登录吗？")
        if result:
            # 清空token和用户信息
            self.token = None
            self.nickname = None
            self.user_main_id = None
            self.selected_image_path = None
            
            # 更新UI状态
            self.status_label.config(text="未登录", foreground="red")
            self.logout_btn.config(state='disabled')
            self.upload_btn.config(state='disabled')
            self.token_entry.delete(0, tk.END)
            self.preview_label.config(image='', text="未选择图片")
            self.upload_status_label.config(text="")
            
            # 删除配置文件
            try:
                if os.path.exists(self.config_file):
                    os.remove(self.config_file)
            except Exception as e:
                print(f"删除配置文件失败: {e}")
            
            messagebox.showinfo("提示", "已退出登录")

    def get_user_info(self):
        """获取用户信息"""        
        try:
            headers = HEYTEA_HEADER.copy()
            headers["authorization"] = f"Bearer {self.token}"
            headers["current-page"] = "/pages/my/index"
            endpoint = f"{HEYTEA_API_BASE}/api/service-member/vip/user/info"
            
            response = requests.get(endpoint, headers=headers)
            print(response.text)
            resp = response.json()
            
            if resp.get("code") != 0 or resp.get("message") != "SUCCESS":
                raise Exception(resp.get("message", "未知错误"))
            
            user_info = resp.get("data", {})

            user_info = heytea_cryption.decrypt_response_data(user_info, is_app=True)
            user_info = json.loads(user_info)

            self.nickname = user_info.get("name")
            self.user_main_id = user_info.get("user_main_id")
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("错误", f"获取用户信息失败: {error_msg}")
    
    def select_image(self):
        """选择图片"""
        file_path = filedialog.askopenfilename(
            title="选择图片 (仅支持PNG格式)",
            filetypes=[
                ("PNG图片", "*.png"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            try:
                # 先检查图片格式
                if not file_path.lower().endswith('.png'):
                    messagebox.showerror(
                        "图片格式错误",
                        "只支持PNG格式的图片！"
                    )
                    return
                
                # 检查图片尺寸
                image = Image.open(file_path)
                if image.size != (596, 832):
                    messagebox.showerror(
                        "图片尺寸错误",
                        f"当前图片尺寸为 {image.width}x{image.height}\n必须使用 596x832 尺寸的图片！"
                    )
                    return
                
                # 尺寸正确，保存路径并显示预览
                self.selected_image_path = file_path
                self.show_image_preview(file_path)
                
                if self.token:
                    self.upload_btn.config(state='normal')
            except Exception as e:
                messagebox.showerror("错误", f"无法读取图片: {str(e)}")
    
    def show_image_preview(self, image_path):
        """显示图片预览"""
        try:
            image = Image.open(image_path)
            
            # 按比例调整图片大小以适应预览框（保持596:832的比例）
            display_width = 150 * self.scale_factor
            display_height = int(display_width * 832 / 596)
            
            # 如果高度超出，则按高度限制
            if display_height > 420:
                display_height = 420
                display_width = int(display_height * 596 / 832)
            
            image.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # 保持引用
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {str(e)}")
    
    def upload_image(self):
        """上传图片"""
        if not self.token:
            messagebox.showerror("错误", "请先登录")
            return
        
        if not self.selected_image_path:
            messagebox.showerror("错误", "请先选择图片")
            return
        
        self.upload_status_label.config(text="上传中...", foreground="blue")
        self.upload_btn.config(state='disabled')
        
        threading.Thread(target=self.do_upload_image, daemon=True).start()
    
    def do_upload_image(self):
        """执行上传（需要你实现具体逻辑）"""
        try:
            with open(self.selected_image_path, 'rb') as f:
                image_data = f.read()
            # response = 调用上传API(self.token, image_data)

            timestamp = int(time.time()*1000)
            sign = heytea_cryption.timestamp_sign(self.user_main_id, timestamp)
            
            # 构建带参数的URL
            endpoint = f"{HEYTEA_API_BASE}/api/service-cps/user/diy?sign={sign}&t={timestamp}"

            # 准备multipart/form-data
            files = {
                'file': ('image.png', image_data, 'image/png')
            }
            
            data = {
                'width': '596',
                'height': '832'
            }

            header = HEYTEA_HEADER.copy()
            header["Authorization"] = f"Bearer {self.token}"
            # 移除Content-Type，让requests自动设置multipart/form-data
            if 'Content-Type' in header:
                del header['Content-Type']

            response = requests.post(endpoint, headers=header, files=files, data=data)

            print(response.text)
            resp = response.json()

            if resp.get("code") != 0 or resp.get("message") != "SUCCESS":
                raise Exception(resp.get("message", "未知错误"))

            self.root.after(0, lambda: self.upload_status_label.config(text="上传成功！", foreground="green"))
            self.root.after(0, lambda: self.upload_btn.config(state='normal'))
            self.root.after(0, lambda: messagebox.showinfo("成功", "图片上传成功！"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.upload_status_label.config(text="上传失败", foreground="red"))
            self.root.after(0, lambda: self.upload_btn.config(state='normal'))
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"上传失败: {msg}"))
    
    def save_config(self):
        """保存配置到文件"""
        if not self.save_login_var.get():
            # 如果不勾选保存，则删除配置文件
            try:
                if os.path.exists(self.config_file):
                    os.remove(self.config_file)
            except:
                pass
            return
        
        try:
            config = {
                "token": self.token
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def load_config(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.token = config.get("token")
                
                if self.token:
                    # 自动填充token输入框
                    self.token_entry.insert(0, self.token)
                    # 自动登录（会从API获取用户信息）
                    self.on_login_success()
                    self.save_login_var.set(True)
        except Exception as e:
            print(f"加载配置失败: {e}")


def main():
    # 检查是否是captcha子进程模式
    if len(sys.argv) > 1 and sys.argv[1] == '--captcha':
        if len(sys.argv) < 3:
            print(json.dumps({'success': False, 'error': 'Missing captcha_app_id'}), flush=True)
            sys.exit(1)
        
        captcha_app_id = sys.argv[2]
        try:
            run_captcha_window(captcha_app_id)
        except Exception as e:
            print(json.dumps({'success': False, 'error': str(e)}), flush=True)
            sys.exit(1)
        return
    
    # 启用高DPI支持（必须在创建窗口之前调用）
    scale_factor = 1.0
    
    # 检测操作系统类型
    import platform
    system = platform.system()
    
    try:
        from ctypes import windll
        # 尝试使用 Windows 10/11 的 DPI 感知 API
        try:
            windll.shcore.SetProcessDpiAwareness(2)  # 2 = PROCESS_PER_MONITOR_DPI_AWARE_V2
        except:
            windll.shcore.SetProcessDpiAwareness(1)  # 1 = PROCESS_SYSTEM_DPI_AWARE
        
        # 获取屏幕缩放比例
        try:
            scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100.0
        except:
            pass
    except:
        try:
            # 旧版 Windows 的 DPI 感知
            from ctypes import windll
            windll.user32.SetProcessDPIAware()
        except:
            pass

    # 正常运行主程序
    root = tk.Tk()

    # 根据缩放比例调整窗口大小
    base_width = 1400
    base_height = 1100
    
    # 对于 macOS，调整基础尺寸
    if system == "Darwin":
        base_height = 1150  # macOS 需要更大的高度
    
    scaled_width = int(base_width * scale_factor)
    scaled_height = int(base_height * scale_factor)
    root.geometry(f"{scaled_width}x{scaled_height}")
    root.minsize(800, 600)  # 设置最小窗口尺寸
    
    app = HeyTeaUploader(root, scale_factor)
    root.mainloop()


if __name__ == "__main__":
    main()
