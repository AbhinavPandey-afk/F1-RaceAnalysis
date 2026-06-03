from fastapi import APIRouter
from app.telemetry.f1_data import load_session

router = APIRouter()

# ==========================================
# TIRE STRATEGY ENDPOINT
# ==========================================

@router.get("/strategy")
def get_strategy(driver: str = "VER"):

    try:

        session = load_session()

        laps = session.laps.pick_driver(driver)

        if laps.empty:
            return {
                "driver": driver,
                "strategy": []
            }

        strategy_data = []

        # ======================================
        # BUILD STRATEGY DATA
        # ======================================

        for _, lap in laps.iterrows():

            try:

                compound = lap["Compound"]

                if compound is None:
                    continue

                lap_number = int(lap["LapNumber"])

                strategy_data.append({

                    "lap": lap_number,
                    "compound": compound,
                    "tyreLife": int(lap["TyreLife"]) if lap["TyreLife"] == lap["TyreLife"] else 0,
                    "stint": int(lap["Stint"]) if lap["Stint"] == lap["Stint"] else 0,
                    "pitIn": lap["PitInTime"] == lap["PitInTime"],
                    "pitOut": lap["PitOutTime"] == lap["PitOutTime"],

                })

            except Exception as e:
                print("STRATEGY LAP ERROR:", e)

        print("STRATEGY DATA:", len(strategy_data))

        return {

            "driver": driver,
            "strategy": strategy_data

        }

    except Exception as e:

        print("STRATEGY ERROR:", e)

        return {

            "driver": driver,
            "strategy": []

        }
