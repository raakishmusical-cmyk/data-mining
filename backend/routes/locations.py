import json
import os
import sys

from fastapi import APIRouter, HTTPException
from datetime import datetime


router = APIRouter(tags=["Locations"])


def resource_path(relative_path):
    """
    Get the correct path for both normal Python execution
    and PyInstaller EXE execution.
    """

    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )

    return os.path.join(base_path, relative_path)


LOCATIONS_PATH = resource_path("locations.json")


@router.get("/locations")
async def get_locations():
    """Returns parsed state and district mapping from locations.json."""

    if not os.path.exists(LOCATIONS_PATH):
        raise HTTPException(
            status_code=404,
            detail=(
                "Locations database file not found: "
                f"{LOCATIONS_PATH}"
            )
        )

    try:

        with open(
            LOCATIONS_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return {
            "success": True,
            "message": "Fetched locations dataset.",
            "data": data,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to read locations dataset: {str(e)}"
        )