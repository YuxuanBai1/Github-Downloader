import sys
import os
import threading
import time
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QSlider, QPushButton, QTextEdit,
    QProgressBar, QFileDialog, QFrame, QGridLayout,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import json

class DownloadThread(QThread):
    """下载线程类"""
    progress_signal = pyqtSignal(int, int, int)
    log_signal = pyqtSignal(str, str)
    speed_signal = pyqtSignal(float)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, url, save_path, threads=4):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.threads = threads
        self.is_running = True
        self.total_size = 0
        self.downloaded_size = 0
        self.start_time = None
        self.last_downloaded = 0
        
    def run(self):
        try:
            self.start_time = time.time()
            response = requests.head(self.url, allow_redirects=True, timeout=10)
            if 'Content-Length' in response.headers:
                self.total_size = int(response.headers['Content-Length'])
                self.log_signal.emit(f"文件大小: {self.format_size(self.total_size)}", "info")
            else:
                self.log_signal.emit("无法获取文件大小", "error")
                self.finished_signal.emit(False, "无法获取文件大小")
                return
            
            content_disposition = response.headers.get('Content-Disposition', '')
            filename = None
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"\'')
            
            self.log_signal.emit(f"开始下载: {os.path.basename(self.url) if not filename else filename}", "info")
            
            part_size = self.total_size // self.threads
            threads_list = []
            
            for i in range(self.threads):
                start = i * part_size
                end = (i + 1) * part_size - 1 if i != self.threads - 1 else self.total_size - 1
                thread = threading.Thread(target=self.download_part, args=(i, start, end))
                threads_list.append(thread)
                thread.start()
            
            for thread in threads_list:
                thread.join()
            
            if self.is_running:
                try:
                    self.log_signal.emit("正在合并临时文件...", "info")
                    with open(self.save_path, 'wb') as final_file:
                        for i in range(self.threads):
                            temp_file = f"{self.save_path}.part{i}"
                            if os.path.exists(temp_file):
                                with open(temp_file, 'rb') as f:
                                    final_file.write(f.read())
                                os.remove(temp_file)
                    
                    elapsed_time = time.time() - self.start_time
                    self.log_signal.emit(f"下载完成! 用时: {elapsed_time:.1f}秒", "success")
                    self.finished_signal.emit(True, "下载完成")
                except Exception as e:
                    self.log_signal.emit(f"合并文件错误: {str(e)}", "error")
                    self.finished_signal.emit(False, f"合并文件错误: {str(e)}")
            else:
                self.log_signal.emit("下载已取消", "warning")
                self.finished_signal.emit(False, "下载已取消")
                for i in range(self.threads):
                    temp_file = f"{self.save_path}.part{i}"
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                
        except Exception as e:
            self.log_signal.emit(f"下载错误: {str(e)}", "error")
            self.finished_signal.emit(False, f"下载错误: {str(e)}")
    
    def download_part(self, thread_id, start, end):
        """下载文件的一部分"""
        headers = {'Range': f'bytes={start}-{end}'}
        try:
            response = requests.get(self.url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            temp_file = f"{self.save_path}.part{thread_id}"
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk and self.is_running:
                        f.write(chunk)
                        self.downloaded_size += len(chunk)
                        progress = int((self.downloaded_size / self.total_size) * 100) if self.total_size > 0 else 0
                        self.progress_signal.emit(progress, self.downloaded_size, self.total_size)
                    else:
                        break
            
        except Exception as e:
            self.log_signal.emit(f"线程{thread_id+1}下载错误: {str(e)}", "error")
            self.is_running = False
    
    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def stop(self):
        """停止下载"""
        self.is_running = False

class SimpleHeaderWidget(QFrame):
    """简洁标题栏组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("GitHub Downloader")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            font-family: 'Microsoft YaHei';
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()

class SectionTitle(QLabel):
    """区域标题组件"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            font-family: 'Microsoft YaHei';
            margin-top: 10px;
            margin-bottom: 10px;
        """)

class UrlInputWidget(QWidget):
    """URL输入组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.title = SectionTitle("下载链接")
        layout.addWidget(self.title)
        
        url_layout = QHBoxLayout()
        url_layout.setSpacing(10)
        
        self.prefix_combo = QComboBox()
        self.prefix_combo.addItem("ghfast.top", "https://ghfast.top/")
        self.prefix_combo.addItem("gh-proxy.net", "https://gh-proxy.net/")
        self.prefix_combo.addItem("直连", "")
        self.prefix_combo.setFixedWidth(200)
        self.prefix_combo.setStyleSheet("""
            QComboBox {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
                padding: 10px 15px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background: white;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """)
        
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("输入GitHub文件或仓库链接...")
        self.url_edit.setStyleSheet("""
            QLineEdit {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
                padding: 10px 15px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                padding: 9px 14px;
            }
        """)
        
        url_layout.addWidget(self.prefix_combo)
        url_layout.addWidget(self.url_edit)
        
        layout.addLayout(url_layout)
        
        tip_label = QLabel("示例: https://github.com/YuxuanBai1/Luogu-Plus/releases/download/v1.0.1/Luogu.Plus.crx")
        tip_label.setStyleSheet("""
            font-size: 12px;
            color: #7f8c8d;
            font-family: 'Microsoft YaHei';
            margin-top: 5px;
        """)
        layout.addWidget(tip_label)

class SettingsWidget(QWidget):
    """设置组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.title = SectionTitle("下载设置")
        layout.addWidget(self.title)
        
        # 线程数设置
        thread_layout = QHBoxLayout()
        thread_layout.setSpacing(10)
        
        thread_label = QLabel("下载线程:")
        thread_label.setStyleSheet("""
            font-size: 14px;
            color: #34495e;
            font-family: 'Microsoft YaHei';
        """)
        thread_label.setFixedWidth(70)
        
        self.thread_slider = QSlider(Qt.Horizontal)
        self.thread_slider.setMinimum(1)
        self.thread_slider.setMaximum(16)
        self.thread_slider.setValue(4)
        self.thread_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #ecf0f1;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -7px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #2980b9;
            }
        """)
        
        self.thread_value_label = QLabel("4")
        self.thread_value_label.setAlignment(Qt.AlignCenter)
        self.thread_value_label.setFixedWidth(40)
        self.thread_value_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #3498db;
            font-family: 'Microsoft YaHei';
            padding: 4px 8px;
            background: #ecf0f1;
            border-radius: 4px;
        """)
        
        self.thread_slider.valueChanged.connect(
            lambda v: self.thread_value_label.setText(str(v))
        )
        
        thread_layout.addWidget(thread_label)
        thread_layout.addWidget(self.thread_slider)
        thread_layout.addWidget(self.thread_value_label)
        layout.addLayout(thread_layout)
        
        # 保存路径设置
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)
        
        path_label = QLabel("保存位置:")
        path_label.setStyleSheet("""
            font-size: 14px;
            color: #34495e;
            font-family: 'Microsoft YaHei';
        """)
        path_label.setFixedWidth(70)
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择保存文件夹...")
        self.path_edit.setReadOnly(True)
        self.path_edit.setStyleSheet("""
            QLineEdit {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
                padding: 8px 15px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background: #f8f9fa;
            }
        """)
        
        self.browse_button = QPushButton("浏览")
        self.browse_button.setFixedWidth(80)
        self.browse_button.setStyleSheet("""
            QPushButton {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 6px;
                background: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
            }
            QPushButton:hover {
                background: #d5dbdb;
            }
            QPushButton:pressed {
                background: #bfc9ca;
            }
        """)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit, 1)
        path_layout.addWidget(self.browse_button)
        layout.addLayout(path_layout)

class SpeedWidget(QWidget):
    """速度显示组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 速度显示
        self.speed_label = QLabel("0 KB/s")
        self.speed_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #3498db;
            font-family: 'Microsoft YaHei';
        """)
        self.speed_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.speed_label)
        
        # 进度标签
        self.progress_label = QLabel("等待下载...")
        self.progress_label.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
            font-family: 'Microsoft YaHei';
        """)
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

