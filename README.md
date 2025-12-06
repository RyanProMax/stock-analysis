# 股票分析系统

一个基于多因子模型的股票分析系统，提供技术面和基本面分析，支持 A 股和美股。

🌐 [https://ryanpromax.github.io/stock-analysis/](https://ryanpromax.github.io/stock-analysis/)

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

**前端**: React 18, TypeScript, Vite, Ant Design, Axios
**后端**: FastAPI, Python 3.12+, akshare, yfinance, pandas, stockstats

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

1. 在前端输入股票代码（支持多个，用逗号或空格分隔）
   - 美股示例：`NVDA`, `AAPL`, `TSLA`
   - A 股示例：`600519`, `000001`, `300750`
2. 点击"分析"按钮
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
│   │   ├── types/         # TypeScript 类型定义
│   │   └── App.tsx        # 主应用组件
│   └── package.json
│
├── server/                 # Python 后端
│   ├── src/
│   │   ├── controller/    # API 控制器层
│   │   ├── service/       # 业务逻辑层
│   │   │   ├── strategies/    # 分析策略
│   │   │   ├── data_loader.py # 数据加载
│   │   │   └── model.py       # 数据模型
│   │   └── __init__.py
│   ├── main.py            # FastAPI 应用入口
│   ├── pyproject.toml     # Python 依赖管理
│   └── Dockerfile         # Docker 配置
│
├── package.json           # 根目录脚本（一键启动）
└── README.md
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

**响应：**

```json
[
  {
    "symbol": "NVDA",
    "stock_name": "NVIDIA Corporation",
    "price": 125.50,
    "fear_greed": {
      "index": 65.5,
      "label": "贪婪"
    },
    "factors": [
      {
        "key": "ma",
        "name": "MA均线",
        "status": "📈 多头趋势",
        "bullish_signals": [...],
        "bearish_signals": [...]
      }
    ]
  }
]
```

## 开发指南

### 添加新的分析因子

1. 在 `server/src/service/strategies/multi_factor.py` 中添加新的分析方法：

```python
def _analyze_new_factor(self, data) -> FactorDetail:
    return FactorDetail(
        key="new_factor",
        name="新因子",
        status="状态描述",
        bullish_signals=[...],
        bearish_signals=[...],
    )
```

2. 在 `analyze()` 方法中调用并添加到 `factors` 列表
3. 前端会自动显示新因子（无需修改前端代码）

### 修改 API 接口

1. 修改 `server/src/controller/schemas.py` 中的 Pydantic 模型
2. 修改 `server/src/controller/index.py` 中的路由处理逻辑
3. 更新 `web/src/types/index.ts` 中的 TypeScript 类型
4. 更新 `web/src/api/client.ts` 中的 API 调用方法

### 代码规范

**Python**:

- 使用 `black` 格式化代码
- 遵循 PEP 8 规范
- 使用类型提示

```bash
black server/src/
```

**TypeScript/React**:

- 使用 ESLint 检查代码
- 遵循 React Hooks 最佳实践
- 使用函数式组件和 TypeScript

```bash
cd web && pnpm run lint
```

### 调试

- **前端**: 使用浏览器开发者工具和 React DevTools
- **后端**: 使用 FastAPI 自动文档 http://localhost:8080/docs ，查看控制台输出

## 部署

### Docker 部署

```bash
cd server

# 构建镜像
docker build -t stock-analysis .

# 运行容器
docker run -p 8080:8080 stock-analysis

# 使用中国镜像加速
docker build --build-arg USE_CHINA_MIRROR=true -t stock-analysis .

# 或使用 poetry taskipy 任务
poetry run task build
poetry run task run_docker
```

### 生产环境配置

1. **前端**: 设置 `VITE_API_BASE_URL` 环境变量，运行 `pnpm run build` 构建生产版本
2. **后端**: 设置环境变量 `PORT`（默认 8080），使用生产级 ASGI 服务器

## 常见问题

- **CORS 错误**: 检查 `server/main.py` 中的 `origins` 配置
- **API 请求失败**: 检查后端是否运行，检查 `web/vite.config.ts` 中的代理配置
- **数据获取失败**: 检查网络连接和股票代码格式（美股：NVDA，A 股：600519）

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！
