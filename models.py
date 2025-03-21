from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False)  # 股票代码
    stock_name = Column(String(50), nullable=False)  # 股票名称
    buy_price = Column(Float, nullable=False)        # 买入价格
    buy_time = Column(DateTime, nullable=False)      # 买入时间
    sell_target = Column(Float)                      # 卖出目标价格
    buy_target = Column(Float)                       # 买入目标价格
    sell_condition = Column(Float)                   # 卖出条件（年化收益率）
    buy_step = Column(Float)                         # 买入台阶
    price_precision = Column(Integer, default=2)     # 价格精度
    is_active = Column(Boolean, default=True)        # 是否活跃
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def calculate_targets(self):
        """计算卖出和买入目标价格"""
        days = max((datetime.now() - self.buy_time).days, 30)
        print(f"变量值: {days} {self.sell_condition} {self.buy_step}") 
        # 计算卖出目标价格并使用指定精度
        precision = self.price_precision if hasattr(self, 'price_precision') and self.price_precision is not None else 2
        self.sell_target = round(self.buy_price * (1 + self.sell_condition * days/360), precision)
        # 计算买入目标价格并使用指定精度
        self.buy_target = round(self.sell_target * (1 - self.buy_step), precision)

# 创建数据库连接
engine = create_engine('sqlite:///trades.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine) 