import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# V2 Storage Directories
DATA_DIR = BASE_DIR / "data"
INVESTIGATIONS_DIR = DATA_DIR / "investigations"
MODELS_DIR = BASE_DIR / "backend" / "models"
CHECKPOINT_PATH = MODELS_DIR / "checkpoints" / "best_model.pth"
TEST_EVIDENCE_DIR = BASE_DIR / "TEST_EVIDENCE"
VESSEL_TEST_CASES_DIR = TEST_EVIDENCE_DIR / "satellite" / "vessel_test_cases"
RECORDED_TRACKS_MANIFEST = VESSEL_TEST_CASES_DIR / "vessel_test_cases_manifest.json"
RECORDED_TRACKS_DIR = VESSEL_TEST_CASES_DIR / "trajectories"

# System defaults
DEFAULT_PORT = int(os.getenv("PORT", "8000"))
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
MODEL_VAL_DICE = 0.0794  # 7.94% validation Dice score
MODEL_WARNING = "M2 MODEL: PyTorch U-Net | VAL DICE: 7.94% | HIGH FALSE-POSITIVE WARNING"

# Default Case Metadata (Fallback)
CASE_ID = "KA-026-IND"
CASE_NAME = "Gujarat / Arabian Sea Oil Discharge Investigation"
CASE_DATE_UTC = "2026-09-12T10:24:00Z"
CASE_STATUS = "INVESTIGATION ACTIVE"
SPILL_CENTER_LAT = 21.1520
SPILL_CENTER_LNG = 69.8540
PROBABLE_ORIGIN_LAT = 20.8450
PROBABLE_ORIGIN_LNG = 69.5210
SPILL_AREA_SQ_KM = 16.5
DETECTION_CONFIDENCE = 0.67
UNCERTAINTY_RADIUS_KM = 8.6
HINDCAST_TIME_WINDOW = "13:40 - 15:10 UTC"

OCEAN_METADATA = {
    "current_speed_kn": 1.42,
    "current_direction_deg": 135.0,
    "current_direction_str": "SE",
    "wind_speed_kn": 12.6,
    "wind_direction_deg": 225.0,
    "wind_direction_str": "SW",
    "wave_height_m": 1.3,
    "wave_period_s": 0.8,
    "sea_surface_temp_c": 28.4,
    "water_salinity_psu": 35.2
}

INVESTIGATION_STEPS = [
    {"id": 1, "step_num": "1", "name": "Evidence", "icon": "📄", "detail": "3/3 Sources Loaded", "status": "completed"},
    {"id": 2, "step_num": "2", "name": "Spill Detection", "icon": "💧", "detail": "Area: 16.5 km²", "status": "completed"},
    {"id": 3, "step_num": "3", "name": "Characterization", "icon": "🗂️", "detail": "Confidence: 67%", "status": "completed"},
    {"id": 4, "step_num": "4", "name": "Rewind", "icon": "🔄", "detail": "Reconstructing Origin", "status": "completed"},
    {"id": 5, "step_num": "5", "name": "Vessel Analysis", "icon": "🚢", "detail": "41 Relevant Vessels", "status": "in_progress"},
    {"id": 6, "step_num": "6", "name": "Correlation", "icon": "🔍", "detail": "3 Suspect Candidates", "status": "pending"},
    {"id": 7, "step_num": "7", "name": "Forecast", "icon": "🌊", "detail": "Generating Projection", "status": "pending"},
    {"id": 8, "step_num": "8", "name": "Report", "icon": "📋", "detail": "Legal Dossier Ready", "status": "pending"}
]

EVIDENCE_SOURCES = [
    {"id": 1, "type": "SAR Satellite", "name": "IMG_2640_1432.tif", "status": "VERIFIED"},
    {"id": 2, "type": "AIS Stream", "name": "ais_20260826.csv", "status": "PARSED"},
    {"id": 3, "type": "Ocean Hydro", "name": "hycom_arabian_sea.nc", "status": "MAPPED"}
]
