from datetime import date
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.kudago import kudago_client

app = FastAPI(
    title="City Events Aggregator",
    description="Агрегатор событий: концерты, митапы, выставки и другое",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/locations")
async def get_locations() -> list[dict]:
    try:
        return await kudago_client.get_locations()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"KudaGo API error: {exc}") from exc


@app.get("/api/categories")
async def get_categories() -> list[dict[str, str]]:
    return await kudago_client.get_categories()


@app.get("/api/events")
async def get_events(
    location: Annotated[str, Query(description="Slug города, например spb или msk")],
    categories: Annotated[str | None, Query(description="Категории через запятую")] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    date_from: Annotated[date | None, Query(alias="dateFrom")] = None,
    date_to: Annotated[date | None, Query(alias="dateTo")] = None,
    is_free: Annotated[bool | None, Query(alias="isFree")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=50)] = 12,
) -> dict:
    category_list = [c.strip() for c in categories.split(",") if c.strip()] if categories else None

    try:
        return await kudago_client.search_events(
            location=location,
            categories=category_list,
            search=search,
            date_from=date_from,
            date_to=date_to,
            is_free=is_free,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"KudaGo API error: {exc}") from exc
