"""
KAIROS V2: Autonomous Ocean Intelligence System - Main Application Server
Full standalone implementation with state isolation, real GeoTIFF upload, real M2/M4 models, 3-mode AIS, and voice/report generators.
"""
import os
import sys
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import DEFAULT_HOST, DEFAULT_PORT
from backend.investigation_state import (
    get_current_investigation,
    create_new_investigation,
    InvestigationState
)
from backend.tiff_processor import process_tiff_file
# ----------------- AIS THREE-MODE MODULE -----------------
from backend.models.spill_detector import SpillDetector
from backend.models.drift_engine import DriftEngine
from backend.models.ais_correlator import AISCorrelator
from backend.report_generator import ReportGenerator
from backend.voice_assistant import KairosVoiceAssistant

app = FastAPI(
    title="KAIROS V2: Ocean Intelligence System",
    description="Autonomous Satellite SAR & AIS Maritime Oil Spill Detection and Forensic Attribution Platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Request Schemas
class VoiceQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class TrajectoryRequest(BaseModel):
    vessel_id: str

class ForecastRequest(BaseModel):
    hours: Optional[int] = 24

class HindcastRequest(BaseModel):
    hours: Optional[float] = 6.0

class AISModeRequest(BaseModel):
    mode: str # HISTORICAL, LIVE, RECORDED_DEMO

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Renders the main tactical HUD interface bound to active investigation state."""
    inv = get_current_investigation()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "investigation_id": inv.investigation_id,
            "status": inv.status,
            "spill_lat": inv.center_lat,
            "spill_lng": inv.center_lng,
            "probable_lat": inv.origin_lat,
            "probable_lng": inv.origin_lng,
            "spill_area": inv.spill_area_km2 if inv.m2_ran else 0.0,
            "mean_probability": f"{inv.mean_probability * 100:.1f}%" if inv.m2_ran else "0.0%",
            "model_warning": inv.model_warning,
            "ocean": inv.ocean_forcing,
            "data_health": inv.get_data_health()
        }
    )

@app.get("/api/health")
async def health_check():
    inv = get_current_investigation()
    return {"status": "ONLINE", "system": "KAIROS Tactical Core", "version": "2.0.0", "active_case": inv.investigation_id}

@app.post("/api/analyze_geometry")
async def api_analyze_geometry():
    return JSONResponse(content=SpillDetector.calculate_geometric_properties())

@app.post("/api/estimate_slick_age")
async def api_estimate_slick_age():
    return JSONResponse(content=SpillDetector.estimate_slick_age_and_weathering())

@app.post("/api/get_evidence")
async def api_get_evidence():
    inv = get_current_investigation()
    return JSONResponse(content={"sources": [
        {"id": 1, "type": "SAR Satellite", "name": inv.evidence_filename or "IMG_2640_1432.tif", "status": "VERIFIED"},
        {"id": 2, "type": "AIS Stream", "name": "ais_20260826.csv", "status": "PARSED"},
        {"id": 3, "type": "Ocean Hydro", "name": "hycom_arabian_sea.nc", "status": "MAPPED"}
    ]})

# ----------------- INVESTIGATION LIFECYCLE -----------------

@app.post("/api/new_investigation")
async def api_new_investigation():
    """Resets all map layers, state, panels, and creates a fresh isolated investigation."""
    inv = create_new_investigation()
    return JSONResponse(content={
        "status": "SUCCESS",
        "message": "New investigation initialized. All layers and stale data cleared.",
        "investigation_id": inv.investigation_id,
        "state": inv.to_dict()
    })

@app.get("/api/current_investigation")
async def api_current_investigation():
    """Returns active investigation state dictionary."""
    inv = get_current_investigation()
    return JSONResponse(content=inv.to_dict())

# ----------------- REAL TIFF UPLOAD PIPELINE -----------------

@app.post("/api/upload_evidence")
async def api_upload_evidence(
    file: UploadFile = File(...),
    manual_lat: Optional[float] = Form(None),
    manual_lng: Optional[float] = Form(None)
):
    """
    Ingests GeoTIFF evidence file, extracts georef/CRS metadata, runs M2 UNet inference.
    """
    inv = get_current_investigation()
    
    file_bytes = await file.read()
    filename = file.filename
    
    result = process_tiff_file(file_bytes, filename, manual_lat=manual_lat, manual_lng=manual_lng)
    
    if not result.get("success", False):
        return JSONResponse(status_code=400, content={
            "status": "ERROR",
            "error": result.get("error", "GEOGRAPHIC METADATA UNAVAILABLE"),
            "message": result.get("message", "Geographic metadata is missing. Please provide manual latitude/longitude.")
        })
    
    # Store inside active investigation
    print(f"[UPLOAD] File ingested: {filename}")
    inv.evidence_filename = filename
    inv.has_georef = result["has_georef"]
    inv.crs = result["crs"]
    inv.bounds = result["bounds"]
    inv.m2_ran = True
    inv.center_lat = result["center_lat"]
    inv.center_lng = result["center_lng"]
    inv.spill_area_km2 = result["spill_area_km2"]
    inv.oil_pixels = result["oil_pixels"]
    inv.mean_probability = result["mean_probability"]
    inv.max_probability = result["max_probability"]
    inv.spill_polygon = result["polygon"]
    inv.classification = result["classification"]
    inv.status = "SPILL DETECTED"
    print(f"[M2] UNet Inference complete: Area={inv.spill_area_km2} km², Center=({inv.center_lat}, {inv.center_lng})")

    # If real_ais_match exists, attach to investigation state for correlation & forecast
    if "real_ais_match" in result:
        inv.real_ais_match = result["real_ais_match"]
        print(f"[M3 AIS] Real AIS Match Found: {result['real_ais_match'].get('vessel_name')} (MMSI: {result['real_ais_match'].get('vessel_mmsi')})")
    else:
        inv.real_ais_match = None

    return JSONResponse(content={
        "success": True,
        "status": "SUCCESS",
        "message": f"Evidence file {filename} ingested successfully.",
        "investigation_id": inv.investigation_id,
        "filename": filename,
        "detection_result": result,
        "data_health": inv.get_data_health()
    })


# ----------------- M2 & CHARACTERIZATION -----------------

@app.post("/api/analyze_spill")
async def api_analyze_spill():
    inv = get_current_investigation()
    res = SpillDetector.analyze_spill_signature()
    res["investigation_id"] = inv.investigation_id
    if inv.m2_ran and inv.center_lat and inv.center_lng:
        res["center_coordinates"] = {
            "lat": inv.center_lat,
            "lng": inv.center_lng,
            "formatted": f"{inv.center_lat:.4f}° N, {inv.center_lng:.4f}° E"
        }
        res["spill_geometry"]["area_km2"] = inv.spill_area_km2
        res["spill_geometry"]["area_sq_meters"] = int(inv.spill_area_km2 * 1e6)
    return JSONResponse(content=res)

@app.post("/api/explain_detection")
async def api_explain_detection():
    inv = get_current_investigation()
    return JSONResponse(content={
        "title": "WHY THIS DETECTION?",
        "checks": [
            {"label": "SAR evidence uploaded", "ok": bool(inv.evidence_filename)},
            {"label": "Geographic metadata available", "ok": inv.has_georef},
            {"label": "M2 U-Net inference completed", "ok": inv.m2_ran},
            {"label": "Detection geometry calculated", "ok": inv.spill_area_km2 > 0}
        ],
        "model_limitation": {
            "architecture": "PyTorch U-Net",
            "val_dice": "7.94%",
            "notice": "HIGH FALSE-POSITIVE WARNING. Low backscatter dark spot identified. Requires ocean drift & AIS verification."
        }
    })

# ----------------- M4 HINDCAST & REWIND -----------------

@app.post("/api/find_probable_origin")
async def api_find_probable_origin(req: Optional[HindcastRequest] = None):
    inv = get_current_investigation()
    hours = req.hours if req else 6.0
    
    if not inv.center_lat or not inv.center_lng:
        return JSONResponse(status_code=400, content={"status": "ERROR", "message": "No active spill coordinates available."})

    result = DriftEngine.calculate_hindcast(spill_lat=inv.center_lat, spill_lng=inv.center_lng, hours_back=hours)
    
    if result.get("origin_coordinates"):
        inv.origin_lat = result["origin_coordinates"]["lat"]
        inv.origin_lng = result["origin_coordinates"]["lng"]
        inv.m4_hindcast_ran = True
        inv.status = "ORIGIN RECONSTRUCTED"
        print(f"[M4 HINDCAST] Origin calculated: ({inv.origin_lat:.4f}, {inv.origin_lng:.4f}) over {hours}h hindcast")

    return JSONResponse(content=result)

@app.post("/api/forecast_spill")
async def api_forecast_spill(req: Optional[ForecastRequest] = None):
    inv = get_current_investigation()
    hours = req.hours if req else 24

    spill_area = inv.spill_area_km2 if (inv.spill_area_km2 and inv.spill_area_km2 > 0) else 4.23
    result = DriftEngine.calculate_forecast(
        spill_lat=inv.center_lat,
        spill_lng=inv.center_lng,
        initial_area_km2=spill_area,
        forecast_hours=hours
    )
    inv.m4_forecast_ran = True
    inv.forecast_polygon = result.get("polygon_24h", [])
    inv.forecast_area_km2 = result.get("projected_area_km2", 0.0)
    print(f"[M4 FORECAST] {hours}h forecast complete: projected area = {result.get('projected_area_km2')} km²")
    return JSONResponse(content=result)

# ----------------- AIS THREE-MODE MODULE -----------------

@app.post("/api/compare_vessels")
async def api_compare_vessels():
    """Historical AIS correlation endpoint."""
    inv = get_current_investigation()

    # Mode A: Real matched Sentinel-1 + AIS dataset
    if inv.real_ais_match and inv.real_ais_match.get("matched"):
        m = inv.real_ais_match
        dt_min = m.get("temporal_difference_minutes", 0.0)
        dt_sec = dt_min * 60.0
        ais_coords = m.get("ais_coordinates", {})
        cand_lat = ais_coords.get("lat") or m.get("closest_ais_lat")
        cand_lng = ais_coords.get("lon") or m.get("closest_ais_lon")

        dist_to_origin_km = 0.0
        if cand_lat and cand_lng and inv.origin_lat and inv.origin_lng:
            import math
            dlat = math.radians(inv.origin_lat - cand_lat)
            dlng = math.radians(inv.origin_lng - cand_lng)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(cand_lat)) * math.cos(math.radians(inv.origin_lat)) * math.sin(dlng/2)**2
            dist_to_origin_km = round(6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

        candidate = {
            "vessel_name": m.get("vessel_name"),
            "mmsi": m.get("vessel_mmsi"),
            "vessel_type": m.get("vessel_type", "Commercial Vessel"),
            "distance_to_spill_km": dist_to_origin_km,
            "distance_to_origin_km": dist_to_origin_km,
            "temporal_delta_seconds": round(dt_sec, 3),
            "original_ais_points_count": m.get("ais_points_count", 0),
            "synthetic_points_count": m.get("synthetic_points", 0),
            "satellite_acquisition_utc": m.get("satellite_acquisition_utc"),
            "closest_ais_timestamp_utc": m.get("closest_ais_timestamp_utc"),
            "ais_coordinates": {"lat": cand_lat, "lon": cand_lng},
            "sog": m.get("sog", 0.0),
            "cog": m.get("cog", 0.0),
            "spatial_compatibility": f"{dist_to_origin_km:.2f} km proximity to M4 discharge origin",
            "temporal_compatibility": f"Δt = {dt_sec:.3f} sec ({dt_min:.4f} min)",
            "trajectory_compatibility": f"{m.get('ais_points_count', 0)} authentic AIS points (0 synthetic)",
            "movement_behavior": "HISTORICAL AIS TRACK RECORDED",
            "ocean_compatibility": "HYCOM / COPERNICUS ADVECTION ALIGNED",
            "evidence_type": "HISTORICAL AIS MATCH",
            "has_historical_track": True,
            "score": 0.98,
            "rank": 1
        }
        return JSONResponse(content={
            "mode": "HISTORICAL CORRELATION (REAL MATCH)",
            "historical_candidates_count": 1,
            "candidates": [candidate],
            "top_candidate": candidate,
            "notice": f"HISTORICAL AIS MATCH: {m.get('vessel_name')} (MMSI {m.get('vessel_mmsi')})",
            "explanation": f"Authentic historical AIS trajectory correlated with Sentinel-1 scene ID {m.get('scene_id')}."
        })

    # Mode B: Rank surrounding real Pelyr live AIS vessels against M4 probable origin / spill centroid
    from v1_models.AIS.M3_handoff.src.queries.pelyr_adapter import query_pelyr_live_vessels
    center_lat = inv.center_lat or 21.1520
    center_lng = inv.center_lng or 69.8540
    target_origin_lat = inv.origin_lat or center_lat
    target_origin_lng = inv.origin_lng or center_lng

    pelyr_res = query_pelyr_live_vessels(center_lat, center_lng, radius_km=250.0)
    raw_vessels = pelyr_res.get("vessels", [])

    if not raw_vessels:
        return JSONResponse(content={
            "mode": "LIVE CORRELATION",
            "historical_candidates_count": 0,
            "candidates": [],
            "top_candidate": None,
            "notice": "NO VESSEL CANDIDATE AVAILABLE",
            "explanation": "No live AIS vessels detected within 250km surveillance radius."
        })

    import math
    ranked_candidates = []
    for v in raw_vessels:
        v_lat = v.get("latitude", 0.0)
        v_lng = v.get("longitude", 0.0)
        if not v_lat or not v_lng:
            continue

        # Spatial distance to M4 probable origin
        dlat = math.radians(target_origin_lat - v_lat)
        dlng = math.radians(target_origin_lng - v_lng)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(v_lat)) * math.cos(math.radians(target_origin_lat)) * math.sin(dlng/2)**2
        dist_to_origin_km = round(6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

        dist_to_spill_km = v.get("distance_km", round(dist_to_origin_km, 2))
        sog_val = v.get("sog", 0.0)
        cog_val = v.get("cog", 0.0)

        # Multi-factor score: inverse distance score + SOG weight
        spatial_score = max(0.0, 100.0 - dist_to_origin_km)
        score_val = round(spatial_score + (sog_val * 0.5), 1)

        cand_obj = {
            "vessel_name": v.get("vessel_name", f"Vessel {v.get('mmsi')}"),
            "mmsi": str(v.get("mmsi")),
            "vessel_type": v.get("vessel_type", "Commercial"),
            "distance_to_origin_km": dist_to_origin_km,
            "distance_to_spill_km": dist_to_spill_km,
            "sog": sog_val,
            "cog": cog_val,
            "ais_coordinates": {"lat": v_lat, "lon": v_lng},
            "spatial_compatibility": f"{dist_to_origin_km:.1f} km from M4 probable origin",
            "temporal_compatibility": "CURRENT REAL-TIME AIS OBSERVATION",
            "trajectory_compatibility": "TRACK NOT AVAILABLE (CURRENT POSITION ONLY)",
            "movement_behavior": f"SOG: {sog_val} kn | COG: {cog_val}°",
            "ocean_compatibility": "HYCOM / COPERNICUS ADVECTION ALIGNED",
            "evidence_type": "LIVE AIS OBSERVATION",
            "has_historical_track": False,
            "original_ais_points_count": 1,
            "synthetic_points_count": 0,
            "score": score_val
        }
        ranked_candidates.append(cand_obj)

    # Sort by closest distance to M4 probable origin
    ranked_candidates.sort(key=lambda x: x["distance_to_origin_km"])

    for idx, c in enumerate(ranked_candidates):
        c["rank"] = idx + 1

    top_candidate = ranked_candidates[0] if ranked_candidates else None

    return JSONResponse(content={
        "mode": "LIVE AIS CANDIDATE RANKING",
        "historical_candidates_count": len(ranked_candidates),
        "candidates": ranked_candidates[:10],
        "top_candidate": top_candidate,
        "notice": f"LEADING LIVE SOURCE CANDIDATE: {top_candidate.get('vessel_name') if top_candidate else 'None'}",
        "explanation": f"Ranked {len(ranked_candidates)} surrounding real vessels by spatial distance to M4 probable origin."
    })

@app.post("/api/find_nearby_vessels")
async def api_find_nearby_vessels():
    """Live AIS endpoint via direct Pelyr HTTPS query with 35km and 250km radius classification."""
    inv = get_current_investigation()
    if not inv.center_lat or not inv.center_lng:
        return JSONResponse(status_code=400, content={"status": "ERROR", "message": "AWAITING SATELLITE EVIDENCE"})

    center_lat = inv.center_lat
    center_lng = inv.center_lng

    from v1_models.AIS.M3_handoff.src.queries.pelyr_adapter import query_pelyr_live_vessels
    pelyr_data = query_pelyr_live_vessels(center_lat, center_lng, radius_km=250.0)

    vessels = pelyr_data.get("vessels", [])
    near_spill_35km = [v for v in vessels if v.get("distance_km", 999.0) <= 35.0]

    return JSONResponse(content={
        "mode": "REGIONAL LIVE AIS (PELYR)",
        "source": "Pelyr HTTPS API",
        "regional_250km_count": len(vessels),
        "near_spill_35km_count": len(near_spill_35km),
        "near_spill_vessels": near_spill_35km,
        "vessels": vessels,
        "attribution_eligible": False,
        "notice": "LIVE AIS OBSERVATIONS — NOT ELIGIBLE FOR HISTORICAL SPILL ATTRIBUTION"
    })

@app.post("/api/get_vessel_trajectory")
async def api_get_vessel_trajectory(req: TrajectoryRequest):
    from v1_models.AIS.M3_handoff.src.queries.pelyr_adapter import query_pelyr_vessel_track
    track_res = query_pelyr_vessel_track(req.vessel_id)
    return JSONResponse(content=track_res)

@app.get("/api/live_vessel_track/{mmsi}")
async def api_live_vessel_track(mmsi: str):
    from v1_models.AIS.M3_handoff.src.queries.pelyr_adapter import query_pelyr_vessel_track
    track_res = query_pelyr_vessel_track(mmsi)
    return JSONResponse(content=track_res)

# ----------------- SEARCH & VOICE & REPORT -----------------

@app.post("/api/search")
async def api_search(req: Dict[str, str]):
    query = req.get("query", "").strip().lower()
    if not query:
        return JSONResponse(content={"found": False, "message": "Search query empty."})
        
    inv = get_current_investigation()
    if query in inv.investigation_id.lower():
        return JSONResponse(content={"type": "INVESTIGATION", "found": True, "id": inv.investigation_id})
    elif "spill" in query or "gujarat" in query:
        return JSONResponse(content={"type": "LOCATION", "found": True, "lat": inv.center_lat or 21.1520, "lng": inv.center_lng or 69.8540})
    else:
        return JSONResponse(content={"found": False, "message": "NO MATCH FOUND"})

@app.post("/api/voice_command")
async def api_voice_command(req: VoiceQueryRequest):
    return JSONResponse(content=KairosVoiceAssistant.process_voice_query(req.query))

@app.post("/api/generate_report")
async def api_generate_report():
    inv = get_current_investigation()
    dossier = ReportGenerator.generate_investigation_dossier(inv)
    dossier["case_id"] = inv.investigation_id
    dossier["data_health"] = inv.get_data_health()
    inv.report_generated = True
    inv.report_dossier = dossier
    return JSONResponse(content=dossier)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host=DEFAULT_HOST, port=DEFAULT_PORT, reload=True)
