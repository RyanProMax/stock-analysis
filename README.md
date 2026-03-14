# Stock Analysis Web

股票分析系统前端应用。

## 功能

- 股票技术指标可视化
- 基本面数据分析
- AI 智能分析报告
- 响应式设计 (桌面/移动端)

## 前置要求

- **Node.js**: >= 24.0.0
- **包管理器**: pnpm
- **后端服务**: [stock-analysis-api](https://github.com/RyanProMax/stock-analysis-api)

## 快速开始

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm run dev
```

访问 <http://localhost:3000> 查看应用。

## 环境变量

创建 `.env.local` 文件：

```bash
VITE_API_BASE_URL=http://localhost:8080
```

## 构建部署

```bash
pnpm run build
```

构建产物在 `dist/` 目录。

## 相关项目

- [stock-analysis-api](https://github.com/RyanProMax/stock-analysis-api) - 后端 API 服务
