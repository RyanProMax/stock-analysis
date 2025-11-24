import os
import uvicorn
from fastapi import FastAPI
from src.controller import index as controller

port = int(os.environ.get("PORT", 8080))

# Create the FastAPI app
app = FastAPI(
    title="Stock Analysis API",
    description="An API to perform technical analysis on stock symbols.",
    version="1.0.0",
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
