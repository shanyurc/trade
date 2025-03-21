# 交易记录软件（时间网格）

这是一个轻量级的股票交易记录应用，帮助用户记录股票交易信息并计算目标价格，使用时间网格的交易方式，来源于雪球之水沧浪的白马股交易法。

## 主要功能

1. 轻量化应用，简洁易用
2. 记录股票信息，包括每笔交易的买入点、买入时间等信息
3. 自动计算卖出目标价格和买入目标价格
   - 可设置买入台阶和卖出条件(年化收益)
   - 计算公式：
     - 卖出目标价格 = 本次交易买入价 *（1 + 卖出条件 * MAX(（当前时间-买入时间）,30)/360）
     - 买入目标价格 = 卖出目标价格 *（1 - 买入台阶）
4. 获取实时股价信息，根据目标价格发送通知
5. 交易信息保存在本地
6. 支持OneDrive或WebDAV备份

## 安装说明

1. 克隆项目
2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用说明

1. 运行主程序：
```bash
python main.py
```

## 配置说明

1. 在 `.env` 文件中配置以下信息：
   - TUSHARE_TOKEN：Tushare API token
   - ONEDRIVE_CLIENT_ID：OneDrive API client ID
   - ONEDRIVE_CLIENT_SECRET：OneDrive API client secret 