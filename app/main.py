from fastapi import FastAPI
from app.config.settings import Settings
from app.routers.search import router as search_router
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def get_settings():
    return Settings()


def create_application():
    # Initialize settings
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
    )

    # Add routers
    app.include_router(search_router)

    @app.get("/")
    async def root():
        return {"message": "Welcome to RAG API"}

    @app.get("/health")
    async def health_check():
        logging.info("Health endpoint was called")
        return {"status": "Ok"}

    return app


app = create_application()
