import os
import threading
import time
from pathlib import Path
from uuid import uuid4
import tkinter as tk
from tkinter import ttk, messagebox

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay"
)

import cv2
from PIL import Image, ImageTk


class CameraStream:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.frame = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.running = self.cap.isOpened()

        self.fps = 0
        self._frames = 0
        self._fps_time = time.time()

        if self.running:
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

    @property
    def opened(self):
        return self.running

    def _loop(self):
        while not self.stop_event.is_set():
            ok, frame = self.cap.read()

            if not ok:
                time.sleep(0.01)
                continue

            with self.lock:
                self.frame = frame

            self._frames += 1
            now = time.time()

            if now - self._fps_time >= 1:
                self.fps = self._frames / (now - self._fps_time)
                self._frames = 0
                self._fps_time = now

        self.cap.release()

    def read(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        if not self.running:
            return

        self.running = False
        self.stop_event.set()

        if hasattr(self, "thread"):
            self.thread.join(timeout=1)

        self.cap.release()


class Processor:
    def __init__(self):
        self.model = None

    def process(self, frame):
        return frame


class DatasetSaver:
    def __init__(self, folder="dataset"):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def save(self, frame):
        path = self.folder / f"{uuid4().hex}.jpg"

        if not cv2.imwrite(str(path), frame):
            raise IOError("Не удалось сохранить изображение")

        return path


class App:
    def __init__(self, root):
        self.root = root
        self.stream = None
        self.processor = Processor()
        self.saver = DatasetSaver()

        self.display_frames = 0
        self.display_fps = 0
        self.fps_time = time.time()

        root.title("Камера")
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._build_ui()

    def _build_ui(self):
        login = ttk.Frame(self.root)
        login.pack(padx=8, pady=8)

        self.ip = tk.StringVar(value="192.168.1.108")
        self.user = tk.StringVar(value="admin")
        self.password = tk.StringVar()
        self.quality = tk.StringVar(value="Доп. (лёгкий)")

        fields = [("IP", self.ip), ("Логин", self.user), ("Пароль", self.password)]

        for i, (text, var) in enumerate(fields):
            ttk.Label(login, text=text).grid(row=0, column=i * 2, padx=2)
            ttk.Entry(
                login, textvariable=var, width=14,
                show="*" if text == "Пароль" else ""
            ).grid(row=0, column=i * 2 + 1, padx=2)

        ttk.Combobox(
            login, textvariable=self.quality, width=14, state="readonly",
            values=["Основной", "Доп. (лёгкий)"]
        ).grid(row=0, column=6, padx=4)

        ttk.Button(login, text="Подключить", command=self.connect).grid(
            row=0, column=7, padx=2
        )

        self.video = tk.Label(self.root, bg="black")
        self.video.pack(padx=8)

        self.info = tk.StringVar(value="Отключено | FPS: 0")
        ttk.Label(self.root, textvariable=self.info).pack()

        ttk.Button(
            self.root,
            text="Снимок в dataset",
            command=self.snapshot
        ).pack(pady=8)

    def connect(self):
        if self.stream:
            self.stream.stop()

        subtype = 0 if self.quality.get() == "Основной" else 1

        url = (
            f"rtsp://{self.user.get()}:{self.password.get()}"
            f"@{self.ip.get()}:554"
            f"/cam/realmonitor?channel=1&subtype={subtype}"
        )

        stream = CameraStream(url)

        if not stream.opened:
            messagebox.showerror("Ошибка", "Не удалось подключиться")
            self.info.set("Отключено | FPS: 0")
            return

        self.stream = stream
        self.display_frames = 0
        self.display_fps = 0
        self.fps_time = time.time()
        self.info.set("Подключено | FPS: 0")
        self.update()

    def update(self):
        if self.stream is None:
            return

        frame = self.stream.read()

        if frame is not None:
            frame = self.processor.process(frame)
            frame = self.resize(frame, 720)

            img = ImageTk.PhotoImage(
                Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            )

            self.video.config(image=img)
            self.video.image = img

            self.display_frames += 1
            now = time.time()

            if now - self.fps_time >= 1:
                self.display_fps = self.display_frames / (now - self.fps_time)
                self.display_frames = 0
                self.fps_time = now

            self.info.set(
                f"Подключено | Camera: {self.stream.fps:.1f} FPS | "
                f"Display: {self.display_fps:.1f} FPS"
            )

        self.root.after(30, self.update)

    @staticmethod
    def resize(frame, width):
        h, w = frame.shape[:2]
        height = int(h * width / w)
        return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

    def snapshot(self):
        if not self.stream:
            messagebox.showwarning("Ошибка", "Сначала подключитесь к камере")
            return

        frame = self.stream.read()

        if frame is None:
            messagebox.showwarning("Ошибка", "Кадр ещё не получен")
            return

        try:
            path = self.saver.save(frame)
            self.info.set(f"Сохранено: {path.name}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def close(self):
        if self.stream:
            self.stream.stop()

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()