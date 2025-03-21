import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTableWidget, QTableWidgetItem, QMessageBox,
                           QDialog, QListWidget, QDialogButtonBox, 
                           QComboBox, QMenu, QMenuBar, QTabWidget, QDateTimeEdit)
from PySide6.QtCore import QTimer, QDateTime, Qt
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
        # 创建主界面
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加交易表单
        self.stock_code = QLineEdit()
        self.stock_code.setPlaceholderText("股票代码")
        # 添加回车键响应
        self.stock_code.returnPressed.connect(self.search_stock)
        
        self.buy_price = QLineEdit()
        self.buy_price.setPlaceholderText("买入价格")
        
        self.sell_condition = QLineEdit()
        self.sell_condition.setPlaceholderText("卖出条件(年化%)")
        self.sell_condition.setText("30")  # 设置默认值30%
        
        self.buy_step = QLineEdit()
        self.buy_step.setPlaceholderText("买入台阶(%)")
        self.buy_step.setText("10")  # 设置默认值10%
        
        # 添加买入时间选择控件
        self.buy_time_edit = QDateTimeEdit()
        self.buy_time_edit.setCalendarPopup(True)  # 启用日历弹出窗口
        self.buy_time_edit.setDateTime(QDateTime.currentDateTime())
        
        # 添加股票搜索按钮
        search_button = QPushButton("搜索股票")
        search_button.clicked.connect(self.search_stock)
        
        add_button = QPushButton("添加交易")
        add_button.clicked.connect(self.add_trade)
        
        # 添加第一行控件
        row1_layout = QHBoxLayout()
        row1_layout.addWidget(QLabel("股票代码:"))
        row1_layout.addWidget(self.stock_code)
        row1_layout.addWidget(search_button)
        row1_layout.addWidget(QLabel("买入价格:"))
        row1_layout.addWidget(self.buy_price)
        layout.addLayout(row1_layout)
        
        # 添加第二行控件
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(QLabel("卖出条件:"))
        row2_layout.addWidget(self.sell_condition)
        row2_layout.addWidget(QLabel("买入台阶:"))
        row2_layout.addWidget(self.buy_step)
        row2_layout.addWidget(QLabel("买入时间:"))
        row2_layout.addWidget(self.buy_time_edit)
        row2_layout.addWidget(add_button)
        layout.addLayout(row2_layout)
        
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
        export_button = QPushButton("导出数据")
        export_button.clicked.connect(self.export_data)
        
        button_layout.addWidget(backup_button)
        button_layout.addWidget(restore_button)
        button_layout.addWidget(export_button)
        layout.addLayout(button_layout)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 刷新表格
        self.refresh_table()
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        export_action = file_menu.addAction("导出数据")
        export_action.triggered.connect(self.export_data)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # 设置菜单
        settings_menu = menu_bar.addMenu("设置")
        
        cloud_settings_action = settings_menu.addAction("云存储设置")
        cloud_settings_action.triggered.connect(self.show_cloud_settings)
        
    def show_cloud_settings(self):
        """显示云存储设置对话框"""
        self.cloud_sync.show_settings_dialog(self)
        
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
            
            # 获取实时价格和精度
            price, precision = self.stock_service.get_realtime_price(stock_code)
            if not price:
                # 如果无法获取实时价格，使用输入的价格
                price = float(self.buy_price.text())
                precision = 2  # 默认使用2位小数精度
            
            # 直接从主界面的时间控件获取买入时间
            buy_time = self.buy_time_edit.dateTime().toPython()
                
            trade = Trade(
                stock_code=stock_code,
                stock_name=stock_info['name'],
                buy_price=price if float(self.buy_price.text()) == 0 else float(self.buy_price.text()),
                buy_time=buy_time,
                sell_condition=float(self.sell_condition.text())/100,
                buy_step=float(self.buy_step.text())/100,
                price_precision=precision
            )
            trade.calculate_targets()
            
            self.session.add(trade)
            self.session.commit()
            
            self.refresh_table()
            self.clear_form()
            
            # 显示成功提示
            QMessageBox.information(self, "成功", f"已添加交易记录: {stock_info['name']}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            
    def refresh_table(self):
        # 查询所有活跃交易
        all_trades = self.session.query(Trade).filter_by(is_active=True).all()
        
        # 按股票代码分组，只保留每支股票买入价最低的记录
        lowest_price_trades = {}
        for trade in all_trades:
            if trade.stock_code not in lowest_price_trades:
                lowest_price_trades[trade.stock_code] = trade
            else:
                if trade.buy_price < lowest_price_trades[trade.stock_code].buy_price:
                    lowest_price_trades[trade.stock_code] = trade
        
        # 转换为列表
        trades = list(lowest_price_trades.values())
        
        # 设置表格行数
        self.trade_table.setRowCount(len(trades))
        
        for i, trade in enumerate(trades):
            # 获取价格精度
            precision = trade.price_precision if hasattr(trade, 'price_precision') and trade.price_precision is not None else 2
            price_format = f"{{:.{precision}f}}"
            
            self.trade_table.setItem(i, 0, QTableWidgetItem(trade.stock_code))
            self.trade_table.setItem(i, 1, QTableWidgetItem(trade.stock_name))
            self.trade_table.setItem(i, 2, QTableWidgetItem(price_format.format(trade.buy_price)))
            self.trade_table.setItem(i, 3, QTableWidgetItem(trade.buy_time.strftime('%Y-%m-%d %H:%M')))
            self.trade_table.setItem(i, 4, QTableWidgetItem(price_format.format(trade.sell_target)))
            self.trade_table.setItem(i, 5, QTableWidgetItem(price_format.format(trade.buy_target)))
            self.trade_table.setItem(i, 6, QTableWidgetItem("活跃"))
            
            # 创建按钮布局，包含删除和详情按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            # 删除按钮
            delete_button = QPushButton("删除")
            current_trade = trade  # 将当前的trade捕获到本地变量中
            delete_button.clicked.connect(lambda checked=False, t=current_trade: self.delete_trade(t))
            
            # 详情按钮
            detail_button = QPushButton("详情")
            detail_button.clicked.connect(lambda checked=False, code=trade.stock_code: self.show_stock_detail(code))
            
            button_layout.addWidget(delete_button)
            button_layout.addWidget(detail_button)
            
            self.trade_table.setCellWidget(i, 7, button_widget)
            
    def check_prices(self):
        # 只检查主表显示的交易（每支股票最低价格的那条）
        trades = self.session.query(Trade).filter_by(is_active=True).all()
        
        # 按股票代码分组，只保留每支股票买入价最低的记录
        lowest_price_trades = {}
        for trade in trades:
            if trade.stock_code not in lowest_price_trades:
                lowest_price_trades[trade.stock_code] = trade
            else:
                if trade.buy_price < lowest_price_trades[trade.stock_code].buy_price:
                    lowest_price_trades[trade.stock_code] = trade
                    
        # 只检查这些交易的价格
        for trade in lowest_price_trades.values():
            result = self.stock_service.check_price_targets(trade)
            if result:
                # 使用InfoBar替代消息框
                QMessageBox.information(self, "价格提醒", f"{trade.stock_name}({trade.stock_code}) 达到{result}目标价格！")
                
    def delete_trade(self, trade):
        trade.is_active = False
        self.session.commit()
        self.refresh_table()
        
    def backup_data(self):
        """备份数据到云存储"""
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
        
        # 使用云同步类中的默认备份目标
        target_name = "OneDrive" if self.cloud_sync.backup_target == "onedrive" else "WebDAV"
        
        if self.cloud_sync.backup_data(data, parent_widget=self):
            QMessageBox.information(self, "成功", f"数据成功备份到{target_name}")
        else:
            QMessageBox.warning(self, "错误", f"备份到{target_name}失败")
            
    def restore_data(self):
        """从云存储恢复数据"""
        try:
            # 选择恢复源
            source_dialog = QDialog(self)
            source_dialog.setWindowTitle("选择恢复源")
            source_layout = QVBoxLayout(source_dialog)
            
            source_layout.addWidget(QLabel("请选择恢复数据源:"))
            restore_source = QComboBox()
            
            # 添加可用的恢复源
            if self.cloud_sync.onedrive_enabled:
                restore_source.addItem("OneDrive", "onedrive")
            if self.cloud_sync.webdav_enabled:
                restore_source.addItem("WebDAV", "webdav")
                
            if restore_source.count() == 0:
                QMessageBox.warning(self, "错误", "没有可用的云存储。请先设置云存储。")
                self.show_cloud_settings()
                return
                
            source_layout.addWidget(restore_source)
            
            source_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            source_buttons.accepted.connect(source_dialog.accept)
            source_buttons.rejected.connect(source_dialog.reject)
            source_layout.addWidget(source_buttons)
            
            if source_dialog.exec() != QDialog.DialogCode.Accepted:
                return
                
            source = restore_source.currentData()
            
            # 获取备份文件列表
            backup_files = self.cloud_sync.get_backup_files(from_source=source, parent_widget=self)
            if not backup_files:
                QMessageBox.warning(self, "错误", f"在{restore_source.currentText()}中未找到备份文件")
                return
            
            # 创建选择对话框
            file_dialog = QDialog(self)
            file_dialog.setWindowTitle("选择恢复文件")
            file_layout = QVBoxLayout(file_dialog)
            
            file_list = QListWidget()
            for file in backup_files:
                file_list.addItem(file)
            
            file_layout.addWidget(QLabel("选择要恢复的备份文件:"))
            file_layout.addWidget(file_list)
            
            file_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            file_buttons.accepted.connect(file_dialog.accept)
            file_buttons.rejected.connect(file_dialog.reject)
            file_layout.addWidget(file_buttons)
            
            if file_dialog.exec() == QDialog.DialogCode.Accepted and file_list.currentItem():
                selected_file = file_list.currentItem().text()
                data = self.cloud_sync.restore_data(selected_file, from_source=source, parent_widget=self)
                
                if data:
                    # 确认是否要覆盖现有数据
                    confirm = QMessageBox.question(self, "确认", 
                                               "恢复将覆盖现有数据，确定要继续吗？",
                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if confirm == QMessageBox.StandardButton.Yes:
                        # 清除现有数据
                        self.session.query(Trade).delete()
                        
                        # 添加恢复的数据
                        for item in data:
                            trade = Trade(
                                stock_code=item['stock_code'],
                                stock_name=item['stock_name'],
                                buy_price=item['buy_price'],
                                buy_time=datetime.fromisoformat(item['buy_time']),
                                sell_condition=item['sell_condition'],
                                buy_step=item['buy_step'],
                                is_active=item['is_active']
                            )
                            trade.calculate_targets()
                            self.session.add(trade)
                        
                        self.session.commit()
                        self.refresh_table()
                        QMessageBox.information(self, "成功", "数据恢复成功")
                else:
                    QMessageBox.warning(self, "错误", "数据恢复失败")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"恢复数据时出错: {str(e)}")
        
    def clear_form(self):
        self.stock_code.clear()
        self.buy_price.clear()
        self.sell_condition.setText("30")
        self.buy_step.setText("10")
        
    def search_stock(self):
        """搜索股票并让用户选择"""
        try:
            search_text = self.stock_code.text().strip()
            if not search_text:
                QMessageBox.warning(self, "提示", "请输入股票代码或名称进行搜索")
                return
            
            # 搜索股票
            results = self.stock_service.search_stocks(search_text)
            
            if not results:
                QMessageBox.information(self, "提示", "未找到匹配的股票")
                return
            
            # 创建选择对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("选择股票")
            dialog.setModal(True)
            layout = QVBoxLayout(dialog)
            
            # 创建一个更明显的标签提示用户如何操作
            label = QLabel("<h3>请双击选择股票</h3>")
            label.setStyleSheet("color: #0078d4; margin: 5px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            
            # 创建表格
            table = QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["代码", "名称", "行业"])
            table.setRowCount(len(results))
            
            for i, stock in enumerate(results):
                # 防止缺少键值导致的崩溃
                ts_code = stock.get('ts_code', '')
                name = stock.get('name', '未知')
                industry = stock.get('industry', '')
                
                item_code = QTableWidgetItem(ts_code)
                item_name = QTableWidgetItem(name)
                item_industry = QTableWidgetItem(industry)
                
                table.setItem(i, 0, item_code)
                table.setItem(i, 1, item_name)
                table.setItem(i, 2, item_industry)
                
                # 保存完整的股票信息作为表格项的数据
                table.item(i, 0).setData(Qt.ItemDataRole.UserRole, stock)
            
            # 设置表格可选中整行
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            # 设置表格列宽自动适应内容
            table.resizeColumnsToContents()
            
            # 双击事件
            table.cellDoubleClicked.connect(lambda row, col: self.handle_stock_selection(results[row], dialog))
            
            layout.addWidget(table)
            
            # 设置对话框大小和位置
            dialog.setMinimumWidth(550)
            dialog.setMinimumHeight(400)
            dialog.setGeometry(
                self.geometry().center().x() - 275,
                self.geometry().center().y() - 200,
                550, 400
            )
            
            # 显示对话框
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"搜索股票出错: {str(e)}")
    
    def handle_stock_selection(self, stock, dialog):
        """处理股票选择事件"""
        try:
            # 安全获取ts_code
            ts_code = stock.get('ts_code', '')
            if not ts_code:
                QMessageBox.warning(self, "错误", "无效的股票代码")
                return
                
            self.stock_code.setText(ts_code)
            
            # 尝试获取当前价格，如果stock中有current_price则使用
            price = stock.get('current_price')
            precision = 2  # 默认精度
            
            if not price or price <= 0:
                try:
                    price, precision = self.stock_service.get_realtime_price(ts_code)
                except Exception as e:
                    print(f"获取股票价格出错: {e}")
            
            if price and price > 0:
                # 根据精度格式化价格
                price_format = f"{{:.{precision}f}}"
                self.buy_price.setText(price_format.format(price))
            
            dialog.accept()
        except Exception as e:
            print(f"选择股票异常: {e}")
            QMessageBox.warning(self, "错误", f"处理股票数据时出错: {str(e)}")
            # 不关闭对话框，让用户可以尝试选择其他股票
        
    def export_data(self):
        """导出交易数据为CSV或Excel"""
        try:
            from PySide6.QtWidgets import QFileDialog
            import pandas as pd
            import os
            
            # 获取所有交易记录
            trades = self.session.query(Trade).all()
            if not trades:
                QMessageBox.warning(self, "提示", "没有可导出的交易记录")
                return
            
            # 转换为DataFrame
            data = []
            for t in trades:
                # 获取价格精度并确保是有效值
                precision = 2  # 默认值
                try:
                    if hasattr(t, 'price_precision') and t.price_precision is not None:
                        precision = int(t.price_precision)
                except (ValueError, TypeError):
                    pass  # 如果转换失败，使用默认值
                
                # 确保所有数值都是有效的
                try:
                    buy_price = float(t.buy_price) if t.buy_price is not None else 0.0
                    sell_target = float(t.sell_target) if t.sell_target is not None else 0.0
                    buy_target = float(t.buy_target) if t.buy_target is not None else 0.0
                    sell_condition = float(t.sell_condition) if t.sell_condition is not None else 0.0
                    buy_step = float(t.buy_step) if t.buy_step is not None else 0.0
                    
                    data.append({
                        '股票代码': t.stock_code,
                        '股票名称': t.stock_name,
                        '买入价格': round(buy_price, precision),
                        '买入时间': t.buy_time.strftime('%Y-%m-%d %H:%M') if t.buy_time else '',
                        '卖出目标价': round(sell_target, precision),
                        '买入目标价': round(buy_target, precision),
                        '卖出条件(年化%)': round(sell_condition * 100, 2),
                        '买入台阶(%)': round(buy_step * 100, 2),
                        '状态': '活跃' if t.is_active else '已关闭'
                    })
                except Exception as e:
                    print(f"处理交易记录 {t.id} 时出错: {e}")
                    # 继续处理其他记录
            
            if not data:
                QMessageBox.warning(self, "错误", "无法处理交易数据，请检查数据有效性")
                return
                
            df = pd.DataFrame(data)
            
            # 让用户选择保存位置和文件类型
            file_filter = "CSV文件 (*.csv);;Excel文件 (*.xlsx)"
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self, "导出数据", "交易记录", file_filter
            )
            
            if not file_path:
                return  # 用户取消了保存
                
            # 确保文件有正确的扩展名
            if '*.csv' in selected_filter and not file_path.lower().endswith('.csv'):
                file_path += '.csv'
            elif '*.xlsx' in selected_filter and not file_path.lower().endswith('.xlsx'):
                file_path += '.xlsx'
            
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # 保存文件
            try:
                if file_path.lower().endswith('.csv'):
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                else:  # .xlsx
                    df.to_excel(file_path, index=False)
                
                QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
                
        except ImportError as e:
            QMessageBox.critical(self, "错误", f"缺少必要的库: {str(e)}\n请安装 pandas 和 openpyxl")
            return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出数据时出错: {str(e)}")

    def show_stock_detail(self, stock_code):
        """显示指定股票的详细记录"""
        # 查找该股票的所有交易记录
        trades = self.session.query(Trade).filter_by(stock_code=stock_code).all()
        if not trades:
            QMessageBox.information(self, "提示", f"未找到股票{stock_code}的交易记录")
            return
            
        # 创建详情对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{trades[0].stock_name}({stock_code})详细记录")
        dialog.setMinimumWidth(800)
        dialog.setMinimumHeight(500)
        
        layout = QVBoxLayout(dialog)
        
        # 创建TabWidget来分离活跃和已关闭的交易
        tab_widget = QTabWidget()
        
        # 创建活跃交易表格
        active_trades = [t for t in trades if t.is_active]
        active_table = self.create_detail_table(active_trades)
        tab_widget.addTab(active_table, f"活跃交易({len(active_trades)})")
        
        # 创建已关闭交易表格
        closed_trades = [t for t in trades if not t.is_active]
        closed_table = self.create_detail_table(closed_trades)
        tab_widget.addTab(closed_table, f"已关闭交易({len(closed_trades)})")
        
        layout.addWidget(tab_widget)
        
        dialog.exec()
    
    def create_detail_table(self, trades):
        """创建详情表格"""
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "ID", "买入价格", "买入时间", "卖出目标", "买入目标", 
            "卖出条件(%)", "买入台阶(%)", "状态", "操作"
        ])
        
        # 允许排序
        table.setSortingEnabled(True)
        
        # 设置行数
        table.setRowCount(len(trades))
        
        for i, trade in enumerate(trades):
            # 获取价格精度
            precision = trade.price_precision if hasattr(trade, 'price_precision') and trade.price_precision is not None else 2
            price_format = f"{{:.{precision}f}}"
            
            table.setItem(i, 0, QTableWidgetItem(str(trade.id)))
            table.setItem(i, 1, QTableWidgetItem(price_format.format(trade.buy_price)))
            table.setItem(i, 2, QTableWidgetItem(trade.buy_time.strftime('%Y-%m-%d %H:%M')))
            table.setItem(i, 3, QTableWidgetItem(price_format.format(trade.sell_target)))
            table.setItem(i, 4, QTableWidgetItem(price_format.format(trade.buy_target)))
            table.setItem(i, 5, QTableWidgetItem(f"{trade.sell_condition*100:.2f}%"))
            table.setItem(i, 6, QTableWidgetItem(f"{trade.buy_step*100:.2f}%"))
            
            status = "活跃" if trade.is_active else "已关闭"
            table.setItem(i, 7, QTableWidgetItem(status))
            
            # 操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            # 修改按钮
            edit_button = QPushButton("修改")
            current_trade = trade
            edit_button.clicked.connect(lambda checked=False, t=current_trade: self.edit_trade(t))
            
            # 删除按钮
            delete_button = QPushButton("删除")
            delete_button.clicked.connect(lambda checked=False, t=current_trade: self.delete_trade_and_refresh(t))
            
            button_layout.addWidget(edit_button)
            button_layout.addWidget(delete_button)
            
            table.setCellWidget(i, 8, button_widget)
        
        # 调整列宽
        table.resizeColumnsToContents()
        
        return table
    
    def edit_trade(self, trade):
        """修改交易参数"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"修改交易 - {trade.stock_name}")
        layout = QVBoxLayout(dialog)
        
        # 获取价格精度
        precision = trade.price_precision if hasattr(trade, 'price_precision') and trade.price_precision is not None else 2
        price_format = f"{{:.{precision}f}}"
        
        # 当前交易信息
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"买入价格: {price_format.format(trade.buy_price)}"))
        info_layout.addWidget(QLabel(f"当前卖出目标: {price_format.format(trade.sell_target)}"))
        info_layout.addWidget(QLabel(f"当前买入目标: {price_format.format(trade.buy_target)}"))
        layout.addLayout(info_layout)
        
        # 表单布局
        form_layout = QVBoxLayout()
        
        # 买入时间选择
        buy_time_layout = QHBoxLayout()
        buy_time_layout.addWidget(QLabel("买入时间:"))
        buy_time_edit = QDateTimeEdit()
        buy_time_edit.setCalendarPopup(True)  # 启用日历弹出窗口
        buy_time_edit.setDateTime(QDateTime(trade.buy_time))
        buy_time_layout.addWidget(buy_time_edit)
        form_layout.addLayout(buy_time_layout)
        
        # 买入台阶输入
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("买入台阶(%):"))
        step_edit = QLineEdit()
        step_edit.setText(f"{trade.buy_step*100:.2f}")
        step_layout.addWidget(step_edit)
        form_layout.addLayout(step_layout)
        
        # 卖出条件输入
        condition_layout = QHBoxLayout()
        condition_layout.addWidget(QLabel("卖出条件(年化%):"))
        condition_edit = QLineEdit()
        condition_edit.setText(f"{trade.sell_condition*100:.2f}")
        condition_layout.addWidget(condition_edit)
        form_layout.addLayout(condition_layout)
        
        layout.addLayout(form_layout)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                # 获取新的参数
                new_buy_time = buy_time_edit.dateTime().toPython()
                new_step = float(step_edit.text()) / 100
                new_condition = float(condition_edit.text()) / 100
                
                # 更新交易参数
                trade.buy_time = new_buy_time
                trade.buy_step = new_step
                trade.sell_condition = new_condition
                
                # 重新计算目标价格
                trade.calculate_targets()
                
                # 保存到数据库
                self.session.commit()
                
                # 刷新主表
                self.refresh_table()
                
                QMessageBox.information(dialog, "成功", "交易参数已更新")
            except Exception as e:
                QMessageBox.warning(dialog, "错误", f"更新交易参数失败: {str(e)}")
    
    def delete_trade_and_refresh(self, trade):
        """删除交易并刷新所有相关视图"""
        confirm = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除 {trade.stock_name} 的这条交易记录吗？",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            trade.is_active = False
            self.session.commit()
            self.refresh_table()
            
            # 关闭并重新打开详情对话框
            active_window = QApplication.activeWindow()
            if active_window and active_window != self:
                active_window.close()
                self.show_stock_detail(trade.stock_code)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TradeApp()
    window.show()
    sys.exit(app.exec()) 