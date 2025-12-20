import os
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.controller import index as controller
from src.controller.schemas import StandardResponse
from src.env import is_development

port = int(os.environ.get("PORT", 8080))

# Create the FastAPI app
app = FastAPI(
    title="Stock Analysis API",
    description="An API to perform technical analysis on stock symbols.",
    version="1.0.0",
)

origins = [
    "http://localhost:3000",
    "https://ryanpromax.github.io",
    "https://ryanai.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的域名列表
    allow_credentials=True,  # 是否允许携带 Cookie 等凭证
    allow_methods=["*"],  # 允许的方法 (GET, POST, OPTIONS 等)
    allow_headers=["*"],  # 允许的 Header (Content-Type, Authorization 等)
)


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=StandardResponse(
            status_code=400,
            data=None,
            err_msg=f"请求参数验证失败: {str(exc)}",
        ).model_dump(),
    )


# General error handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=StandardResponse(
            status_code=500,
            data=None,
            err_msg=f"服务器内部错误: {str(exc)}",
        ).model_dump(),
    )


# Routers
app.include_router(controller.router)


@app.get("/", tags=["Root"])
def read_root():
    return StandardResponse(
        status_code=200,
        data={"message": "Welcome to the Stock Analysis API. Go to /docs for API documentation."},
        err_msg=None,
    )


@app.get("/ping", tags=["Health"])
async def ping():
    """Health check endpoint to verify server availability"""
    return StandardResponse(
        status_code=200,
        data={"message": "pong", "status": "healthy"},
        err_msg=None,
    )


def start():
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=is_development())


if __name__ == "__main__":
    start()
