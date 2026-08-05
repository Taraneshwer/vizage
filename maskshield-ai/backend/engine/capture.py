import cv2
import threading
import queue
from loguru import logger
from typing import Optional
import time

class VideoCaptureThread:
    """
    Runs video capture in a dedicated thread to prevent blocking the AI inference pipeline.
    """
    def __init__(self, source: int | str = 0, queue_size: int = 5):
        self.source = source
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            logger.error(f"Failed to open video source: {self.source}")
            raise RuntimeError(f"Cannot open video source {self.source}")
            
        self.q = queue.Queue(maxsize=queue_size)
        self.running = False
        self.thread = threading.Thread(target=self._update, daemon=True)

    def start(self) -> 'VideoCaptureThread':
        self.running = True
        self.thread.start()
        logger.info(f"Started video capture thread on source {self.source}")
        return self

    def _update(self) -> None:
        while self.running:
            if not self.q.full():
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("Failed to read frame from video source.")
                    time.sleep(0.1)
                    continue
                self.q.put(frame)
            else:
                time.sleep(0.01)

    def read(self) -> Optional[object]:
        if not self.q.empty():
            return self.q.get()
        return None

    def stop(self) -> None:
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
        self.cap.release()
        logger.info("Stopped video capture thread.")
