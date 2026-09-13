import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.config import RECORDED_TRACKS_MANIFEST, RECORDED_TRACKS_DIR

def load_recorded_tracks_manifest() -> Dict[str, Any]:
    if not RECORDED_TRACKS_MANIFEST.exists():
        return {"test_cases": []}
    with open(RECORDED_TRACKS_MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)

def load_recorded_track_points(mmsi: str) -> Optional[Dict[str, Any]]:
    manifest = load_recorded_tracks_manifest()
    track_info = next((t for t in manifest.get("test_cases", []) if t["vessel_mmsi"] == mmsi), None)
    if not track_info:
        return None
    
    file_path = RECORDED_TRACKS_DIR / f"trajectory_{mmsi}.json"
    if not file_path.exists():
        return None
        
    with open(file_path, "r", encoding="utf-8") as f:
        track_data = json.load(f)
        
    return {
        "metadata": track_info,
        "points": track_data.get("points", [])
    }
