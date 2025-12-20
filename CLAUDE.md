# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
# Install all dependencies (from root directory)
pnpm install

# Start both frontend and backend (recommended)
pnpm run dev

# Backend only
cd server
poetry install
poetry run python main.py

# Frontend only
cd web
pnpm install
pnpm run dev

# Run tests
cd server
poetry run python test_agent.py  # Test LangGraph agent

# Docker build
cd server
task build  # Build Docker image
task run_docker  # Run container
```

### Production
```bash
# Set environment variables
ENV=production
PORT=8080
TUSHARE_TOKEN=your_token
GCS_CACHE_BUCKET=your_bucket_name

# Docker deployment
docker run -d -p 8080:8080 --name stock-app stock-analysis
```

## Architecture

### Backend Architecture

The system uses a **layered architecture** with clear separation of concerns:

```
controller/    # API endpoints and request/response handling
    - index.py        # Route registration center
    - stock.py        # Traditional batch analysis endpoints
    - agent.py        # LangGraph agent streaming endpoint (/analyze)

service/       # Business logic layer
    - index.py        # Orchestration of stock analysis
    - factors/        # Factor analysis libraries
        - base.py     # Abstract base classes for factors
        - technical_factors.py    # Technical indicators (MA, RSI, MACD, etc.)
        - fundamental_factors.py  # Fundamental metrics (PE, PB, ROE, etc.)
        - qlib_158_factors.py    # 158 quantitative factors from Qlib
        - multi_factor.py        # Main analyzer combining all factors
    - data_loader/   # Data fetching from multiple sources
    - cache_util.py  # Caching abstraction (local/GCS)

agent/         # LangGraph workflow implementation
    - stock_analysis_agent.py     # Base agent with 5 nodes
    - extended_stock_agent.py     # Extended agent with financial reports
    - nodes/                      # Custom node implementations
```

### Key Design Patterns

1. **Factor Library Pattern**: Each analysis type (technical, fundamental, qlib) has its own library that inherits from `BaseFactor`. This makes it easy to add new analysis dimensions.

2. **LangGraph Workflow**: The agent architecture uses StateGraph to orchestrate analysis as a series of nodes:
   - Data Fetcher → Fundamental → Technical → Qlib → Decision
   - Each node emits progress updates via streaming

3. **Caching Strategy**: Two-level caching:
   - Memory cache for current session
   - Persistent cache (local files or GCS) with date-based keys

### Data Flow

1. Stock symbols enter via API endpoints
2. `DataLoader` fetches data from multiple sources (yfinance, tushare, akshare)
3. `MultiFactorAnalyzer` coordinates factor libraries
4. Results are cached and returned as structured responses

### Agent Integration

The LangGraph agent provides:
- **Streaming analysis** via Server-Sent Events (SSE) at `/agent/analyze`
- **Node-based architecture** for easy extension
- **Real-time progress updates** for each analysis step
- **Comprehensive scoring** combining all factors

### Agent Endpoints

#### Streaming Analysis
```
GET /agent/analyze?symbol={symbol}&refresh={bool}
```
Returns Server-Sent Events (SSE) with real-time analysis progress:
- `start` - Analysis initiated
- `progress` - Step-by-step progress updates
- `error` - Any errors during analysis
- `complete` - Final analysis result

### Agent Architecture

**Base Agent Flow:**
```
Data Fetcher → Fundamental → Technical → Qlib → Decision
```

**Extended Agent Flow (adds financial reports):**
```
Data Fetcher → Fundamental → Financial Report → Technical → Qlib → Decision
```

### Adding Custom Nodes

1. Create analyzer class:
```python
class CustomAnalyzer:
    async def analyze(self, symbol: str) -> Dict[str, Any]:
        return {"status": "success", "data": {...}}
```

2. Add node to agent:
```python
async def _custom_node(self, state: AgentState) -> AgentState:
    analyzer = CustomAnalyzer()
    result = await analyzer.analyze(state["symbol"])
    state["custom_data"] = result["data"]
    return state
```

3. Update workflow edges in `_build_graph()`

### Important Notes

- All factor calculations use the last row of data (most recent)
- Technical indicators are pre-calculated via StockDataFrame
- Caching keys include date to ensure fresh data daily
- The system supports both A-shares (via Tushare) and US stocks (via yfinance)
- Agent endpoint is at `/agent/analyze` (streaming only)
- Each node has independent error handling
