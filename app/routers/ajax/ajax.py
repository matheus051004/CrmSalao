from fastapi import APIRouter

router = APIRouter(
    prefix="/ajax",
    tags=["ajax"]
)

@router.get('/dashboard', name='ajax-dashboard')
async def dashboard():
    return {
        'status': 'ok',
        'message': 'Dashboard data'
    }