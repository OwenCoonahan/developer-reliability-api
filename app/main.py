from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import developers

app = FastAPI(
    title="Developer Reliability Score API",
    description="Scores energy project developers based on interconnection queue track records",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(developers.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
