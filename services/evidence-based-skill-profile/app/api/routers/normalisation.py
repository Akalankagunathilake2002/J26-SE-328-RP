from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.normalisation.normaliser import get_normaliser
from app.schemas.normalisation import NormalisedTerm, NormaliseRequest

router = APIRouter(tags=["normalisation"])


@router.post("/normalise", response_model=list[NormalisedTerm])
async def normalise_terms(request: NormaliseRequest) -> list[NormalisedTerm]:
    """Map written skill terms ("Javascrpit", "made neural networks") to standard skill IDs."""
    return await run_in_threadpool(get_normaliser().normalise, request.terms)
