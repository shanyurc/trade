import tushare as ts
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class StockService:
    def __init__(self):
        self.token = os.getenv('TUSHARE_TOKEN')
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        
    def get_stock_info(self, stock_code):
        """获取股票基本信息"""
        try:
            df = self.pro.daily_basic(ts_code=stock_code, 
                                    fields='ts_code,symbol,name,area,industry,list_date')
            if not df.empty:
                return df.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"获取股票信息失败: {e}")
            return None
            
    def get_realtime_price(self, stock_code):
        """获取实时股价"""
        try:
            df = self.pro.daily(ts_code=stock_code, 
                              start_date=datetime.now().strftime('%Y%m%d'),
                              end_date=datetime.now().strftime('%Y%m%d'))
            if not df.empty:
                return df.iloc[0]['close']
            return None
        except Exception as e:
            print(f"获取实时价格失败: {e}")
            return None
            
    def check_price_targets(self, trade):
        """检查是否达到目标价格"""
        current_price = self.get_realtime_price(trade.stock_code)
        if current_price is None:
            return None
            
        if current_price >= trade.sell_target:
            return "SELL"
        elif current_price <= trade.buy_target:
            return "BUY"
        return None 