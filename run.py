import uvicorn
from utils.config import settings
from utils.logger import log


def main() -> None:
    """
    Start the FastAPI app using uvicorn, pointing to fastapi_project.main:app.

    Environment variables (optional):
      - HOST: bind address (default: 0.0.0.0)
      - PORT: port number (default: 8000)
      - WORKERS: number of worker processes (default: 1)
      - RELOAD: enable auto-reload on file changes (default: true)

    Note: Uvicorn does not support reload with workers > 1. If RELOAD is true,
    workers will be forced to 1.
    """
    host = settings.HOST
    port = settings.PORT
    workers = settings.WORKERS
    reload_flag = str(settings.RELOAD).strip().lower() in {"1", "true", "yes", "on"}

    # Ensure compatibility: reload requires a single worker
    if reload_flag and workers != 1:
        workers = 1
    log.info(f"Starting server at {host}:{port} with {workers} worker(s)")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload_flag,
        workers=workers,
        factory=False,
    )


if __name__ == "__main__":
    main()


