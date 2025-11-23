from fastapi import APIRouter, HTTPException, Path

from src.service import index as service
from .schemas import AnalysisReportResponse

router = APIRouter()


@router.get(
    "/analyze/{symbol}",
    response_model=AnalysisReportResponse,
    summary="Analyze a stock symbol",
    tags=["Analysis"],
)
def analyze_stock(
    symbol: str = Path(
        ...,
        title="Stock Symbol",
        description="The stock symbol to analyze (e.g., 'NVDA', '600519')",
    )
):
    """
    Performs a technical analysis on the given stock symbol and returns a report.
    """
    print(f"symbol: {symbol}")
    report = service.run_stock_analysis(symbol)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not retrieve or analyze data for symbol '{symbol}'. Please ensure it's a valid symbol.",
        )
    return report
