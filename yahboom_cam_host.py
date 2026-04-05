import cv2
import logging
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yahboom-cam-host")

app = FastAPI(title="Yahboom Direct Webcam Streamer")

# Camera settings
CAP_DEVICE = 0
CAP_WIDTH = 640
CAP_HEIGHT = 480
CAP_FPS = 15

class Camera:
    def __init__(self):
        self.cap = None
        self.last_frame = None
        self.active = False
        self.lock = asyncio.Lock()

    def start(self):
        if self.active:
            return
        self.cap = cv2.VideoCapture(CAP_DEVICE)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, CAP_FPS)
        
        if not self.cap.isOpened():
            logger.error(f"Cannot open camera {CAP_DEVICE}")
            return False
            
        self.active = True
        logger.info(f"Camera {CAP_DEVICE} opened at {CAP_WIDTH}x{CAP_HEIGHT}")
        return True

    def stop(self):
        self.active = False
        if self.cap:
            self.cap.release()
            self.cap = None

    async def get_frame(self):
        if not self.active or not self.cap:
            return None
            
        # Running in a thread to keep FastAPI responsive
        loop = asyncio.get_event_loop()
        ret, frame = await loop.run_in_executor(None, self.cap.read)
        if ret:
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return buffer.tobytes()
        return None

camera = Camera()

@app.on_event("startup")
async def startup_event():
    camera.start()

@app.on_event("shutdown")
def shutdown_event():
    camera.stop()

@app.get("/health")
async def health():
    return {"status": "ok", "camera_active": camera.active}

@app.get("/mjpeg")
async def video_feed():
    async def generator():
        while camera.active:
            frame = await camera.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            await asyncio.sleep(1/CAP_FPS)
            
    return StreamingResponse(generator(), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10895)
