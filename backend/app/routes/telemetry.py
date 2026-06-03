from fastapi import APIRouter
from app.telemetry.f1_data import get_driver_laps
import pandas as pd

router = APIRouter()

# ==========================================
# DRIVER COMPARISON
# ==========================================

@router.get("/compare")
def compare_drivers(
    driver1: str = "VER",
    driver2: str = "HAM"
):

    # ======================================
    # LOAD DRIVER DATA
    # ======================================

    laps1 = get_driver_laps(driver1)
    laps2 = get_driver_laps(driver2)

    # ======================================
    # VALIDATE DATA
    # ======================================

    if laps1 is None or laps2 is None:
        return {
            "driver1": driver1,
            "driver2": driver2,
            "comparison": []
        }

    # ======================================
    # REMOVE NULL LAP TIMES
    # ======================================

    laps1 = laps1.dropna(subset=["LapTime"])
    laps2 = laps2.dropna(subset=["LapTime"])

    # ======================================
    # RESET INDEX
    # ======================================

    laps1 = laps1.reset_index(drop=True)
    laps2 = laps2.reset_index(drop=True)

    # ======================================
    # MATCH SHORTEST STINT
    # ======================================

    max_laps = min(len(laps1), len(laps2))

    comparison = []

    # ======================================
    # BUILD TELEMETRY DATA
    # ======================================

    for i in range(max_laps):

        try:

            lap1 = laps1.iloc[i]
            lap2 = laps2.iloc[i]

            lap1_time = lap1["LapTime"]
            lap2_time = lap2["LapTime"]

            # ==============================
            # SKIP INVALID VALUES
            # ==============================

            if pd.isna(lap1_time) or pd.isna(lap2_time):
                continue

            lap1_seconds = lap1_time.total_seconds()
            lap2_seconds = lap2_time.total_seconds()

            # ==============================
            # REMOVE BAD OUTLIERS ONLY
            # ==============================

            if (
                lap1_seconds <= 0
                or lap2_seconds <= 0
                or lap1_seconds > 150
                or lap2_seconds > 150
            ):
                continue

            # ==============================
            # APPEND CLEAN DATA
            # ==============================

            comparison.append({

                "lap": int(lap1["LapNumber"]),

                driver1: round(lap1_seconds, 2),

                driver2: round(lap2_seconds, 2),
                "delta": round(lap1_seconds - lap2_seconds, 2),
                f"{driver1}_compound": str(lap1.get("Compound", "")),
                f"{driver2}_compound": str(lap2.get("Compound", "")),
                f"{driver1}_tyreLife": int(lap1.get("TyreLife", 0)) if lap1.get("TyreLife", 0) == lap1.get("TyreLife", 0) else 0,
                f"{driver2}_tyreLife": int(lap2.get("TyreLife", 0)) if lap2.get("TyreLife", 0) == lap2.get("TyreLife", 0) else 0,

            })

        except Exception as e:

            print("LAP ERROR:", e)
            continue

    # ======================================
    # DEBUGGING
    # ======================================

    print("TOTAL LAPS:", len(comparison))

    # ======================================
    # RETURN RESPONSE
    # ======================================

    return {

        "driver1": driver1,
        "driver2": driver2,
        "comparison": comparison

    }
