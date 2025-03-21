from O365 import Account
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import requests
import webbrowser
import webdav3.client as webdav
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox

load_dotenv()

class CloudSync:
    def __init__(self):
        # OneDrive设置
        self.client_id = os.getenv('ONEDRIVE_CLIENT_ID')
        self.client_secret = os.getenv('ONEDRIVE_CLIENT_SECRET')
        self.onedrive_enabled = bool(self.client_id and self.client_secret)
        
        # WebDAV设置 - 默认使用坚果云
        self.webdav_url = os.getenv('WEBDAV_URL', 'https://dav.jianguoyun.com/dav/')
        self.webdav_username = os.getenv('WEBDAV_USERNAME', 'oxyg.rj@outlook.com')
        self.webdav_password = os.getenv('WEBDAV_PASSWORD', 'aqt4mm9yzge3nrb2')
        self.webdav_enabled = True  # 默认启用WebDAV
        
        # 默认备份目标
        self.backup_target = os.getenv('DEFAULT_BACKUP_TARGET', 'webdav')
        
        # 初始化OneDrive客户端
        if self.onedrive_enabled:
            self.account = Account((self.client_id, self.client_secret))
        else:
            self.account = None
        
        # 初始化WebDAV客户端
        self.init_webdav_client()
            
    def init_webdav_client(self):
        """初始化WebDAV客户端"""
        # 确保URL末尾有斜杠
        webdav_url = self.webdav_url
        
        # 确保URL包含协议
        if not (webdav_url.startswith('http://') or webdav_url.startswith('https://')):
            webdav_url = 'https://' + webdav_url
            
        # 确保URL末尾有斜杠
        if not webdav_url.endswith('/'):
            webdav_url = webdav_url + '/'
            
        options = {
            'webdav_hostname': webdav_url,
            'webdav_login': self.webdav_username,
            'webdav_password': self.webdav_password
        }
        self.webdav_client = webdav.Client(options)
        
    def setup_webdav(self, url, username, password):
        """设置WebDAV参数"""
        # 确保URL包含协议
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
            
        self.webdav_url = url
        self.webdav_username = username
        self.webdav_password = password
        self.webdav_enabled = True
        
        # 保存到环境变量
        with open('.env', 'r') as f:
            env_content = f.read()
            
        # 检查是否已存在WebDAV配置
        if 'WEBDAV_URL' in env_content:
            # 更新现有配置
            lines = env_content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('WEBDAV_URL='):
                    new_lines.append(f'WEBDAV_URL={url}')
                elif line.startswith('WEBDAV_USERNAME='):
                    new_lines.append(f'WEBDAV_USERNAME={username}')
                elif line.startswith('WEBDAV_PASSWORD='):
                    new_lines.append(f'WEBDAV_PASSWORD={password}')
                else:
                    new_lines.append(line)
            new_env_content = '\n'.join(new_lines)
        else:
            # 添加新配置
            new_env_content = env_content + '\n\n# WebDAV配置\n'
            new_env_content += f'WEBDAV_URL={url}\n'
            new_env_content += f'WEBDAV_USERNAME={username}\n'
            new_env_content += f'WEBDAV_PASSWORD={password}\n'
            
        with open('.env', 'w') as f:
            f.write(new_env_content)
            
        # 重新初始化WebDAV客户端
        self.init_webdav_client()
        return True
        
    def authenticate_onedrive(self, parent_widget=None):
        """认证OneDrive，并显示登录窗口"""
        if parent_widget:
            QMessageBox.warning(parent_widget, "OneDrive功能已禁用", "请使用WebDAV进行云存储同步")
        return False
            
    def backup_data(self, data, parent_widget=None):
        """备份数据到云存储"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.json'
        json_data = json.dumps(data)
        
        success = False
        error_msg = ""
        
        # 使用默认备份目标
        target = self.backup_target
        
        # 根据target参数选择备份到哪个存储
        if target == 'onedrive':
            # 尝试OneDrive备份
            if self.onedrive_enabled:
                try:
                    if self.authenticate_onedrive(parent_widget):
                        storage = self.account.storage()
                        drive = storage.get_default_drive()
                        
                        # 创建备份文件夹
                        folder = drive.get_item('TradeBackup')
                        if not folder:
                            folder = drive.create_folder('TradeBackup')
                            
                        # 上传数据
                        folder.upload_item(filename, json_data)
                        success = True
                except Exception as e:
                    error_msg += f"OneDrive备份失败: {str(e)}\n"
                    print(f"OneDrive备份失败: {e}")
        else:
            # 默认使用WebDAV备份
            try:
                # 确保webdav_client已初始化
                if not hasattr(self, 'webdav_client') or self.webdav_client is None:
                    self.init_webdav_client()
                
                # 获取完整的网址路径 - 确保URL格式正确
                base_url = self.webdav_url
                if not (base_url.startswith('http://') or base_url.startswith('https://')):
                    base_url = 'https://' + base_url
                if not base_url.endswith('/'):
                    base_url = base_url + '/'
                
                # 创建TradeBackup文件夹
                try:
                    if not self.webdav_client.check('TradeBackup'):
                        self.webdav_client.mkdir('TradeBackup')
                except Exception as e:
                    print(f"创建TradeBackup文件夹失败: {e}")
                
                # 保存文件到临时位置
                temp_file = f"temp_{filename}"
                with open(temp_file, 'w') as f:
                    f.write(json_data)
                
                # 上传到WebDAV (使用相对路径)
                remote_path = "TradeBackup/" + filename
                
                try:
                    self.webdav_client.upload_sync(local_path=temp_file, remote_path=remote_path)
                    success = True
                except Exception as e:
                    print(f"WebDAV上传失败 (路径1): {str(e)}")
                    
                    # 尝试替代路径
                    try:
                        # 尝试不同的相对路径格式
                        self.webdav_client.upload_sync(local_path=temp_file, remote_path=filename, remote_directory="TradeBackup")
                        success = True
                    except Exception as e2:
                        print(f"WebDAV上传失败 (路径2): {str(e2)}")
                        
                        # 最后尝试直接使用根目录
                        try:
                            self.webdav_client.upload_sync(local_path=temp_file, remote_path=filename)
                            success = True
                        except Exception as e3:
                            print(f"WebDAV上传失败 (路径3): {str(e3)}")
                            error_msg += f"WebDAV备份失败: 无法上传文件\n"
                
                # 删除临时文件
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
            except Exception as e:
                error_msg += f"WebDAV备份失败: {str(e)}\n"
                print(f"WebDAV备份失败: {e}")
        
        if not success and error_msg:
            if parent_widget:
                QMessageBox.warning(parent_widget, "备份失败", error_msg)
            return False
            
        return success
            
    def restore_data(self, backup_file, from_source='onedrive', parent_widget=None):
        """从云存储恢复数据"""
        try:
            if from_source == 'onedrive' and self.onedrive_enabled:
                if self.authenticate_onedrive(parent_widget):
                    storage = self.account.storage()
                    drive = storage.get_default_drive()
                    folder = drive.get_item('TradeBackup')
                    
                    if folder:
                        file = folder.get_item(backup_file)
                        if file:
                            content = file.get_content()
                            return json.loads(content)
            elif from_source == 'webdav' and self.webdav_enabled:
                remote_path = f"TradeBackup/{backup_file}"
                
                if self.webdav_client.check(remote_path):
                    # 下载到临时文件
                    temp_file = f"temp_{backup_file}"
                    self.webdav_client.download_sync(remote_path=remote_path, local_path=temp_file)
                    
                    # 读取文件内容
                    with open(temp_file, 'r') as f:
                        data = json.loads(f.read())
                    
                    # 删除临时文件
                    os.remove(temp_file)
                    return data
                    
            return None
        except Exception as e:
            if parent_widget:
                QMessageBox.warning(parent_widget, "恢复失败", f"从{from_source}恢复数据失败: {str(e)}")
            print(f"恢复失败: {e}")
            return None
            
    def get_backup_files(self, from_source='onedrive', parent_widget=None):
        """获取所有备份文件列表"""
        try:
            if from_source == 'onedrive' and self.onedrive_enabled:
                if self.authenticate_onedrive(parent_widget):
                    storage = self.account.storage()
                    drive = storage.get_default_drive()
                    folder = drive.get_item('TradeBackup')
                    
                    if folder:
                        files = folder.get_items()
                        return [item.name for item in files if item.name.endswith('.json')]
            elif from_source == 'webdav' and self.webdav_enabled:
                if self.webdav_client.check('TradeBackup'):
                    files = self.webdav_client.list('TradeBackup')
                    return [f for f in files if f.endswith('.json')]
                    
            return []
        except Exception as e:
            if parent_widget:
                QMessageBox.warning(parent_widget, "获取备份列表失败", 
                                    f"从{from_source}获取备份文件列表失败: {str(e)}")
            print(f"获取备份文件列表失败: {e}")
            return []
            
    def show_settings_dialog(self, parent_widget):
        """显示云存储设置对话框"""
        dialog = QDialog(parent_widget)
        dialog.setWindowTitle("云存储设置")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        # 默认备份目标设置
        layout.addWidget(QLabel("<b>默认备份目标</b>"))
        backup_target = QComboBox()
        
        # 添加可用的备份目标
        if self.onedrive_enabled:
            backup_target.addItem("OneDrive", "onedrive")
        if self.webdav_enabled:
            backup_target.addItem("WebDAV (坚果云等)", "webdav")
        
        # 设置当前值
        index = backup_target.findData(self.backup_target)
        if index >= 0:
            backup_target.setCurrentIndex(index)
            
        layout.addWidget(QLabel("默认备份目标:"))
        layout.addWidget(backup_target)
        
        # OneDrive设置区域
        layout.addWidget(QLabel("<b>OneDrive设置</b>"))
        onedrive_status = "已配置" if self.onedrive_enabled else "未配置"
        layout.addWidget(QLabel(f"状态: {onedrive_status}"))
        
        if self.onedrive_enabled:
            auth_status = "已认证" if (self.account and self.account.is_authenticated) else "未认证"
            layout.addWidget(QLabel(f"认证状态: {auth_status}"))
            
            onedrive_auth_button = QPushButton("认证OneDrive")
            onedrive_auth_button.clicked.connect(lambda: self.authenticate_onedrive(parent_widget))
            layout.addWidget(onedrive_auth_button)
        else:
            layout.addWidget(QLabel("请在.env文件中配置OneDrive的client_id和client_secret"))
        
        # WebDAV设置区域
        layout.addWidget(QLabel("<b>WebDAV设置</b>"))
        
        webdav_url_label = QLabel("WebDAV地址:")
        webdav_url_input = QLineEdit(self.webdav_url)
        layout.addWidget(webdav_url_label)
        layout.addWidget(webdav_url_input)
        
        webdav_username_label = QLabel("WebDAV用户名:")
        webdav_username_input = QLineEdit(self.webdav_username)
        layout.addWidget(webdav_username_label)
        layout.addWidget(webdav_username_input)
        
        # WebDAV密码标签和输入框
        webdav_password_label = QLabel("WebDAV密码:")
        webdav_password_input = QLineEdit(self.webdav_password)
        webdav_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(webdav_password_label)
        layout.addWidget(webdav_password_input)
        
        # 保存WebDAV设置按钮
        save_webdav_button = QPushButton("保存WebDAV设置")
        save_webdav_button.clicked.connect(lambda: self.save_webdav_settings(
            webdav_url_input.text(),
            webdav_username_input.text(),
            webdav_password_input.text(),
            dialog,
            parent_widget
        ))
        layout.addWidget(save_webdav_button)
        
        # 保存默认备份目标按钮
        save_target_button = QPushButton("保存默认备份目标")
        save_target_button.clicked.connect(lambda: self.save_backup_target(
            backup_target.currentData(),
            dialog
        ))
        layout.addWidget(save_target_button)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec()
        
    def save_webdav_settings(self, url, username, password, dialog, parent_widget):
        """保存WebDAV设置"""
        if not url or not username or not password:
            QMessageBox.warning(dialog, "错误", "所有WebDAV字段都必须填写")
            return
            
        try:
            # 尝试验证连接
            options = {
                'webdav_hostname': url,
                'webdav_login': username,
                'webdav_password': password
            }
            test_client = webdav.Client(options)
            
            # 尝试列出根目录，验证连接
            test_client.list()
            
            # 保存设置
            if self.setup_webdav(url, username, password):
                QMessageBox.information(dialog, "成功", "WebDAV设置已保存并验证成功")
        except Exception as e:
            QMessageBox.warning(dialog, "错误", f"WebDAV连接测试失败: {str(e)}")
            
    def save_backup_target(self, target, dialog):
        """保存默认备份目标"""
        if not target:
            QMessageBox.warning(dialog, "错误", "请选择有效的备份目标")
            return
            
        self.backup_target = target
        
        # 保存到环境变量
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
                
            # 检查是否已存在DEFAULT_BACKUP_TARGET配置
            if 'DEFAULT_BACKUP_TARGET' in env_content:
                # 更新现有配置
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('DEFAULT_BACKUP_TARGET='):
                        new_lines.append(f'DEFAULT_BACKUP_TARGET={target}')
                    else:
                        new_lines.append(line)
                new_env_content = '\n'.join(new_lines)
            else:
                # 添加新配置
                new_env_content = env_content + f'\nDEFAULT_BACKUP_TARGET={target}\n'
                
            with open('.env', 'w') as f:
                f.write(new_env_content)
                
            QMessageBox.information(dialog, "成功", f"已设置默认备份目标为: {target}")
        except Exception as e:
            QMessageBox.warning(dialog, "错误", f"保存默认备份目标失败: {str(e)}") 