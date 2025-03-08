from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
def get_status():
    return {"message": "Debug app is running"}


@router.get("/health")
def get_health():
    return {"message": "Health check passed"}


@router.get("/info")
def get_info():
    return {"message": "Debug app information"}
