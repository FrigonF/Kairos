from fastapi import FastAPI, Query
from datetime import datetime
import polars as pl
import json

from src.queries.nearby_vessels import find_nearby_vessels
from src.ranking.rank_candidates import rank_candidates

app = FastAPI(
    title="KAIROS AIS Intelligence API",
    description="AIS vessel detection and trajectory API for KAIROS",
    version="1.0.0",
)

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AIS_FILE = BASE_DIR / "data" / "processed" / "ais_clean.parquet"
TRAJECTORY_FILE = BASE_DIR / "data" / "processed" / "trajectories" / "trajectories.geojson"


@app.get("/")
def root():
    return {
        "project": "KAIROS",
        "module": "M3 - AIS/Data Engineering",
        "status": "online",
        "endpoints": [
            "/api/ais/vessels/nearby",
            "/api/ais/candidates",
            "/api/ais/vessels/{mmsi}",
            "/api/ais/vessels/{mmsi}/trajectory",
        ],
    }


@app.get("/api/ais/vessels/nearby")
def nearby_vessels(
    lat: float,
    lon: float,
    time: str,
    radius_km: float = Query(20, gt=0),
    time_window_minutes: int = Query(30, gt=0),
):
    spill_time = datetime.fromisoformat(time)

    vessels = find_nearby_vessels(
        spill_lat=lat,
        spill_lon=lon,
        spill_time=spill_time,
        radius_km=radius_km,
        time_window_minutes=time_window_minutes,
    )

    return {
        "spill": {
            "latitude": lat,
            "longitude": lon,
            "time": time,
        },
        "radius_km": radius_km,
        "time_window_minutes": time_window_minutes,
        "count": len(vessels),
        "vessels": vessels,
    }


@app.get("/api/ais/candidates")
def candidates(
    lat: float,
    lon: float,
    time: str,
    radius_km: float = Query(20, gt=0),
    time_window_minutes: int = Query(30, gt=0),
):
    spill_time = datetime.fromisoformat(time)

    vessels = find_nearby_vessels(
        spill_lat=lat,
        spill_lon=lon,
        spill_time=spill_time,
        radius_km=radius_km,
        time_window_minutes=time_window_minutes,
    )

    ranked = rank_candidates(
        vessels,
        radius_km,
        time_window_minutes,
    )

    return {
        "spill": {
            "latitude": lat,
            "longitude": lon,
            "time": time,
        },
        "ranking_method": {
            "distance": "40%",
            "time": "30%",
            "trajectory": "20%",
            "vessel_type": "10%",
        },
        "count": len(ranked),
        "candidates": ranked,
    }


@app.get("/api/ais/vessels/{mmsi}")
def vessel_info(mmsi: int):

    df = pl.read_parquet(AIS_FILE)

    vessel = (
        df.filter(pl.col("mmsi") == mmsi)
        .sort("base_date_time")
    )

    if vessel.height == 0:
        return {"error": "Vessel not found"}

    first = vessel.row(0, named=True)

    return {
        "mmsi": mmsi,
        "vessel_name": first["vessel_name"],
        "imo": first["imo"],
        "call_sign": first["call_sign"],
        "vessel_type": first["vessel_type"],
        "length": first["length"],
        "width": first["width"],
        "draft": first["draft"],
        "position_count": vessel.height,
        "first_seen": str(vessel["base_date_time"].min()),
        "last_seen": str(vessel["base_date_time"].max()),
    }


@app.get("/api/ais/vessels/{mmsi}/trajectory")
def vessel_trajectory(mmsi: int):

    with open(TRAJECTORY_FILE) as f:
        geojson = json.load(f)

    for feature in geojson["features"]:
        if feature["properties"]["mmsi"] == mmsi:
            return feature

    return {
        "error": "Trajectory not found",
        "mmsi": mmsi,
    }
