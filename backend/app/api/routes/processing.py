from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def processing_status():
    return {"module": "processing", "status": "ready"}