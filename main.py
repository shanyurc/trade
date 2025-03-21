import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                           QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt6.QtCore import QTimer
from models import Session, Trade
from stock_service import StockService
from cloud_sync import CloudSync
from datetime import datetime

class TradeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("交易记录软件")
        self.setGeometry(100, 100, 800, 600)
        
        self.session = Session()
        self.stock_service = StockService()
        self.cloud_sync = CloudSync()
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加交易表单
        form_layout = QHBoxLayout()
        
        self.stock_code = QLineEdit()
        self.stock_code.setPlaceholderText("股票代码")
        self.buy_price = QLineEdit()
        self.buy_price.setPlaceholderText("买入价格")
        self.sell_condition = QLineEdit()
        self.sell_condition.setPlaceholderText("卖出条件(年化%)")
        self.buy_step = QLineEdit()
        self.buy_step.setPlaceholderText("买入台阶(%)")
        
        add_button = QPushButton("添加交易")
        add_button.clicked.connect(self.add_trade)
        
        form_layout.addWidget(QLabel("股票代码:"))
        form_layout.addWidget(self.stock_code)
        form_layout.addWidget(QLabel("买入价格:"))
        form_layout.addWidget(self.buy_price)
        form_layout.addWidget(QLabel("卖出条件:"))
        form_layout.addWidget(self.sell_condition)
        form_layout.addWidget(QLabel("买入台阶:"))
        form_layout.addWidget(self.buy_step)
        form_layout.addWidget(add_button)
        
        layout.addLayout(form_layout)
        
        # 交易列表
        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(8)
        self.trade_table.setHorizontalHeaderLabels([
            "股票代码", "股票名称", "买入价格", "买入时间", 
            "卖出目标", "买入目标", "状态", "操作"
        ])
        layout.addWidget(self.trade_table)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        backup_button = QPushButton("备份数据")
        backup_button.clicked.connect(self.backup_data)
        restore_button = QPushButton("恢复数据")
        restore_button.clicked.connect(self.restore_data)
        
        button_layout.addWidget(backup_button)
        button_layout.addWidget(restore_button)
        layout.addLayout(button_layout)
        
        self.refresh_table()
        
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_prices)
        self.timer.start(60000)  # 每分钟检查一次
        
    def add_trade(self):
        try:
            stock_code = self.stock_code.text()
            stock_info = self.stock_service.get_stock_info(stock_code)
            if not stock_info:
                QMessageBox.warning(self, "错误", "无法获取股票信息")
                return
                
            trade = Trade(
                stock_code=stock_code,
                stock_name=stock_info['name'],
                buy_price=float(self.buy_price.text()),
                buy_time=datetime.now(),
                sell_condition=float(self.sell_condition.text()),
                buy_step=float(self.buy_step.text())/100
            )
            trade.calculate_targets()
            
            self.session.add(trade)
            self.session.commit()
            
            self.refresh_table()
            self.clear_form()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            
    def refresh_table(self):
        trades = self.session.query(Trade).filter_by(is_active=True).all()
        self.trade_table.setRowCount(len(trades))
        
        for i, trade in enumerate(trades):
            self.trade_table.setItem(i, 0, QTableWidgetItem(trade.stock_code))
            self.trade_table.setItem(i, 1, QTableWidgetItem(trade.stock_name))
            self.trade_table.setItem(i, 2, QTableWidgetItem(str(trade.buy_price)))
            self.trade_table.setItem(i, 3, QTableWidgetItem(trade.buy_time.strftime('%Y-%m-%d %H:%M')))
            self.trade_table.setItem(i, 4, QTableWidgetItem(str(trade.sell_target)))
            self.trade_table.setItem(i, 5, QTableWidgetItem(str(trade.buy_target)))
            self.trade_table.setItem(i, 6, QTableWidgetItem("活跃"))
            
            delete_button = QPushButton("删除")
            delete_button.clicked.connect(lambda checked, t=trade: self.delete_trade(t))
            self.trade_table.setCellWidget(i, 7, delete_button)
            
    def check_prices(self):
        trades = self.session.query(Trade).filter_by(is_active=True).all()
        for trade in trades:
            result = self.stock_service.check_price_targets(trade)
            if result:
                QMessageBox.information(self, "价格提醒", 
                    f"{trade.stock_name}({trade.stock_code}) 达到{result}目标价格！")
                
    def delete_trade(self, trade):
        trade.is_active = False
        self.session.commit()
        self.refresh_table()
        
    def backup_data(self):
        trades = self.session.query(Trade).all()
        data = [{
            'stock_code': t.stock_code,
            'stock_name': t.stock_name,
            'buy_price': t.buy_price,
            'buy_time': t.buy_time.isoformat(),
            'sell_condition': t.sell_condition,
            'buy_step': t.buy_step,
            'is_active': t.is_active
        } for t in trades]
        
        if self.cloud_sync.backup_data(data):
            QMessageBox.information(self, "成功", "数据备份成功")
        else:
            QMessageBox.warning(self, "错误", "数据备份失败")
            
    def restore_data(self):
        # 这里需要实现从备份文件列表中选择并恢复的功能
        pass
        
    def clear_form(self):
        self.stock_code.clear()
        self.buy_price.clear()
        self.sell_condition.clear()
        self.buy_step.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TradeApp()
    window.show()
    sys.exit(app.exec()) 