from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def stats_status():
    return {"module": "stats", "status": "ready"}