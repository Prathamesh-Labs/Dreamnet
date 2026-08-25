from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# Global in-memory spacecraft telemetry simulator state
telemetry_state = {
    "thruster_temp": 24.5,          # Celsius, nominal < 75.0, warning > 80.0, critical > 100.0
    "solar_current": 8.4,            # Amperes, nominal
    "battery_voltage": 28.2,         # Volts
    "gyro_drift": 0.01,              # deg/hour
    "propellant_pressure": 1.2,      # MPa, nominal < 2.0
    "avionics_temp": 18.2,           # Celsius
    "status": "NOMINAL"              # NOMINAL, WARNING, ANOMALOUS_THERMAL_DRIFT
}

class TelemetryStatusOut(BaseModel):
    thruster_temp: float
    solar_current: float
    battery_voltage: float
    gyro_drift: float
    propellant_pressure: float
    avionics_temp: float
    status: str

@router.get("/status", response_model=TelemetryStatusOut)
def get_telemetry_status():
    return telemetry_state

@router.post("/anomaly", response_model=TelemetryStatusOut)
def trigger_telemetry_anomaly():
    global telemetry_state
    telemetry_state.update({
        "thruster_temp": 112.4,          # Critical overheating
        "propellant_pressure": 2.85,      # High pressure alert
        "gyro_drift": 0.18,              # Attitude control instability
        "status": "ANOMALOUS_THERMAL_DRIFT"
    })
    return telemetry_state

@router.post("/resolve", response_model=TelemetryStatusOut)
def resolve_telemetry_anomaly():
    global telemetry_state
    telemetry_state.update({
        "thruster_temp": 24.8,
        "solar_current": 8.4,
        "battery_voltage": 28.2,
        "gyro_drift": 0.01,
        "propellant_pressure": 1.2,
        "avionics_temp": 18.5,
        "status": "NOMINAL"
    })
    return telemetry_state
