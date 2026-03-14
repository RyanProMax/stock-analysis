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
├── .github/
│   └── workflows/
│       └── docker-publish.yml  # 仅后端部署
├── .gitignore            # Python 标准
├── .python-version       # 3.12
├── .dockerignore
├── Dockerfile
├── .env.example
├── CLAUDE.md             # 后端专用
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
├── .github/
│   └── workflows/
│       └── deploy-web.yml     # 仅前端部署
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
| `server/src/` | 复制到新项目 `src/` |
| `server/tests/` | 复制到新项目 `tests/` |
| `server/main.py` | 复制到新项目根目录 |
| `server/pyproject.toml` | 复制到新项目根目录 |
| `server/poetry.lock` | 复制到新项目根目录 |
| `server/.python-version` | 复制到新项目根目录 |
| `server/.dockerignore` | 复制到新项目根目录 |
| `server/Dockerfile` | 复制到新项目根目录 |
| `server/.env.example` | 复制到新项目根目录 |
| `server/.env` | **不复制** (敏感信息，用户手动创建) |
| `server/.cache/` | **不复制** (缓存目录) |
| `server/.venv/` | **不复制** (虚拟环境) |
| `.github/workflows/docker-publish.yml` | 复制到新项目 |
| `pyrightconfig.json` | 复制到新项目 |

### 前端项目文件

| 文件/目录 | 操作 |
|-----------|------|
| `server/` | 删除整个目录 |
| `web/src/` | 移动到根目录 `src/` |
| `web/public/` | 移动到根目录 `public/` |
| `web/package.json` | 移动到根目录 |
| `web/pnpm-lock.yaml` | 移动到根目录 |
| `web/.*` (配置文件) | 移动到根目录 |
| `web/index.html` | 移动到根目录 |
| `web/*.ts/*.json` | 移动到根目录 |
| `web/dist/` | **不移动** (构建产物) |
| `web/node_modules/` | **不移动** (依赖) |
| `package.json` (根目录) | 删除 (用 web/package.json 替换) |
| `pnpm-lock.yaml` (根目录) | 删除 |
| `node_modules/` (根目录) | 删除 |
| `.python-version` | 删除 |
| `pyrightconfig.json` | 删除 |
| `.github/workflows/docker-publish.yml` | 删除 |

### 两边都需要的文件 (内容不同)

| 文件 | 后端内容 | 前端内容 |
|------|----------|----------|
| `.gitignore` | Python + Poetry + venv | Node.js + pnpm + IDE |
| `CLAUDE.md` | 后端架构、API 文档 | 前端架构、组件文档 |
| `README.md` | 后端说明 | 前端说明 |

## 配置更新

### 后端 `pyproject.toml`

更新项目名称：

```toml
[project]
name = "stock-analysis-api"
# 其他配置保持不变
```

### 后端 `docker-publish.yml`

移除 `server/` 路径前缀：

```yaml
# 原来
context: ./server
file: ./server/Dockerfile

# 改为
context: .
file: ./Dockerfile
```

删除 `Copy README.md to server directory` 步骤。

paths 触发条件更新：

```yaml
paths:
  - 'src/**'
  - 'main.py'
  - '.github/workflows/docker-publish.yml'
```

### 前端 `package.json`

使用原 `web/package.json`，更新项目名：

```json
{
  "name": "stock-analysis-web"
}
```

### 前端 `deploy-web.yml`

移除 `web/` 路径前缀：

```yaml
# 原来
working-directory: ./web
cache-dependency-path: './web/pnpm-lock.yaml'
path: './web/dist'

# 改为
# working-directory: . (移除此行)
cache-dependency-path: './pnpm-lock.yaml'
path: './dist'
```

paths 触发条件更新：

```yaml
paths:
  - 'src/**'
  - '.github/workflows/deploy-web.yml'
```

### 前端 `lint-staged.config.mjs`

路径从 `web/**` 改为 `**`（如果需要）。

## 实施步骤

### 前置准备

1. **确保工作区干净**
   ```bash
   git status --porcelain
   # 应该为空
   ```

2. **创建备份分支**
   ```bash
   git branch backup-pre-split
   ```

### 步骤 1: 创建后端项目

1. 创建目录并复制文件
   ```bash
   mkdir -p ~/projects/stock-analysis-api
   cp -r server/src ~/projects/stock-analysis-api/
   cp -r server/tests ~/projects/stock-analysis-api/
   cp server/main.py server/pyproject.toml server/poetry.lock ~/projects/stock-analysis-api/
   cp server/.python-version server/.dockerignore server/Dockerfile server/.env.example ~/projects/stock-analysis-api/
   cp pyrightconfig.json ~/projects/stock-analysis-api/
   mkdir -p ~/projects/stock-analysis-api/.github/workflows
   cp .github/workflows/docker-publish.yml ~/projects/stock-analysis-api/.github/workflows/
   ```

2. 创建 Python 标准 `.gitignore`

3. 更新 `pyproject.toml` 项目名

4. 更新 `docker-publish.yml` 路径

5. 编写后端专用 `CLAUDE.md` 和 `README.md`

6. 初始化 Git 仓库
   ```bash
   cd ~/projects/stock-analysis-api
   git init
   git add .
   git commit -m "Initial commit: stock-analysis-api"
   ```

### 步骤 2: 重构前端项目

1. 删除 server 相关
   ```bash
   rm -rf server/ .python-version pyrightconfig.json
   rm .github/workflows/docker-publish.yml
   ```

2. 移动 web 内容到根目录
   ```bash
   # 移动文件（排除 dist 和 node_modules）
   mv web/src ./
   mv web/public ./
   mv web/package.json web/pnpm-lock.yaml ./
   mv web/index.html ./
   mv web/.prettierrc.json web/.prettierignore web/.stylelintrc ./
   mv web/eslint.config.ts web/tsconfig.json web/tsconfig.app.json web/tsconfig.node.json ./
   mv web/vite.config.ts web/postcss.config.ts ./

   # 删除空的 web 目录
   rm -rf web/
   rm -rf node_modules/
   ```

3. 更新 `.gitignore` 为 Node.js 标准

4. 更新 `package.json` 项目名

5. 更新 `deploy-web.yml` 路径

6. 更新 `lint-staged.config.mjs` 路径

7. 更新前端专用 `CLAUDE.md` 和 `README.md`

8. 提交变更
   ```bash
   git add .
   git commit -m "refactor: split monorepo - web only"
   ```

### 步骤 3: 重命名项目目录

```bash
cd ~/projects
mv stock-analysis stock-analysis-web
```

## 验证

- [ ] 后端项目: `cd ~/projects/stock-analysis-api && poetry install && poetry run python main.py`
- [ ] 前端项目: `cd ~/projects/stock-analysis-web && pnpm install && pnpm run dev`
- [ ] 前端可以调用后端 API (http://localhost:8080)
- [ ] 后端项目 Git 状态: `git log --oneline -1` 显示 initial commit
- [ ] 前端项目 Git 状态: `git log --oneline -3` 保留历史