class DownloadProgressWidget(QWidget):
    """下载进度组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 状态显示
        status_layout = QHBoxLayout()
        
        title_label = QLabel("下载进度")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            font-family: 'Microsoft YaHei';
        """)
        
        self.status_label = QLabel("等待开始")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
            font-family: 'Microsoft YaHei';
        """)
        self.status_label.setAlignment(Qt.AlignRight)
        
        status_layout.addWidget(title_label)
        status_layout.addStretch()
        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #ecf0f1;
                height: 20px;
                border-radius: 10px;
                text-align: center;
                font-family: 'Microsoft YaHei';
                font-size: 12px;
                color: #2c3e50;
            }
            QProgressBar::chunk {
                background: #3498db;
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 进度细节
        detail_layout = QHBoxLayout()
        
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("""
            font-size: 13px;
            color: #7f8c8d;
            font-family: 'Microsoft YaHei';
        """)
        
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("""
            font-size: 13px;
            color: #7f8c8d;
            font-family: 'Microsoft YaHei';
        """)
        
        detail_layout.addWidget(self.detail_label)
        detail_layout.addStretch()
        detail_layout.addWidget(self.time_label)
        layout.addLayout(detail_layout)

class ControlButtonsWidget(QWidget):
    """控制按钮组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        
        self.start_button = QPushButton("开始下载")
        self.start_button.setFixedHeight(45)
        self.start_button.setStyleSheet("""
            QPushButton {
                font-family: 'Microsoft YaHei';
                font-size: 16px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 8px;
                background: #2ecc71;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background: #27ae60;
            }
            QPushButton:pressed {
                background: #229954;
            }
            QPushButton:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        self.stop_button = QPushButton("停止下载")
        self.stop_button.setFixedHeight(45)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                font-family: 'Microsoft YaHei';
                font-size: 16px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 8px;
                background: #ecf0f1;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
            }
            QPushButton:hover {
                background: #e74c3c;
                color: white;
                border-color: #e74c3c;
            }
            QPushButton:pressed {
                background: #c0392b;
                border-color: #c0392b;
            }
            QPushButton:disabled {
                background: #ecf0f1;
                color: #bdc3c7;
                border-color: #ecf0f1;
            }
        """)
        
        layout.addStretch()
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addStretch()

