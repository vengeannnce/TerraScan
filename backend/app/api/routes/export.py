from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def export_status():
    return {"module": "export", "status": "ready"}