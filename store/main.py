from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List, Dict, Set, Union
import json
import uvicorn

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, String, Float, DateTime
)
from sqlalchemy.orm import sessionmaker

import config

# DB setup
DATABASE_URL = (
    f"postgresql+psycopg2://{config.POSTGRES_USER}:"
    f"{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:"
    f"{config.POSTGRES_PORT}/{config.POSTGRES_DB}"
)
engine = create_engine(DATABASE_URL)
metadata = MetaData()
SessionLocal = sessionmaker(bind=engine)

processed_agent_data = Table(
    "processed_agent_data", metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("user_id", Integer, nullable=False),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)
metadata.create_all(engine)

# Pydantic
class AccelerometerData(BaseModel):
    x: float; y: float; z: float

class GpsData(BaseModel):
    latitude: float; longitude: float

class AgentData(BaseModel):
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime
    user_id: int

    @field_validator('timestamp', mode='before')
    def parse_ts(cls, v):
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)

class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData

class ProcessedAgentDataInDB(BaseModel):
    id: int
    road_state: str
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime
    user_id: int

app = FastAPI()
subscriptions: Dict[int, Set[WebSocket]] = {}

@app.websocket("/ws/{user_id}")
async def websocket_ws(websocket: WebSocket, user_id: int):
    await websocket.accept()
    subs = subscriptions.setdefault(user_id, set())
    subs.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # heartbeat
    except WebSocketDisconnect:
        subs.remove(websocket)

async def send_data_to_subscribers(data: Union[Dict, List[Dict]]):
    batch = data if isinstance(data, list) else [data]
    # приводимо timestamp до ISO, щоб serializable
    for item in batch:
        if isinstance(item.get("timestamp"), datetime):
            item["timestamp"] = item["timestamp"].isoformat()
    user_id = batch[0].get("user_id")
    if not user_id:
        return
    for ws in list(subscriptions.get(user_id, [])):
        await ws.send_json(batch)

@app.post("/processed_agent_data/", response_model=List[ProcessedAgentDataInDB])
async def create_processed_agent_data(data: List[ProcessedAgentData]):
    session = SessionLocal()
    created = []
    for item in data:
        db_data = {
            "road_state": item.road_state,
            "user_id":   item.agent_data.user_id,
            "x": item.agent_data.accelerometer.x,
            "y": item.agent_data.accelerometer.y,
            "z": item.agent_data.accelerometer.z,
            "latitude": item.agent_data.gps.longitude,
            "longitude": item.agent_data.gps.latitude,
            "timestamp": item.agent_data.timestamp,
        }
        result = session.execute(
            processed_agent_data.insert().values(**db_data)
        )
        session.commit()
        inserted_id = result.inserted_primary_key[0]
        # зберігаємо dict із datetime у created
        created.append({"id": inserted_id, **db_data})
    session.close()

    # Відправка WS
    await send_data_to_subscribers(created)

    # Віддаємо відповідь: приводимо timestamp у рядок лише якщо це datetime
    return [
        {
            **c,
            "timestamp": c["timestamp"].isoformat()
            if isinstance(c["timestamp"], datetime)
            else c["timestamp"]
        }
        for c in created
    ]

@app.get(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB
)
def read_processed_agent_data(processed_agent_data_id: int):
    session = SessionLocal()
    row = session.execute(
        processed_agent_data.select()
        .where(processed_agent_data.c.id == processed_agent_data_id)
    ).first()
    session.close()
    if not row:
        raise HTTPException(404, "Data not found")
    return ProcessedAgentDataInDB(**row._mapping)

@app.get(
    "/processed_agent_data/", response_model=List[ProcessedAgentDataInDB]
)
def list_processed_agent_data():
    session = SessionLocal()
    rows = session.execute(
        processed_agent_data.select()
    ).fetchall()
    session.close()
    return [ProcessedAgentDataInDB(**r._mapping) for r in rows]

@app.put(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB
)
def update_processed_agent_data(
    processed_agent_data_id: int,
    data: ProcessedAgentData
):
    session = SessionLocal()
    db_data = {
        "road_state": data.road_state,
        "x": data.agent_data.accelerometer.x,
        "y": data.agent_data.accelerometer.y,
        "z": data.agent_data.accelerometer.z,
        "latitude": data.agent_data.gps.latitude,
        "longitude": data.agent_data.gps.longitude,
        "timestamp": data.agent_data.timestamp,
    }
    result = session.execute(
        processed_agent_data.update()
        .where(processed_agent_data.c.id == processed_agent_data_id)
        .values(**db_data)
        .returning(*processed_agent_data.c)
    )
    session.commit()
    row = result.fetchone()
    session.close()
    if not row:
        raise HTTPException(404, "Data not found")
    return ProcessedAgentDataInDB(**row._mapping)

@app.delete(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB
)
def delete_processed_agent_data(processed_agent_data_id: int):
    session = SessionLocal()
    result = session.execute(
        processed_agent_data.delete()
        .where(processed_agent_data.c.id == processed_agent_data_id)
        .returning(*processed_agent_data.c)
    )
    session.commit()
    row = result.fetchone()
    session.close()
    if not row:
        raise HTTPException(404, "Data not found")
    return ProcessedAgentDataInDB(**row._mapping)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
