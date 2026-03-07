"""
路由注册模块 - 统一管理所有API路由
"""

from fastapi import APIRouter
from .stock import router as stock_router
from .agent import router as agent_router
from .valuation import router as valuation_router

# 创建主路由器
router = APIRouter()

# 注册股票分析相关路由
# /stock/* - 传统批量分析接口
router.include_router(stock_router, prefix="/stock", tags=["Stock Analysis"])

# 注册Agent分析相关路由
# /agent/* - LangGraph流式分析接口
router.include_router(agent_router, prefix="/agent", tags=["Agent Analysis"])

# 注册估值分析相关路由
# /valuation/* - DCF 估值分析接口
router.include_router(valuation_router, prefix="/valuation", tags=["Valuation"])
