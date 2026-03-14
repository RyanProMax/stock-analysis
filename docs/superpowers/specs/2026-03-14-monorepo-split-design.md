# Monorepo 拆分设计文档

## 背景

当前 `stock-analysis` 是一个 monorepo 项目，包含 FastAPI 后端 (`server/`) 和 React 前端 (`web/`)。为了更好的项目管理和独立部署，需要将其拆分为两个独立仓库。

## 目标

将 monorepo 拆分为两个标准化项目：

| 项目 | 类型 | 位置 | Git 历史 |
|------|------|------|----------|
| `stock-analysis-web` | React 前端 (Vite) | `~/projects/stock-analysis` (重命名) | 保留原历史 |
| `stock-analysis-api` | FastAPI 后端 | `~/projects/stock-analysis-api` (新建) | 全新仓库 |

## 项目结构

### 后端项目 (`stock-analysis-api`)

```
stock-analysis-api/
├── .git/                 # 全新 Git 仓库
├── .github/              # GitHub Actions
├── .gitignore            # Python 标准
├── .python-version       # 3.12
├── .dockerignore
├── Dockerfile
├── .env.example
���── CLAUDE.md             # 后端专用
├── README.md             # 后端专用
├── pyproject.toml        # 项目名: stock-analysis-api
├── poetry.lock
├── main.py               # FastAPI 入口
├── src/
│   ├── __init__.py
│   ├── agents/
│   ├── analyzer/
│   ├── api/
│   ├── config.py
│   ├── core/
│   ├── data_provider/
│   ├── model/
│   ├── notification/
│   ├── storage/
│   └── utils/
└── tests/
```

### 前端项目 (`stock-analysis-web`)

```
stock-analysis-web/
├── .git/                 # 保留原历史
├── .github/              # 保留
├── .gitignore            # Node.js 标准
├── .husky/
├── .vscode/
├── .prettierrc.json
├── .prettierignore
├── .stylelintrc
├── eslint.config.ts
├── lint-staged.config.mjs
├── CLAUDE.md             # 前端专用
├── README.md             # 前端专用
├── package.json          # 原 web/package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── index.html
├── postcss.config.ts
├── public/
├── src/                  # 原 web/src/
└── docs/
```

## 文件处理清单

### 后端项目文件

| 来源 | 操作 |
|------|------|
| `server/*` | 复制所有内容到新项目根目录 |
| `server/.env` | 不复制 (敏感信息) |
| `.github/` | 复制到新项目 |
| `.dockerignore` | 复制 |
| `Dockerfile` | 复制 |
| `pyrightconfig.json` | 复制 |

### 前端项目文件

| 文件/目录 | 操作 |
|-----------|------|
| `server/` | 删除整个目录 |
| `web/*` | 移动到根目录 |
| `web/.*` | 移动到根目录 |
| `package.json` | 替换为 `web/package.json` 内容 |
| `pnpm-lock.yaml` | 替换为 `web/pnpm-lock.yaml` |
| `node_modules/` | 删除根目录的，保留 web 的 |
| `.python-version` | 删除 |
| `pyrightconfig.json` | 删除 |

### 两边都需要的文件 (内容不同)

| 文件 | 后端内容 | 前端内容 |
|------|----------|----------|
| `.gitignore` | Python + Poetry + venv | Node.js + pnpm + IDE |
| `CLAUDE.md` | 后端架构、API 文档 | 前端架构、组件文档 |
| `README.md` | 后端说明 | 前端说明 |

## 配置更新

### 后端 `pyproject.toml`

```toml
[project]
name = "stock-analysis-api"
# 其他配置保持不变
```

### 前端 `package.json`

使用原 `web/package.json`，更新项目名：

```json
{
  "name": "stock-analysis-web",
  "scripts": {
    "dev": "vite",
    "build": "tsc -p tsconfig.app.json && vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  }
}
```

### 前端 `vite.config.ts`

更新 API 代理配置，指向独立后端地址。

## 实施步骤概要

1. **创建后端项目**
   - 创建 `~/projects/stock-analysis-api` 目录
   - 复制 `server/` 内容到新项目
   - 创建 Python 标准 `.gitignore`
   - 更新 `pyproject.toml` 项目名
   - 编写后端专用 `CLAUDE.md` 和 `README.md`
   - 初始化 Git 仓库

2. **重构前端项目**
   - 移动 `web/*` 到根目录
   - 删除 `server/` 目录
   - 删除 Python 相关文件
   - 更新 `.gitignore` 为 Node.js 标准
   - 更新 `package.json`
   - 更新前端专用 `CLAUDE.md` 和 `README.md`
   - 删除空目录和临时文件

3. **重命名项目目录**
   - 将 `stock-analysis` 重命名为 `stock-analysis-web`

## 验证

- [ ] 后端项目可以 `poetry install && poetry run python main.py`
- [ ] 前端项目可以 `pnpm install && pnpm run dev`
- [ ] 前端可以调用后端 API
- [ ] 两个项目 Git 状态正常
