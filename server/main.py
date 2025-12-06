import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.controller import index as controller

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

# Include routers
app.include_router(controller.router, prefix="/stock")


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to the Stock Analysis API. Go to /docs for API documentation."
    }


def start():
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    start()
