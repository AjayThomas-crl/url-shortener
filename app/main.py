from fastapi import FastAPI
from app.api.routes import router
from app.database import engine
from app.models import models

app = FastAPI()

# Create all tables stored in this metadata.
# This is equivalent to "Create Table" statements in raw SQL.
models.Base.metadata.create_all(bind=engine)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
