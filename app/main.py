import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.database import engine
from app.models import models

app = FastAPI(
    title="URL Shortener",
    description="A modern URL shortening service",
    version="1.0.0"
)

# Create tables only if they don't exist
models.Base.metadata.create_all(bind=engine)

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Health check endpoint for AWS monitoring
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "url-shortener"}

# Include router (must come after /health to avoid /{short_code} catching /health)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
