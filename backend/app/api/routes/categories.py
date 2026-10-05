from fastapi import APIRouter

from app.schemas.category import CategoryDictionary
from app.services.categories import get_dictionary

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/dictionary", summary="Specializations and grades used for categorisation")
async def dictionary() -> CategoryDictionary:
    return get_dictionary()
