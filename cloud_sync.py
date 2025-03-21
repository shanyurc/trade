from O365 import Account
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

class CloudSync:
    def __init__(self):
        self.client_id = os.getenv('ONEDRIVE_CLIENT_ID')
        self.client_secret = os.getenv('ONEDRIVE_CLIENT_SECRET')
        self.account = Account((self.client_id, self.client_secret))
        
    def authenticate(self):
        """认证OneDrive"""
        if not self.account.is_authenticated:
            self.account.authenticate()
            
    def backup_data(self, data):
        """备份数据到OneDrive"""
        try:
            self.authenticate()
            storage = self.account.storage()
            drive = storage.get_default_drive()
            
            # 创建备份文件夹
            folder = drive.get_item('TradeBackup')
            if not folder:
                folder = drive.create_folder('TradeBackup')
                
            # 创建备份文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backup_{timestamp}.json'
            
            # 上传数据
            folder.upload_item(filename, json.dumps(data))
            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False
            
    def restore_data(self, backup_file):
        """从OneDrive恢复数据"""
        try:
            self.authenticate()
            storage = self.account.storage()
            drive = storage.get_default_drive()
            folder = drive.get_item('TradeBackup')
            
            if folder:
                file = folder.get_item(backup_file)
                if file:
                    content = file.get_content()
                    return json.loads(content)
            return None
        except Exception as e:
            print(f"恢复失败: {e}")
            return None 