class LogWidget(QWidget):
    """日志组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 日志标题和清空按钮
        title_layout = QHBoxLayout()
        
        title_label = QLabel("下载日志")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            font-family: 'Microsoft YaHei';
        """)
        
        self.clear_button = QPushButton("清空日志")
        self.clear_button.setFixedHeight(30)
        self.clear_button.setStyleSheet("""
            QPushButton {
                font-family: 'Microsoft YaHei';
                font-size: 13px;
                padding: 6px 16px;
                border-radius: 6px;
                background: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
            }
            QPushButton:hover {
                background: #d5dbdb;
            }
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.clear_button)
        layout.addLayout(title_layout)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Microsoft YaHei', monospace;
                font-size: 12px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background: #f8f9fa;
                padding: 10px;
                margin-top: 10px;
            }
            QScrollBar:vertical {
                background: #ecf0f1;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #bdc3c7;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #95a5a6;
            }
        """)
        layout.addWidget(self.log_text)

class GithubDownloader(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        current_directory = os.path.dirname(os.path.abspath(__file__))  
        self.download_thread = None
        self.download_history = []
        self.load_history()
        self.setWindowIcon(QIcon(current_directory+'/app.ico'))
        self.init_ui()
        
    def load_history(self):
        """加载下载历史"""
        try:
            if os.path.exists("download_history.json"):
                with open("download_history.json", "r", encoding="utf-8") as f:
                    self.download_history = json.load(f)
        except:
            self.download_history = []
    
    def save_history(self):
        """保存下载历史"""
        try:
            with open("download_history.json", "w", encoding="utf-8") as f:
                json.dump(self.download_history[-100:], f, ensure_ascii=False, indent=2)
        except:
            pass
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('GitHub Downloader')
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)
        
        self.setStyleSheet("""
            QMainWindow {
                background: #f8f9fa;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 15, 20, 15)
        
        # 标题栏
        self.header = SimpleHeaderWidget()
        main_layout.addWidget(self.header)
        
        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #ecf0f1;")
        main_layout.addWidget(line)
        
        content_layout = QGridLayout()
        content_layout.setSpacing(15)
        
        # 第一行：速度显示
        self.speed_widget = SpeedWidget()
        content_layout.addWidget(self.speed_widget, 0, 0, 1, 2)
        
        # 第二行：URL输入
        self.url_widget = UrlInputWidget()
        content_layout.addWidget(self.url_widget, 1, 0, 1, 2)
        
        # 第三行：进度组件和设置组件
        self.progress_widget = DownloadProgressWidget()
        content_layout.addWidget(self.progress_widget, 2, 0)
        
        self.settings_widget = SettingsWidget()
        content_layout.addWidget(self.settings_widget, 2, 1)
        
        # 控制按钮
        self.control_widget = ControlButtonsWidget()
        content_layout.addWidget(self.control_widget, 3, 0, 1, 2)
        
        # 日志组件
        self.log_widget = LogWidget()
        content_layout.addWidget(self.log_widget, 4, 0, 1, 2)
        
        main_layout.addLayout(content_layout)
        
        self.connect_signals()
        
    def connect_signals(self):
        """连接信号和槽"""
        self.settings_widget.browse_button.clicked.connect(self.browse_folder)
        self.control_widget.start_button.clicked.connect(self.start_download)
        self.control_widget.stop_button.clicked.connect(self.stop_download)
        self.log_widget.clear_button.clicked.connect(
            lambda: self.log_widget.log_text.clear()
        )
        
        default_path = os.path.expanduser("~/Downloads")
        self.settings_widget.path_edit.setText(default_path)
        
    def browse_folder(self):
        """选择保存文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择保存文件夹", 
                                                 self.settings_widget.path_edit.text())
        if folder:
            self.settings_widget.path_edit.setText(folder)
            
    def start_download(self):
        """开始下载"""
        original_url = self.url_widget.url_edit.text().strip()
        if not original_url:
            self.add_log("请输入下载链接", "error")
            return
            
        prefix = self.url_widget.prefix_combo.currentData()
        threads = self.settings_widget.thread_slider.value()
        save_folder = self.settings_widget.path_edit.text()
        
        if not save_folder or not os.path.exists(save_folder):
            self.add_log("请选择有效的保存文件夹", "error")
            return
            
        # 构建加速链接
        if original_url.startswith('https://github.com/'):
            accelerated_url = prefix + original_url[8:]
        elif original_url.startswith('https://raw.githubusercontent.com/'):
            accelerated_url = prefix + original_url[8:]
        elif original_url.startswith('https://codeload.github.com/'):
            accelerated_url = prefix + original_url[8:]
        else:
            self.add_log("不支持的链接格式", "error")
            return
            
        # 生成文件名
        file_name = os.path.basename(original_url.split('?')[0])
        if not file_name:
            file_name = f"download_{int(time.time())}.zip"
        save_path = os.path.join(save_folder, file_name)
        
        # 更新UI状态
        self.control_widget.start_button.setEnabled(False)
        self.control_widget.stop_button.setEnabled(True)
        self.progress_widget.status_label.setText("下载中...")
        self.progress_widget.status_label.setStyleSheet("""
            font-size: 14px;
            color: #f39c12;
            font-family: 'Microsoft YaHei';
        """)
        
        self.add_log(f"开始下载: {file_name}", "info")
        self.add_log(f"加速链接: {accelerated_url}", "info")
        
        # 创建下载线程
        self.download_thread = DownloadThread(accelerated_url, save_path, threads)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.log_signal.connect(self.add_log)
        self.download_thread.finished_signal.connect(self.download_finished)
        
        # 手动计算速度
        self.last_downloaded = 0
        self.last_time = time.time()
        
        # 启动定时器计算速度
        from PyQt5.QtCore import QTimer
        self.speed_timer = QTimer()
        self.speed_timer.timeout.connect(self.calculate_speed)
        self.speed_timer.start(1000)
        
        self.download_thread.start()
        
    def calculate_speed(self):
        """计算下载速度"""
        if self.download_thread and self.download_thread.isRunning():
            if hasattr(self.download_thread, 'downloaded_size'):
                current = self.download_thread.downloaded_size
                speed_kb = (current - self.last_downloaded) / 1024
                self.last_downloaded = current
                
                if speed_kb < 1024:
                    self.speed_widget.speed_label.setText(f"{speed_kb:.1f} KB/s")
                else:
                    speed_mb = speed_kb / 1024
                    self.speed_widget.speed_label.setText(f"{speed_mb:.1f} MB/s")
                    
                # 更新进度标签
                if hasattr(self.download_thread, 'total_size') and self.download_thread.total_size > 0:
                    progress = int((current / self.download_thread.total_size) * 100)
                    self.speed_widget.progress_label.setText(f"进度: {progress}%")
        
    def stop_download(self):
        """停止下载"""
        if self.download_thread:
            self.add_log("正在停止下载...", "warning")
            self.download_thread.stop()
            if hasattr(self, 'speed_timer'):
                self.speed_timer.stop()
            
    def update_progress(self, progress, downloaded, total):
        """更新下载进度"""
        self.progress_widget.progress_bar.setValue(progress)
        
        downloaded_str = self.format_size(downloaded)
        total_str = self.format_size(total)
        
        self.progress_widget.detail_label.setText(
            f"{downloaded_str} / {total_str} ({progress}%)"
        )
        
    def add_log(self, message, msg_type="info"):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        
        colors = {
            "info": "#3498db",
            "error": "#e74c3c",
            "success": "#2ecc71",
            "warning": "#f39c12"
        }
        color = colors.get(msg_type, "#7f8c8d")
        
        log_html = f'<span style="color:#95a5a6;">[{timestamp}]</span> '
        log_html += f'<span style="color:{color};">{message}</span>'
        
        self.log_widget.log_text.append(log_html)
        
        self.log_widget.log_text.verticalScrollBar().setValue(
            self.log_widget.log_text.verticalScrollBar().maximum()
        )
        
    def download_finished(self, success, message):
        """下载完成处理"""
        # 停止速度计时器
        if hasattr(self, 'speed_timer'):
            self.speed_timer.stop()
            
        self.control_widget.start_button.setEnabled(True)
        self.control_widget.stop_button.setEnabled(False)
        
        if success:
            self.progress_widget.status_label.setText("下载完成")
            self.progress_widget.status_label.setStyleSheet("""
                font-size: 14px;
                color: #2ecc71;
                font-family: 'Microsoft YaHei';
            """)
            self.progress_widget.progress_bar.setValue(100)
            
            self.speed_widget.speed_label.setText("完成")
            self.speed_widget.progress_label.setText("下载完成")
        else:
            self.progress_widget.status_label.setText("下载失败")
            self.progress_widget.status_label.setStyleSheet("""
                font-size: 14px;
                color: #e74c3c;
                font-family: 'Microsoft YaHei';
            """)
            self.speed_widget.speed_label.setText("0 KB/s")
            self.speed_widget.progress_label.setText("下载失败")
            
        if success:
            self.download_history.append({
                "url": self.url_widget.url_edit.text(),
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "size": self.download_thread.total_size if self.download_thread else 0
            })
            self.save_history()
            
    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.download_thread and self.download_thread.isRunning():
            self.add_log("正在停止下载并关闭程序...", "warning")
            self.download_thread.stop()
        if hasattr(self, 'speed_timer'):
            self.speed_timer.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用程序字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = GithubDownloader()
    window.show()
    
    sys.exit(app.exec_())