from app.telemetry.f1_data import get_driver_laps

laps = get_driver_laps("VER")

print(laps.head())