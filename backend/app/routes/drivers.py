from fastapi import APIRouter
from app.telemetry.f1_data import load_session

router = APIRouter()

# ==========================================
# GET AVAILABLE DRIVERS
# ==========================================

@router.get("/drivers")
def get_drivers():

    try:

        session = load_session()

        drivers = []

        # ======================================
        # EXTRACT DRIVER CODES
        # ======================================

        for driver_number in session.drivers:

            try:

                info = session.get_driver(driver_number)

                code = info["Abbreviation"]

                if code not in drivers:
                    drivers.append(code)

            except:
                continue

        drivers.sort()

        return {
            "drivers": drivers
        }

    except Exception as e:

        print("DRIVER API ERROR:", e)

        return {
            "drivers": []
        }