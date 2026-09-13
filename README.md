# KAIROS V2 — Autonomous Ocean Intelligence & Maritime Forensic Platform

**KAIROS V2** is an AI-powered maritime domain awareness and oil spill investigation system. It integrates multi-modal satellite SAR/optical imagery, hydrodynamic ocean current models (COPERNICUS / HYCOM), and Automatic Identification System (AIS) telemetry to perform rapid detection, 4D advection reconstruction, vessel candidate ranking, and forensic dossier generation.

---

## Technical Architecture

```
                               ┌───────────────────────────┐
                               │     Frontend HUD (UI)     │
                               │ Leaflet JS / Voice / REST │
                               └─────────────┬─────────────┘
                                             │ HTTP / REST
                               ┌─────────────▼─────────────┐
                               │  FastAPI Backend (v2.0)   │
                               └─────────────┬─────────────┘
         ┌───────────────────┬───────────────┼───────────────┬───────────────────┐
         │                   │               │               │                   │
┌────────▼────────┐ ┌────────▼────────┐ ┌────▼────┐ ┌────────▼────────┐ ┌────────▼────────┐
│ Module M1       │ │ Module M2       │ │ Character-│ │ Module M4       │ │ Module M3       │
│ Data Ingestion  │ │ PyTorch U-Net   │ │ ization   │ │ RK4 Drift       │ │ AIS Telemetry   │
│ GeoTIFF / CRS   │ │ Segmentation    │ │ Geometry  │ │ Hindcast/Forecast│ │ Pelyr Live API  │
└─────────────────┘ └─────────────────┘ └───────────┘ └─────────────────┘ └─────────────────┘
```

### Module Breakdown:
1. **Module M1 (Data & Ingestion)**: Ingests Sentinel-1 C-band Synthetic Aperture Radar (SAR) imagery, extracts CRS/WGS84 geotransform metadata, and manages state isolation per investigation.
2. **Module M2 (Spill Detection)**: Executes binary segmentation using a PyTorch U-Net deep learning checkpoint (`best_model.pth`).
3. **Characterization Engine**: Computes morphological invariants (slick surface area, perimeter, compactness, eccentricity, fractal dimension) and estimates slick age/weathering using Mackay evaporative exposure models.
4. **Module M4 (Ocean Current Advection Engine)**: Performs 4th-Order Runge-Kutta (RK4) Lagrangian backward advection (hindcast) and forward advection (forecast) using sampled NetCDF vector fields (`TEST_OCEAN_001.nc`).
5. **Module M3 (AIS Vessel Telemetry & Correlation)**: Interfaces with live Pelyr HTTPS AIS services to query regional vessel traffic and ranks candidate vessels based on spatio-temporal proximity to the reconstructed discharge origin.
6. **Forensic Report Generator**: Compiles an official legal dossier summarizing detection geometry, hydrodynamic advection vectors, vessel candidate rankings, and statutory MARPOL Annex I references.

---

## Datasets & Models

* **M2 Segmentation Model Checkpoint**: PyTorch U-Net architecture (`backend/models/checkpoints/best_model.pth`, size: 160.8 MB). Managed via Git LFS.
* **Hydrodynamic Data**: NetCDF ocean velocity dataset (`TEST_EVIDENCE/weather/TEST_OCEAN_001.nc`).
* **AIS Telemetry**: Integrated with Pelyr HTTPS API for live regional vessel tracking and historical Sentinel-1 + AIS validation scenes (`TEST_EVIDENCE/satellite/real_ais_scenes`).

---

## Installation & Setup

### Prerequisites
* Python 3.9+
* Git & Git LFS (`git lfs install`)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-org/KAIROS_V2_GITHUB_DEPLOY.git
cd KAIROS_V2_GITHUB_DEPLOY

# Pull LFS model checkpoint
git lfs pull

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Optionally configure your Pelyr API credentials:
```env
PELYR_API_KEY=your_pelyr_key_here
```

### 3. Launch Application Server
```bash
python run.py
```
Open your browser and navigate to `http://localhost:8000`.

---

## API Summary

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Tactical HUD dashboard |
| `/api/health` | `GET` | System health diagnostic |
| `/api/new_investigation` | `POST` | Clears active state and initializes a new investigation |
| `/api/upload_evidence` | `POST` | Ingests SAR GeoTIFF, parses CRS, and runs M2 U-Net inference |
| `/api/analyze_spill` | `POST` | Returns geometric characterization & weathering metrics |
| `/api/find_probable_origin`| `POST` | Executes 6-hour M4 RK4 backward advection hindcast |
| `/api/forecast_spill` | `POST` | Executes 24-hour forward Fay-spreading advection forecast |
| `/api/compare_vessels` | `POST` | Ranks candidate vessels by proximity to M4 probable origin |
| `/api/find_nearby_vessels` | `POST` | Queries Pelyr API for live regional AIS traffic |
| `/api/generate_report` | `POST` | Assembles legal MARPOL Annex I evidence report |

---

## Scientific & Technical Limitations

* **Validation Dice Score Warning**: The included M2 PyTorch U-Net model checkpoint has a validation Dice score of **7.94%**. It exhibits high false-positive rates on low-backscatter oceanic features (wind-shadow dark spots, natural oil seeps, low-wind sea surface anomalies). Detection outputs MUST be validated with ocean drift vectors and AIS traffic analysis.
* **Probabilistic Attribution**: Vessel rankings represent **evidence-based vessel candidate rankings** derived from spatial proximity to the probable spill origin. KAIROS V2 does not claim legally proven vessel responsibility or 100% attribution certainty without physical chemical fingerprinting samples.
* **Hydrodynamic Resolution**: M4 RK4 advection calculations rely on interpolated surface current vectors. Sub-grid turbulence, local coastal bathymetry, and micro-scale wave action introduce spatial uncertainty margins.
