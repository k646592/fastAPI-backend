from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
import json
import asyncio

import api.cruds.seat as seat_crud
import api.schemas.seat as seat_schema

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

connection_manager = ConnectionManager()

@router.websocket("/ws_seats")
async def websocket_seat_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await connection_manager.broadcast(message)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except asyncio.TimeoutError:
        connection_manager.disconnect(websocket)
        print("WebSocket connection timed out.")
    except Exception as e:
        connection_manager.disconnect(websocket)
        print(f"WebSocket Error: {e}")


@router.post("/seats", response_model=list[seat_schema.SeatResponse])
async def update_or_create_seats(
    seats: list[seat_schema.SeatUpdate], 
    db: AsyncSession = Depends(get_db)
):
    try:
        all_seats = await seat_crud.bulk_update_or_create_seats_and_get_all(db, seats)
        return all_seats
    except Exception as e:
        import logging
        logging.error(f"Error processing seats: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/seats", response_model=list[seat_schema.Seat])
async def get_seats(
    db: AsyncSession = Depends(get_db)
):
    return await seat_crud.get_seats(db)
