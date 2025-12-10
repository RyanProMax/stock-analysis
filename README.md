# 股票分析系统

一个基于多因子模型的股票分析系统，提供技术面和基本面分析，支持 A 股和美股。

🌐 [在线演示](https://ryanpromax.github.io/stock-analysis/)

## 功能特性

### 技术面因子

- **MA 均线**: MA5/MA20/MA60 多头/空头排列
- **EMA 指数均线**: 12 日/26 日 EMA 交叉信号
- **MACD**: 柱线方向与强度
- **RSI**: 超买超卖判断
- **KDJ**: J 线形态与 K/D 交叉信号
- **WR 威廉指标**: 短期超买超卖
- **布林带**: 宽度、位置分析
- **ATR**: 真实波动幅度
- **贪恐指数**: 逆向情绪指标
- **成交量比率**: 当前成交量 vs 均量
- **VR 成交量比率**: 买盘/卖盘力量对比

### 基本面因子

- **营收增长率**: 反映公司成长性
- **资产负债率**: 反映财务健康度
- **市盈率（PE）**: 反映估值水平
- **市净率（PB）**: 反映资产价值
- **ROE**: 反映盈利能力

## 技术栈

**前端**: React 18, TypeScript, Vite, Ant Design  
**后端**: FastAPI, Python 3.12+, tushare, akshare, yfinance, pandas

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- pnpm（推荐）或 npm

### 安装依赖

```bash
# 1. 安装根目录依赖（用于一键启动）
pnpm install

# 2. 安装后端依赖
cd server
poetry install

# 3. 安装前端依赖
cd ../web
pnpm install
```

### 启动项目

**一键启动（推荐）**：

```bash
# 在项目根目录运行
pnpm run dev
```

这会同时启动前后端服务：
- 前端: http://localhost:3000
- 后端: http://localhost:8080

**分别启动**：

```bash
# 终端 1 - 后端
cd server
poetry run python main.py

# 终端 2 - 前端
cd web
pnpm run dev
```

### 访问应用

- **前端应用**: http://localhost:3000
- **API 文档**: http://localhost:8080/docs

## 使用说明

1. 在前端选择股票（支持搜索和批量选择）
   - 美股示例：`NVDA`, `AAPL`, `TSLA`
   - A 股示例：`600519`, `000001`, `300750`
2. 系统自动分析选中的股票
3. 查看分析结果，包括：
   - 股票基本信息（名称、代码、价格）
   - 贪恐指数仪表盘
   - 技术面和基本面因子详情及多空信号

## 项目结构

```
stock-analysis/
├── web/                    # React 前端应用
│   ├── src/
│   │   ├── api/           # API 客户端
│   │   ├── components/    # React 组件
│   │   └── types/         # TypeScript 类型定义
│   └── package.json
│
├── server/                 # Python 后端
│   ├── src/
│   │   ├── controller/    # API 控制器层
│   │   └── service/       # 业务逻辑层
│   ├── main.py            # FastAPI 应用入口
│   └── pyproject.toml     # Python 依赖管理
│
└── package.json           # 根目录脚本（一键启动）
```

## API 接口

### POST /stock/analyze

批量分析股票列表

**请求体：**

```json
{
  "symbols": ["NVDA", "AAPL", "600519"]
}
```

### GET /stock/list

获取股票列表

**查询参数：**
- `market`: 市场类型，可选值：`A股`、`美股`，不传则返回所有市场
- `refresh`: 是否强制刷新缓存，默认 `false`

## 部署

### Docker 部署

```bash
cd server

# 构建镜像
docker build -t stock-analysis .

# 运行容器
docker run -p 8080:8080 stock-analysis
```

### 生产环境配置

**环境变量：**

- `ENV`: 环境类型，`production` 或 `development`（默认）
- `PORT`: 服务端口（默认 8080）
- `TUSHARE_TOKEN`: Tushare API Token（可选，用于获取 A 股数据）
- `GCS_CACHE_BUCKET`: Google Cloud Storage Bucket 名称（可选，用于生产环境缓存）

**缓存系统：**

- **开发环境**：使用本地文件系统（`.cache/` 目录）
- **生产环境**：
  - 设置 `GCS_CACHE_BUCKET` 环境变量后，使用 Google Cloud Storage 存储缓存
  - 未设置则使用本地文件系统（容器临时存储）
  - 缓存按天存储，自动避免重复写入

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！
