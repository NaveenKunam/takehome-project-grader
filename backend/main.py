from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import Base, engine
from backend.routers.submissions import router as submissions_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Take-Home Project Grader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(submissions_router)


@app.get("/health")
def health_check():
    return {"ok": True}
