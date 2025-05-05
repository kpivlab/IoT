from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float

class GpsData(BaseModel):
    latitude: float
    longitude: float

class AgentData(BaseModel):
    accelerometer: AccelerometerData
    gps:  Optional[GpsData] = None
    timestamp: datetime
    user_id:     int
