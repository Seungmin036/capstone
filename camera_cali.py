import cv2
import numpy as np

cap = cv2.VideoCapture(0)

# set ROI coordinates
x1, y1, x2, y2 = 280, 180, 360, 260

while True:
    ret, frame = cap.read()
    if not ret:
        print("Capture failed")
        break
    
    disp = frame.copy()
    cv2.rectangle(disp, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # HSV transformation
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    roi = hsv[y1:y2, x1:x2]

    H = roi[:, :, 0].flatten()
    S = roi[:, :, 1].flatten()
    V = roi[:, :, 2].flatten()

    mask = (V > 30) & (S > 50)
    H_valid = H[mask]

    if len(H_valid) > 0:
        print(f"H_min={H_valid.min()}, H_max={H_valid.max()}, "
              f"S_mean={S[mask].mean():.1f}, V_mean={V[mask].mean():.1f}")

    cv2.imshow("calib", disp)

    key = cv2.waitKey(10) & 0xFF
    if key == ord('q') or key == 27:
        break

cap.release()
cv2.destroyAllWindows()
