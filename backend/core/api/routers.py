from fastapi import APIRouter

from .chat import router as browser_window_events_router

router = APIRouter(prefix="/api")
router.include_router(browser_window_events_router)
