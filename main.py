from fastapi import FastAPI
from utils import routes
import uvicorn

app = FastAPI(title="ALPHAHUNT AI API")

app.include_router(routes.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)