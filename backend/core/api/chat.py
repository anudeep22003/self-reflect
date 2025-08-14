from fastapi import APIRouter

router = APIRouter(prefix="/record")


@router.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for extension to test server connectivity."""
    return {"status": "ok", "message": "Server is running"}
