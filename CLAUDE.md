# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A stock analysis system with multi-factor model support for both A-shares (Chinese market) and US stocks. The system provides technical and fundamental analysis with AI-powered synthesis using streaming responses.

**Architecture**: Monorepo with FastAPI backend (Python 3.12+) and React frontend (TypeScript/Vite).

## Development Commands

### Root Level
```bash
# Install all dependencies (root + web)
pnpm run install:web

# Start both backend and frontend concurrently
pnpm run dev

# Build frontend
pnpm run build:web

# Format code
pnpm run format
pnpm run format:check
```

### Backend (server/)
```bash
# Install dependencies
poetry install

# Run server standalone
poetry run python main.py
# or
cd server && poetry run start

# Build Docker image
poetry run task build
```

### Frontend (web/)
```bash
# Development server (port 3000)
pnpm run dev

# Production build
pnpm run build

# Preview production build
pnpm run preview

# Lint
pnpm run lint
```

## Architecture Overview

### Backend Structure (`server/src/`)

```
src/
├── agents/           # Agent-based analysis system
│   ├── coordinator/  # Main coordinator agent (LLM synthesis)
│   ├── fundamental/  # Fundamental analysis agent
│   ├── technical/    # Technical analysis agent
│   └── base.py       # Base agent with timing/state management
├── analyzer/         # Factor calculation modules
│   ├── technical_factors.py    # MA, MACD, RSI, KDJ, etc.
│   ├── fundamental_factors.py  # PE, PB, ROE, revenue growth
│   └── trend_analyzer.py       # Trend analysis
├── data_provider/    # Multi-source data management
│   ├── base.py       # BaseStockDataSource abstract class
│   ├── manager.py    # Data source manager with circuit breaker
│   ├── sources/      # Individual source implementations
│   └── stock_list.py # Stock list service
├── api/routes/       # FastAPI route handlers
├── storage/cache.py  # Caching layer (file + GCS support)
└── config.py         # Environment-based configuration
```

**Key Patterns:**
- **Data Source Hierarchy**: All data sources inherit from `BaseStockDataSource` with singleton pattern
- **Circuit Breaker**: `manager.py` implements circuit breaker pattern for data source resilience
- **Agent State**: Agents communicate via `AnalysisState` TypedDict, never direct sharing
- **SSE Streaming**: Agent progress sent via `progress_callback` for real-time frontend updates

### Frontend Structure (`web/src/`)

```
src/
├── components/
│   ├── layout/              # App shell (Main, PageRouter)
│   ├── stock-analysis/      # Main analysis UI
│   │   ├── DesktopPage.tsx  # Desktop layout
│   │   ├── desktop/         # Desktop-specific components
│   │   └── mobile/          # Mobile-specific components
│   ├── agent-report/        # Agent report visualization (SSE consumer)
│   └── theme/               # Theme providers
├── api/client.ts            # Axios client with SSE support
├── types/                   # TypeScript type definitions
└── index.tsx                # Entry point (dark mode fixed)
```

**Key Patterns:**
- **Mobile-First Detection**: `react-responsive` used for layout switching
- **SSE Event Handling**: `agent-report/` module consumes streaming agent progress
- **Dark Mode Only**: App forces dark mode via `document.documentElement.classList.add('dark')`

## Configuration

### Environment Variables (`server/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | Recommended | AI analysis (DeepSeek) |
| `OPENAI_API_KEY` | Optional | Fallback AI provider |
| `TUSHARE_TOKEN` | Optional | A-share data source priority |
| `PORT` | No | Server port (default: 8080) |
| `ENV` | No | `development` or `production` |
| `GCS_CACHE_BUCKET` | Production | Google Cloud Storage cache bucket |

**Data Source Priority (A-shares)**: Efinance (free) → Tushare (token) → AkShare (free) → Pytdx (free) → Baostock (free)

### Frontend Environment
```bash
VITE_API_BASE_URL=http://localhost:8080  # Backend API URL
```

## Important Constraints

### Git Workflow

- **Single commit per task**: When a task involves multiple subtasks, combine all changes into ONE commit. Do not create multiple commits for different parts of the same task - this makes review easier.

### Backend
- **Do NOT modify agent execution order or graph structure**
- **Do NOT merge or split agents** - `FundamentalAgent`, `TechnicalAgent`, `CoordinatorAgent` boundaries are fixed
- **Do NOT change `AnalysisState` schema** - state keys are contract between agents
- Agent failures should be recorded to `state.errors`, not raise exceptions
- Use `progress_callback(step, status, message, data)` for progress updates

### Frontend
- **TailwindCSS v4+ syntax**: `bg-linear-to-r` not `bg-gradient-to-r`, `bg-size-[...]` not `bg-[length:...]`
- **StepCard structure**: Outer border container + inner content container (prevents layout shift on selection)
- **Do NOT break SSE event handling** in `agent-report/` module

## Data Flow

1. **Request**: Frontend calls `/agent/analyze?symbol=NVDA`
2. **Streaming**: Backend sends SSE events with `AgentReportEvent` format
3. **Agent Execution**:
   - `FundamentalAgent` analyzes fundamentals → updates `state.fundamental_data`
   - `TechnicalAgent` calculates indicators → updates `state.technical_data`
   - `CoordinatorAgent` synthesizes both → generates final recommendation
4. **Progress**: Each agent sends progress via `progress_callback` → SSE → frontend `AgentReport` component
5. **Response**: Final state serialized to `StandardResponse<AnalysisReport>`

## Python Tooling

- **Poetry**: Dependency management and virtual environment
- **Black**: Code formatting (configured in pyproject.toml)
- **Python Version**: 3.12+ (enforced in pyproject.toml)

## TypeScript Tooling

- **Vite**: Build tool and dev server
- **TypeScript**: Project references (tsconfig.app.json, tsconfig.node.json)
- **ESLint**: Flat config (@eslint/js + typescript-eslint)
- **Prettier**: Code formatting
- **pnpm**: Package manager

## Testing

Backend tests located in `server/tests/`. Run with pytest from within the Poetry environment.

## Deployment

Backend includes Dockerfile with China mirror support:
```bash
docker build --build-arg USE_CHINA_MIRROR=true -t stock-analysis .
docker run -p 8080:8080 stock-analysis
```

Frontend deploys to GitHub Pages via `vite.config.ts` base path configuration.
