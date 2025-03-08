from fastapi import APIRouter

router = APIRouter()


@router.get("/track")
def track_flight():
    return {"message": "Tracking your flight"}


@router.get("/arrival")
def get_arrival():
    return {"message": "Flight arrival information"}


@router.get("/departure")
def get_departure():
    return {"message": "Flight departure information"}
