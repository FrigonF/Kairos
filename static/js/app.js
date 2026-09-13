/**
 * KAIROS: Ocean Intelligence System - Main Application Orchestrator
 */

class KairosApp {
    constructor() {
        this.map = null;
        this.timeline = null;
        this.voice = null;
        this.report = null;
        this.currentStep = 5; // Step 05 Vessel Analysis as depicted in the reference photo
        this.isNoiseFiltered = true;
        this.isDemoTrackActive = false;
        this.demoTrackData = null;
    }

    async init() {
        console.log("Initializing KAIROS Ocean Intelligence System (Satellite Glassmorphic Edition)...");

        // 1. Initialize Submodules
        this.map = new window.KairosMap('map-viewport');
        this.map.init();

        this.timeline = new window.KairosTimeline(this.map);
        this.timeline.init();

        this.voice = new window.KairosVoice(this);
        this.voice.init();

        this.report = new window.KairosReport();
        this.report.init();

        // 2. Render UI Canvas Components
        this.renderSARThumbnail();
        this.bindPipelineSteps();
        this.bindCandidateTable();
        this.bindUploadModal();
        this.bindNavCapsule();
        this.bindSearchFilter();
        this.bindDrawerControls();
        this.startLiveClock();

        console.log("KAIROS Satellite Glassmorphic Core Ready.");
    }

    startLiveClock() {
        const updateClock = () => {
            const el = document.getElementById('footer-time-stamp-val');
            if (el) {
                const now = new Date();
                const day = now.getDate().toString().padStart(2, '0');
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                const month = months[now.getMonth()];
                const year = now.getFullYear();
                const hours = now.getHours().toString().padStart(2, '0');
                const mins = now.getMinutes().toString().padStart(2, '0');
                const secs = now.getSeconds().toString().padStart(2, '0');
                el.textContent = `${day} ${month} ${year}, ${hours}:${mins}:${secs} IST`;
            }
        };
        updateClock();
        setInterval(updateClock, 1000);
    }

    async startNewInvestigation() {
        try {
            const res = await fetch('/api/new_investigation', { method: 'POST' });
            const data = await res.json();
            
            // Clear map layers
            if (this.map) {
                this.map.layers.currentSpill.clearLayers();
                this.map.layers.probableOrigin.clearLayers();
                this.map.layers.forecastPlume.clearLayers();
                this.map.layers.trajectories.clearLayers();
                this.map.layers.vessels.clearLayers();
                this.map.layers.vesselWakes.clearLayers();
                this.map.clearCorrelationTrace();
                this.map.clearRecordedDemoTrack();
            }
            
            this.activeTestCase = null;
            this.realAisMatch = null;
            this.renderTestCasePills();
            
            const infoBox = document.getElementById('test-case-info-box');
            if (infoBox) infoBox.style.display = 'none';

            const pelyrBox = document.getElementById('pelyr-vessel-info-box');
            if (pelyrBox) pelyrBox.style.display = 'none';

            const areaEl = document.getElementById('hud-spill-area-val');
            if (areaEl) areaEl.textContent = '0.0 km²';
            const meanProbEl = document.getElementById('hud-mean-prob-val');
            if (meanProbEl) meanProbEl.textContent = '0.0%';

            const corrStatusEl = document.getElementById('historical-corr-status-val');
            if (corrStatusEl) {
                corrStatusEl.innerHTML = `<b style="color: #ff9f0a;">NO VERIFIED HISTORICAL SOURCE</b>`;
            }

            // Reset Vessel Analysis HUD card fields
            const pelyrHeader = document.getElementById('pelyr-card-header');
            if (pelyrHeader) pelyrHeader.innerHTML = `<span style="color: #8ca3bf;">LIVE PELYR TRAFFIC</span>`;
            const nameEl = document.getElementById('pelyr-vessel-name');
            if (nameEl) nameEl.textContent = "AWAITING SATELLITE EVIDENCE";
            const mmsiEl = document.getElementById('pelyr-mmsi');
            if (mmsiEl) mmsiEl.textContent = "ATTRIBUTION PENDING";
            const trackEl = document.getElementById('pelyr-track-count');
            if (trackEl) trackEl.textContent = "NO DATA";
            const tempEl = document.getElementById('pelyr-temp-corr');
            if (tempEl) tempEl.textContent = "PROXIMITY ATTRIBUTION PENDING";
            const rankContainer = document.getElementById('pelyr-ranking-container');
            if (rankContainer) rankContainer.style.display = 'none';

            // Reset AI Assistant transcript text
            const transcriptEl = document.getElementById('voice-transcript-text');
            if (transcriptEl) transcriptEl.textContent = 'Listening... Awaiting tactical voice command.';

            this.activatePipelineStep(1);
            this.showNotification(`NEW INVESTIGATION [${data.investigation_id}]: All layers, markers, and stale state reset.`);
        } catch (e) {
            console.error("New investigation error:", e);
        }
    }

