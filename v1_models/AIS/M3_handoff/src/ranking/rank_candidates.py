def rank_candidates(candidates, radius_km=20, time_window_minutes=30):

    ranked = []

    for vessel in candidates:

        # 40% distance
        distance_score = max(
            0,
            1 - vessel["distance_km"] / radius_km
        )

        # 30% time
        time_score = max(
            0,
            1 - vessel["time_difference_minutes"] / time_window_minutes
        )

        # 20% trajectory confidence
        trajectory_score = 1.0

        # 10% vessel information availability
        vessel_type_score = (
            1.0
            if vessel.get("vessel_type") is not None
            else 0.5
        )

        final_score = (
            distance_score * 0.40
            + time_score * 0.30
            + trajectory_score * 0.20
            + vessel_type_score * 0.10
        )

        vessel["scores"] = {
            "distance": round(distance_score, 3),
            "time": round(time_score, 3),
            "trajectory": round(trajectory_score, 3),
            "vessel_type": round(vessel_type_score, 3),
        }

        vessel["candidate_score"] = round(final_score * 100, 2)

        ranked.append(vessel)

    return sorted(
        ranked,
        key=lambda x: x["candidate_score"],
        reverse=True
    )
