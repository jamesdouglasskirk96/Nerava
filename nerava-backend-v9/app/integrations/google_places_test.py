import argparse
import asyncio
import logging
from typing import Optional

from .google_places_client import search_places_near


async def run_test(
    lat: float,
    lng: float,
    query: Optional[str],
    radius: int,
    limit: int,
    keyword: Optional[str],
) -> None:
    logging.info(
        "[GooglePlacesTest] lat=%s lng=%s query=%s radius=%s limit=%s keyword=%s",
        lat,
        lng,
        query,
        radius,
        limit,
        keyword,
    )
    results = await search_places_near(
        lat=lat,
        lng=lng,
        query=query,
        types=None,
        radius_m=radius,
        limit=limit,
        keyword=keyword,
    )
    logging.info("[GooglePlacesTest] Found %s places", len(results))
    for place in results:
        logging.info(
            "[GooglePlacesTest] %s (%s) rating=%s",
            place.name,
            place.address,
            place.rating,
        )


def main():
    parser = argparse.ArgumentParser(description="Quick Google Places test utility")
    parser.add_argument("--lat", type=float, required=True, help="Latitude")
    parser.add_argument("--lng", type=float, required=True, help="Longitude")
    parser.add_argument("--query", type=str, default=None, help="Text search query")
    parser.add_argument("--radius", type=int, default=1000, help="Radius in meters")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--keyword", type=str, default=None, help="Keyword filter")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(
        run_test(
            lat=args.lat,
            lng=args.lng,
            query=args.query,
            radius=args.radius,
            limit=args.limit,
            keyword=args.keyword,
        )
    )


if __name__ == "__main__":
    main()

