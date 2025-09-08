from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from fastapi import Query
try:
    # When imported as a package (python -m backend.main or uvicorn backend.main:app)
    from backend.connected import db_connect
except Exception:
    # When run as a script from the backend/ folder (python db_migrations.py)
    from connected import db_connect
from datetime import datetime
import random
import threading
import time
app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 👈 Allow all origins (good for local dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Background thread to update random camera statuses
def random_status():
    return random.choice(["online", "offline", "error"])



def update_random_cams():
    while True:
        try:
            connection = db_connect()
            cursor = connection.cursor()
            # Get all camera IDs
            cursor.execute("SELECT id FROM camerainfo")
            ids = [row['id'] for row in cursor.fetchall()]
            if ids:
                # Pick 1 to N random cameras to update
                num_to_update = random.randint(1, max(1, len(ids)//2))
                ids_to_update = random.sample(ids, num_to_update)
                for cam_id in ids_to_update:
                    status = random_status()
                    cursor.execute("UPDATE camerainfo SET cam_status=%s WHERE id=%s", (status, cam_id))

                cursor.execute("select id,cam_status from camerainfo")
                updated_statuses = cursor.fetchall()
                now=datetime.now()
                for cams in updated_statuses:
                    new_status=cams['cam_status']
                    cam_id=cams['id']
                    if new_status in ["offline","error"]:
                        cursor.execute("insert into camhistory(cam_id,camstatus,start_time) values(%s,%s,%s)",(cam_id,new_status,now))
                    elif new_status=="online":
                        cursor.execute("""
                        select id,start_time from camhistory 
                        where cam_id=%s and end_time is null 
                        order by start_time desc limit 1
                        """,(cam_id,)
                        )
                        last_event=cursor.fetchone()
                        if last_event:
                            event_id=last_event['id']
                            start_time=last_event['start_time']
                            duration = int((now - start_time).total_seconds())  # Duration in seconds
                            cursor.execute("update camhistory set end_time=%s,duration_seconds=%s where id=%s",(now,duration,event_id))
                connection.commit()
        except Exception as e:
            import traceback
            print("Error updating camera statuses:", e)
            traceback.print_exc()
        finally:
            try:
                connection.close()
            except:
                pass
        time.sleep(60)  # 2 minutes

# Start the background thread when FastAPI starts
def start_background_thread():
    thread = threading.Thread(target=update_random_cams, daemon=True)
    thread.start()

@app.on_event("startup")
def on_startup():
    start_background_thread()

#API'S
class NewCamModel(BaseModel):
    camera_name: str
    location: str
    zone: str
    cam_status: str
    uptime: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@app.post("/newcam")
def create_newcam(data: NewCamModel):
    try:
        connection = db_connect()
        cursor = connection.cursor()
        Query = "INSERT INTO camerainfo (camera_name,location,zone,cam_status,uptime,latitude,longitude) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(Query, (
            data.camera_name,
            data.location,
            data.zone,
            data.cam_status,
            data.uptime,
            data.latitude,
            data.longitude,
        ))
        connection.commit()
        return {"message": "data added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding camera data: {e}")


@app.get("/livefeed/{id}")
def livefeed(id:int):
    try:
        connection=db_connect()
        cursor=connection.cursor()
        cursor.execute("select * from camerainfo where id=%s",(id,))
        result=cursor.fetchone()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching camera data")

@app.get("/livefeed_no_id")
def livefeed_no_id():
    try:
        connection=db_connect()
        cursor=connection.cursor()
        cursor.execute("select * from camerainfo where id=100")
        result=cursor.fetchone()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching camera data")

available_coords = [
    (39.83, -98.55),
    (39.75, -98.45),
    (39.95, -98.65),
    (39.80, -98.40),
]

def getcords():
    if not available_coords:
        # Fallback: return a sensible default coordinate instead of failing
        print("Warning: available_coords empty, returning default coordinate")
        return (39.8283, -98.5795)
    idx = random.randint(0, len(available_coords) - 1)
    cords = available_coords.pop(idx)
    return cords
class CamData(BaseModel):
    camera_name: str
    location: str
    zone: str
    cam_status: Optional[str] = "online"
    uptime: Optional[float] = 100
    latitude: Optional[float] = None
    longitude: Optional[float] = None
@app.post("/addcam")
def addcam(data:CamData):
    try:
        lat = data.latitude
        lon = data.longitude
        if lat is None or lon is None:
            lat, lon = getcords()
        connection = db_connect()
        cursor = connection.cursor()
        Query = "INSERT INTO camerainfo (camera_name,location,zone,cam_status,uptime,latitude,longitude) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(Query, (
            data.camera_name,
            data.location,
            data.zone,
            data.cam_status,
            data.uptime,
            lat,
            lon,
        ))
        connection.commit()
        return {"message": "data added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding camera data: {e}")

@app.get("/getcam") #dashboard in index.html
def getcam():
    try:
        connection=db_connect()
        cursor=connection.cursor()
        Query="SELECT id, camera_name, location, zone, cam_status, uptime, latitude, longitude FROM camerainfo"
        cursor.execute(Query)
        result=cursor.fetchall()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching camera data")

@app.get("/gethistory")
def gethistory():
    try:
        connection=db_connect()
        cursor=connection.cursor()
        cursor.execute("""
        SELECT camhistory.*, camerainfo.location
        FROM camhistory
        JOIN camerainfo ON camhistory.cam_id = camerainfo.id
        ORDER BY camhistory.start_time DESC
        """)
        result=cursor.fetchall()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching camera history data")

from fastapi.responses import FileResponse
import os


@app.get("/map")
def serve_map():
    # Serve the local mapview.html file
    here = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(here, 'mapview.html')
    if os.path.exists(path):
        return FileResponse(path, media_type='text/html')
    raise HTTPException(status_code=404, detail='mapview.html not found')