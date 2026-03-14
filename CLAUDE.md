# CLAUDE.md

Stock Analysis Web 前端项目。

## 技术栈

- React 19
- Vite 7
- TypeScript
- Ant Design 6
- TailwindCSS 4
- pnpm

## 开发命令

```bash
# 安装依赖
pnpm install

# 开发服务器 (port 3000)
pnpm run dev

# 生产构建
pnpm run build

# 代码格式化
pnpm run format
```

## 项目结构

```
src/
├── components/       # React 组件
│   ├── layout/       # 布局组件
│   ├── stock-analysis/  # 股票分析页面
│   └── agent-report/    # Agent 报告组件
├── api/              # API 客户端
├── types/            # TypeScript 类型
└── index.tsx         # 入口文件
```

## 环境变量

| 变量 | 说明 |
|------|------|
| VITE_API_BASE_URL | 后端 API 地址 |

## 部署

构建后部署到 GitHub Pages。

## 后端服务

本项目需要搭配后端 API 服务使用：

- **仓库**: <https://github.com/RyanProMax/stock-analysis-api>
- **本地开发**: 启动后端服务后，设置 `VITE_API_BASE_URL=http://localhost:8080`