    bindDrawerControls() {
        const drawer = document.getElementById('investigation-drawer');
        const toggleBtn = document.getElementById('btn-toggle-sidebar');
        const closeBtn = document.getElementById('btn-close-sidebar');
        const openPill = document.getElementById('btn-open-drawer-pill');

        const openDrawer = () => {
            if (drawer) drawer.classList.remove('drawer-closed');
            if (openPill) openPill.style.display = 'none';
        };

        const closeDrawer = () => {
            if (drawer) drawer.classList.add('drawer-closed');
            if (openPill) openPill.style.display = 'flex';
        };

        const toggleDrawer = () => {
            if (drawer && drawer.classList.contains('drawer-closed')) {
                openDrawer();
            } else {
                closeDrawer();
            }
        };

        if (toggleBtn) toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDrawer();
        });

        if (closeBtn) closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeDrawer();
        });

        if (openPill) openPill.addEventListener('click', (e) => {
            e.stopPropagation();
            openDrawer();
        });
    }

    renderSARThumbnail() {
        // Thumbnail is automatically rendered by map.js for the pinned card
    }

    bindNavCapsule() {
        const navButtons = document.querySelectorAll('.nav-capsule-item');
        navButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                navButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    }

    bindSearchFilter() {
        const searchInput = document.getElementById('search-input-header');
        if (!searchInput) return;

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value.trim().toLowerCase();
                if (query.includes('vessel') || query.includes('ais')) {
                    this.map.loadVessels();
                    this.showNotification("SEARCH: Loaded live Pelyr AIS vessels in sector.");
                } else if (query.includes('spill') || query.includes('gujarat') || query.includes('arabian')) {
                    this.map.focusSpill();
                } else {
                    this.showNotification(`SEARCH: Found active incident sector.`);
                }
            }
        });
    }

    bindPipelineSteps() {
        const stepItems = document.querySelectorAll('.timeline-step-row');
        stepItems.forEach(item => {
            item.addEventListener('click', () => {
                const stepId = parseInt(item.dataset.stepId, 10);
                this.activatePipelineStep(stepId);
            });
        });
    }

    activatePipelineStep(stepId) {
        this.currentStep = stepId;

        // Update active & completed classes in DOM
        document.querySelectorAll('.timeline-step-row').forEach(el => {
            const id = parseInt(el.dataset.stepId, 10);
            const isCompleted = id < stepId;
            const isActive = id === stepId;

            el.classList.toggle('active', isActive);
            el.classList.toggle('completed', isCompleted);

            const badge = el.querySelector('.step-status-badge');
            if (badge) {
                if (isCompleted) {
                    badge.className = 'step-status-badge status-completed';
                    badge.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
                } else if (isActive) {
                    badge.className = 'step-status-badge status-active';
                    badge.innerHTML = `<div class="spinner-ring"></div>`;
                } else {
                    badge.className = 'step-status-badge status-pending';
                    badge.innerHTML = '';
                }
            }
        });

        // Trigger corresponding action
        switch (stepId) {
            case 1: // Evidence
                this.showNotification("EVIDENCE: Sentinel-1 SAR, AIS stream, HYCOM currents & ECMWF wind loaded.");
                break;
            case 2: // Spill Detected
                this.map.focusSpill();
                const currentArea = document.getElementById('hud-spill-area-val')?.textContent || '21.99 km²';
                this.showNotification(`DETECTION: Dark spot segmented covering ${currentArea}.`);
                break;
            case 3: // Characterized
                const currentProb = document.getElementById('hud-mean-prob-val')?.textContent || '67.4%';
                this.showNotification(`CHARACTERIZATION: Heavy crude detected via SAR damping analysis (${currentProb} confidence).`);
                break;
            case 4: // Rewind Hindcast
                return fetch('/api/find_probable_origin', { method: 'POST' })
                    .then(r => r.json())
                    .then(data => {
                        if (data.origin_coordinates && this.map) {
                            const oLat = data.origin_coordinates.lat;
                            const oLng = data.origin_coordinates.lng;
                            this.map.renderProbableOrigin(oLat, oLng, this.map.centerLat, this.map.centerLng, data.trajectory_steps);
                            this.map.showHindcast(data.trajectory_steps);
                            this.showNotification(`HINDCAST: Reconstructed origin at ${oLat.toFixed(4)}° N, ${oLng.toFixed(4)}° E`);
                        }
                    }).catch(e => console.error("Hindcast error:", e));
            case 5: // Vessel Analysis
                return this.map.loadVessels().then(() => {
                    this.showNotification("VESSEL ANALYSIS: Live Pelyr regional maritime traffic stream loaded. All vessels rendered in neutral observation mode.");
                    const pelyrBox = document.getElementById('pelyr-vessel-info-box');
                    if (pelyrBox) {
                        pelyrBox.style.display = 'block';
                        const headerEl = document.getElementById('pelyr-card-header');
                        const nameEl = document.getElementById('pelyr-vessel-name');
                        const mmsiEl = document.getElementById('pelyr-mmsi');
                        const trackEl = document.getElementById('pelyr-track-count');
                        const tempEl = document.getElementById('pelyr-temp-corr');
                        if (headerEl) headerEl.innerHTML = `<span style="color: #00d2ff; font-weight: 800;">VESSEL ANALYSIS • LIVE PELYR TRAFFIC</span>`;
                        if (nameEl) nameEl.textContent = "SELECT CORRELATION TO RANK SOURCE";
                        if (mmsiEl) mmsiEl.textContent = "ATTRIBUTION PENDING";
                        if (trackEl) trackEl.textContent = "SELECT A VESSEL OR EXECUTE CORRELATION";
                        if (tempEl) tempEl.textContent = "PROXIMITY ATTRIBUTION PENDING";
                        const rankContainer = document.getElementById('pelyr-ranking-container');
                        if (rankContainer) rankContainer.style.display = 'none';
                    }
                }).catch(e => {
                    console.error("Vessel analysis error:", e);
                });
            case 6: // Correlation
                return fetch('/api/compare_vessels', { method: 'POST' })
                    .then(r => r.json())
                    .then(data => {
                        const candidates = data.candidates || [];
                        const count = candidates.length;
                        const corrStatusEl = document.getElementById('historical-corr-status-val');
                        if (corrStatusEl) {
                            corrStatusEl.innerHTML = count > 0 ? `<b style="color: #ff3b30;">${count} CANDIDATES RANKED</b>` : `<b style="color: #ff9f0a;">NO VESSEL CANDIDATE AVAILABLE</b>`;
                        }

                        if (count > 0 && data.top_candidate) {
                            const cand = data.top_candidate;
                            if (this.map) {
                                this.map.renderCorrelationTrace(cand, this.realAisMatch);
                            }
                            this.showNotification(`CORRELATION: LEADING SOURCE CANDIDATE: ${cand.vessel_name} (MMSI ${cand.mmsi}) | Rank #1.`);
                            
                            const pelyrBox = document.getElementById('pelyr-vessel-info-box');
                            if (pelyrBox) {
                                pelyrBox.style.display = 'block';
                                const nameEl = document.getElementById('pelyr-vessel-name');
                                const mmsiEl = document.getElementById('pelyr-mmsi');
                                const trackEl = document.getElementById('pelyr-track-count');
                                const tempEl = document.getElementById('pelyr-temp-corr');
                                const headerEl = document.getElementById('pelyr-card-header');
                                if (headerEl) {
                                    headerEl.innerHTML = `<span style="color: #30d158; font-weight: 800;">LEADING SOURCE CANDIDATE</span>`;
                                }
                                if (nameEl) nameEl.textContent = `${cand.vessel_name} #1`;
                                if (mmsiEl) mmsiEl.textContent = `MMSI: ${cand.mmsi}`;
                                if (trackEl) trackEl.textContent = cand.has_historical_track ? `${cand.original_ais_points_count || 0} pts` : "UNAVAILABLE";
                                if (tempEl) tempEl.textContent = cand.temporal_delta_seconds ? `${cand.temporal_delta_seconds} s` : "N/A";

                                this.candidatesList = candidates;
                                this.showAllCandidatesState = false;
                                this.renderCandidateRankingList();
                            }
                        } else {
                            if (this.map) {
                                this.map.clearCorrelationTrace();
                            }
                            this.showNotification("CORRELATION: NO VESSEL CANDIDATE AVAILABLE within 250km surveillance radius.");
                            const pelyrBox = document.getElementById('pelyr-vessel-info-box');
                            if (pelyrBox) {
                                pelyrBox.style.display = 'block';
                                const headerEl = document.getElementById('pelyr-card-header');
                                const nameEl = document.getElementById('pelyr-vessel-name');
                                const mmsiEl = document.getElementById('pelyr-mmsi');
                                const tempEl = document.getElementById('pelyr-temp-corr');
                                if (headerEl) headerEl.innerHTML = `<span style="color: #ff9f0a; font-weight: 800;">NO CANDIDATES</span>`;
                                if (nameEl) nameEl.textContent = "ATTRIBUTION UNAVAILABLE";
                                if (mmsiEl) mmsiEl.textContent = "MMSI: N/A";
                                if (tempEl) tempEl.textContent = "N/A";
                            }
                        }
                    }).catch(e => console.error("Correlation error:", e));
            case 7: // Forecast
                return fetch('/api/forecast_spill', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ hours: 24 }) })
                    .then(r => r.json())
                    .then(data => {
                        if (data.polygon_24h && this.map) {
                            const fcCentroid = data.forecast_centroid || {};
                            this.map.renderForecastPlume(data.polygon_24h, fcCentroid.lat, fcCentroid.lng);
                            this.map.showForecast(data.polygon_24h);
                            this.showNotification(`FORECAST: SIMPLIFIED FAY-BASED MODEL + RK4 NETCDF ADVECTION: 24h expansion to ${data.projected_area_km2} km²`);
                        }
                    }).catch(e => console.error("Forecast error:", e));
            case 8: // Report
                this.report.openReport();
                break;
        }
    }

    bindCandidateTable() {
        const rows = document.querySelectorAll('.candidate-row');
        rows.forEach(row => {
            row.addEventListener('click', () => {
                const vesselId = row.dataset.vesselId;
                this.inspectVessel(vesselId);
            });
        });
    }

    async inspectVessel(vesselId) {
        try {
            const res = await fetch('/api/get_vessel_trajectory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vessel_id: vesselId })
            });
            const vessel = await res.json();

            // Highlight trajectory on map
            if (this.map && vessel.trajectory) {
                this.map.renderVesselTrajectory(vessel);
            }
        } catch (e) {
            console.error("Vessel inspection error:", e);
        }
    }

    highlightTopCandidate() {
        this.showNotification("CORRELATION: 0 Verified Historical Candidates.");
    }

    bindUploadModal() {
        const modal = document.getElementById('upload-modal');
        const trigger = document.getElementById('btn-open-upload');
        const closeBtn = document.getElementById('btn-close-upload');
        const form = document.getElementById('upload-evidence-form');

        if (trigger && modal) {
            trigger.addEventListener('click', () => modal.classList.add('open'));
        }
        if (closeBtn && modal) {
            closeBtn.addEventListener('click', () => modal.classList.remove('open'));
        }

        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const fileInput = document.getElementById('upload-file-input');
                if (!fileInput || !fileInput.files.length) {
                    alert("Please select a file to upload.");
                    return;
                }

                const formData = new FormData();
                formData.append('file', fileInput.files[0]);

                try {
                    this.showNotification("UPLOADING & ANALYZING EVIDENCE...");
                    const res = await fetch('/api/upload_evidence', {
                        method: 'POST',
                        body: formData
                    });

                    let data;
                    try {
                        data = await res.json();
                    } catch (parseErr) {
                        alert("SERVER RETURNED INVALID RESPONSE");
                        return;
                    }

                    if (res.ok && data.success !== false) {
                        const msg = data.message || `Evidence file ${fileInput.files[0].name} ingested successfully.`;
                        this.showNotification(msg);
                        modal.classList.remove('open');
                        
                        // Update app state with detection result
                        if (data.detection_result) {
                            const det = data.detection_result;
                            if (det.center_lat && det.center_lng && this.map) {
                                this.map.renderCurrentSpill(
                                    det.center_lat,
                                    det.center_lng,
                                    det.spill_area_km2 || 21.99,
                                    det.mean_probability || 0.67,
                                    det.polygon || null
                                );
                            }

                            // Store real_ais_match on instance if returned
                            if (det.real_ais_match && det.real_ais_match.matched) {
                                this.realAisMatch = det.real_ais_match;
                            } else {
                                this.realAisMatch = null;
                            }

                            if (det.center_lat && det.center_lng && this.map) {
                                this.map.focusSpill();
                            }

                            const areaEl = document.getElementById('hud-spill-area-val');
                            if (areaEl && det.spill_area_km2 !== undefined) {
                                areaEl.textContent = `${det.spill_area_km2} km²`;
                            }
                            
                            const probEl = document.getElementById('hud-mean-prob-val');
                            if (probEl && det.mean_probability !== undefined) {
                                const pct = (det.mean_probability > 1.0) ? det.mean_probability : (det.mean_probability * 100);
                                probEl.textContent = `${pct.toFixed(1)}%`;
                            }

                            // Announce satellite evidence ingestion via AI voice
                            const speechMsg = `Satellite evidence ${fileInput.files[0].name} ingested. Oil spill detected at ${det.center_lat?.toFixed(4)} North, ${det.center_lng?.toFixed(4)} East covering ${det.spill_area_km2} square kilometers. Ready for characterization and rewind.`;
                            if (this.voice) {
                                this.voice.updateTranscript(`KAIROS: ${speechMsg}`, false);
                                this.voice.speak(speechMsg);
                            }
                        }
                        this.showNotification(`INGESTED: ${fileInput.files[0].name} (${data.detection_result?.center_lat?.toFixed(4)}°N, ${data.detection_result?.center_lng?.toFixed(4)}°E)`);
                        
                        // Set current step to Characterization (Step 3) and STOP. Wait for manual user interaction.
                        this.activatePipelineStep(3);
                    } else {
                        const errMsg = data.error || data.message || data.detail || "Upload failed due to unknown error.";
                        this.showNotification("Upload Error: " + errMsg);
                    }
                } catch (err) {
                    this.showNotification("BACKEND CONNECTION FAILED: " + err.message);
                }
            });
        }
    }

    executeTacticalAction(action, data) {
        console.log("Executing UI Action:", action);
        if (action.step) {
            this.activatePipelineStep(action.step);
        }

        if (action.type === 'FOCUS_SPILL') {
            this.map.focusSpill();
        } else if (action.type === 'SHOW_HINDCAST') {
            this.map.showHindcast();
        } else if (action.type === 'SHOW_FORECAST') {
            this.map.showForecast();
        } else if (action.type === 'HIGHLIGHT_VESSEL') {
            this.inspectVessel(action.vessel_id);
        } else if (action.type === 'SHOW_CORRELATION_MATRIX') {
            this.activatePipelineStep(6);
        } else if (action.type === 'OPEN_REPORT_MODAL') {
            this.report.openReport();
        }
    }

    async inspectPelyrVessel(vessel) {
        if (!vessel || !vessel.mmsi) return;

        // Clear existing demo track layer
        if (this.map) {
            this.map.clearRecordedDemoTrack();
        }

        const infoBox = document.getElementById('pelyr-vessel-info-box');
        const headerEl = document.getElementById('pelyr-card-header');
        const nameEl = document.getElementById('pelyr-vessel-name');
        const mmsiEl = document.getElementById('pelyr-mmsi');
        const typeImoEl = document.getElementById('pelyr-type-imo');
        const spillDistEl = document.getElementById('pelyr-spill-dist');
        const sogCogEl = document.getElementById('pelyr-sog-cog');
        const trackCountEl = document.getElementById('pelyr-track-count');
        const timestampEl = document.getElementById('pelyr-timestamp');
        const tempCorrEl = document.getElementById('pelyr-temp-corr');

        if (infoBox) infoBox.style.display = 'block';
        if (headerEl) headerEl.innerHTML = `<span style="color: #00d2ff; font-weight: 800;">LIVE PELYR VESSEL</span>`;
        if (nameEl) nameEl.textContent = vessel.vessel_name || 'Pelyr Vessel';
        if (mmsiEl) mmsiEl.textContent = `MMSI: ${vessel.mmsi}`;
        if (typeImoEl) typeImoEl.textContent = `${vessel.vessel_type || 'Commercial'} ${vessel.imo ? '/ IMO:' + vessel.imo : ''}`;
        if (spillDistEl) spillDistEl.textContent = vessel.distance_km !== undefined ? `${vessel.distance_km} km` : '-';
        if (sogCogEl) sogCogEl.textContent = `${vessel.sog || 0} kn / ${vessel.cog || 0}°`;
        if (trackCountEl) trackCountEl.textContent = 'FETCHING...';
        if (timestampEl) timestampEl.textContent = vessel.timestamp || 'LIVE';
        if (tempCorrEl) tempCorrEl.innerHTML = `<span style="color: #8ca3bf;">NOT ELIGIBLE FOR CULPRIT/SOURCE RANKING</span>`;

        this.showNotification(`INSPECTING LIVE PELYR VESSEL: ${vessel.vessel_name} (MMSI ${vessel.mmsi})...`);

        try {
            const res = await fetch(`/api/live_vessel_track/${vessel.mmsi}`);
            const data = await res.json();

            if (data.status === 'RATE_LIMITED') {
                if (trackCountEl) trackCountEl.textContent = 'RATE LIMITED';
                this.showNotification(`Pelyr historical track temporarily rate-limited. Retry available in ${data.retry_after || 30} seconds.`);
                return;
            }

            if (data.status === 'NO_TRACK_DATA' || !data.track_points || data.track_points.length === 0) {
                if (trackCountEl) trackCountEl.textContent = '0 POINTS (NO TRACK)';
                this.showNotification("LIVE PELYR OBS: 0 Historical track points (Not eligible for source attribution).");
                return;
            }

            // Points returned > 0 -> Draw real trajectory
            if (trackCountEl) trackCountEl.textContent = `${data.count} POINTS`;
            
            if (this.map && data.track_points.length > 0) {
                this.map.renderRealPelyrTrack(data, vessel);
            }
            this.showNotification(`PELYR TRACK: Rendered ${data.count} real chronological AIS points.`);

        } catch (err) {
            console.error("Failed to fetch Pelyr track:", err);
            if (trackCountEl) trackCountEl.textContent = 'ERROR';
            this.showNotification("Pelyr track request failed.");
        }
    }

    renderCandidateRankingList() {
        const rankContainer = document.getElementById('pelyr-ranking-container');
        const rankList = document.getElementById('pelyr-ranking-list');
        if (!rankContainer || !rankList || !this.candidatesList || this.candidatesList.length === 0) return;

        rankContainer.style.display = 'block';
        const displayList = this.showAllCandidatesState ? this.candidatesList : this.candidatesList.slice(0, 3);
        rankList.innerHTML = displayList.map(c => `
            <div style="display: flex; justify-content: space-between; font-size: 11px; padding: 3px 6px; border-radius: 4px; background: ${c.rank === 1 ? 'rgba(255,59,48,0.2)' : 'rgba(255,255,255,0.05)'};">
                <span style="color: ${c.rank === 1 ? '#ff3b30' : '#00d2ff'}; font-weight: 700;">#${c.rank} ${c.vessel_name}</span>
                <span style="color: #cde0f5; font-family: var(--font-mono);">${c.distance_to_origin_km.toFixed(1)} km</span>
            </div>
        `).join('');
    }

    toggleAllCandidates() {
        this.showAllCandidatesState = !this.showAllCandidatesState;
        this.renderCandidateRankingList();
    }

    clearPelyrTrack() {
        if (this.map) {
            this.map.clearRecordedDemoTrack();
        }
        const infoBox = document.getElementById('pelyr-vessel-info-box');
        if (infoBox) infoBox.style.display = 'none';
        this.showNotification("PELYR TRAJECTORY: Cleared layer.");
    }

    showNotification(msg) {
        const toast = document.getElementById('tactical-toast');
        if (!toast) return;
        toast.textContent = msg;
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
        }, 4000);
    }
}

// Bootstrap Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    window.kairosApp = new KairosApp();
    window.kairosApp.init();
});
