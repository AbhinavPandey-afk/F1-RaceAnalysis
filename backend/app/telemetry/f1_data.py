from functools import lru_cache

import fastf1
import pandas as pd

# ==========================================
# ENABLE CACHE
# ==========================================

fastf1.Cache.enable_cache("cache")

# ==========================================
# LOAD SESSION
# ==========================================

@lru_cache(maxsize=1)
def load_session():

    session = fastf1.get_session(
        2024,
        "Monaco Grand Prix",
        "R"
    )

    session.load()

    return session

# ==========================================
# GET DRIVER LAPS
# ==========================================

def get_driver_laps(driver_code: str):

    try:

        session = load_session()

        laps = session.laps.pick_driver(driver_code)

        # ==================================
        # CHECK EMPTY
        # ==================================

        if laps.empty:

            print(f"NO DATA FOUND FOR {driver_code}")

            return pd.DataFrame()

        # ==================================
        # RETURN CLEAN LAPS
        # ==================================

        columns = [
            "LapNumber",
            "LapTime",
            "Sector1Time",
            "Sector2Time",
            "Sector3Time",
            "SpeedI1",
            "SpeedI2",
            "SpeedFL",
            "SpeedST",
            "Compound",
            "TyreLife",
            "Stint",
            "PitInTime",
            "PitOutTime",
            "Position",
            "TrackStatus",
        ]

        laps = laps[[column for column in columns if column in laps.columns]]

        laps = laps.dropna(subset=["LapTime"])

        print(f"{driver_code} LAPS:", len(laps))

        return laps

    except Exception as e:

        print("F1 DATA ERROR:", e)

        return pd.DataFrame()
