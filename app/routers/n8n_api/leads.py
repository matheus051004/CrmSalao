from fastapi import APIRouter

leads_router = APIRouter(
    prefix="/leads",
    include_in_schema=True,
)

@leads_router.get("/")
async def get_leads():
    pass