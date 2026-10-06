import cv2

rtsp_url = "rtsp://admin:admin123@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0"

cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
if not cap.isOpened():
    raise SystemExit("Не удалось открыть RTSP-поток")

while True:
    ok, frame = cap.read()
    if not ok:
        print("Кадр не получен")
        break
    cv2.imshow("Dahua RTSP", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()