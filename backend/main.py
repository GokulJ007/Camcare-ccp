from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from fastapi import Query
from connected import db_connect
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
# def random_status():
#     return random.choice(["online", "offline", "error"])

# def update_random_cams():
#     while True:
#         try:
#             connection = db_connect()
#             cursor = connection.cursor()
#             # Get all camera IDs
#             cursor.execute("SELECT id FROM camerainfo")
#             ids = [row[0] for row in cursor.fetchall()]
#             if ids:
#                 # Pick 1 to N random cameras to update
#                 num_to_update = random.randint(1, max(1, len(ids)//2))
#                 ids_to_update = random.sample(ids, num_to_update)
#                 for cam_id in ids_to_update:
#                     status = random_status()
#                     cursor.execute("UPDATE camerainfo SET cam_status=%s WHERE id=%s", (status, cam_id))
#                 connection.commit()
#         except Exception as e:
#             print("Error updating camera statuses:", e)
#         finally:
#             try:
#                 connection.close()
#             except:
#                 pass
#         time.sleep(120)  # 2 minutes

# # Start the background thread when FastAPI starts
# def start_background_thread():
#     thread = threading.Thread(target=update_random_cams, daemon=True)
#     thread.start()

# @app.on_event("startup")
# def on_startup():
#     start_background_thread()

#API'S
class newcam(BaseModel):
    camera_name:str
    location:str
    zone:str    
    cam_status:str
    uptime:float
@app.post("/newcam")
def newcam(data:newcam):
    try:
        connection=db_connect()
        cursor=connection.cursor()
        Query="INSERT INTO camerainfo (camera_name,location,zone,cam_status,uptime) VALUES (%s,%s,%s,%s,%s)"
        cursor.execute(Query,(
            data.camera_name,
            data.location,
            data.zone,
            data.cam_status,
            data.uptime
        ))
        connection.commit()
        return{"message":"data added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error adding camera data")


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


class CamData(BaseModel):
    camera_name:str
    location:str
    zone:str    
    cam_status:Optional[str]= "online"
    uptime:Optional[float]=100
@app.post("/addcam")
def addcam(data:CamData):
    try:
        connection=db_connect()
        cursor=connection.cursor()
        Query="INSERT INTO camerainfo (camera_name,location,zone,cam_status,uptime) VALUES (%s,%s,%s,%s,%s)"
        cursor.execute(Query,(
            data.camera_name,
            data.location,
            data.zone,
            data.cam_status,
            data.uptime
        ))
        connection.commit()
        return{"message":"data added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error adding camera data")

@app.get("/getcam") #dashboard in index.html
def getcam():
    try:
        connection=db_connect()
        cursor=connection.cursor()
        Query="SELECT * FROM camerainfo"
        cursor.execute(Query)
        result=cursor.fetchall()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching camera data")

