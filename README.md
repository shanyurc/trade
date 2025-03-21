# 交易记录软件

这是一个轻量级的交易记录软件，用于记录和管理股票交易信息。

## 主要功能

1. 记录股票交易信息（买入点、买入时间等）
2. 自动计算卖出和买入目标价格
3. 实时股价监控和价格提醒
4. 本地数据存储
5. OneDrive/WebDAV 备份支持

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