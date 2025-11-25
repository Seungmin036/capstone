import cv2
import numpy as np

cap = cv2.VideoCapture(0)

# 중앙 ROI 좌표 (지금 코드와 동일)
x1, y1, x2, y2 = 280, 180, 360, 260

while True:
    ret, frame = cap.read()
    if not ret:
        print("캡쳐 실패")
        break

    # ROI 표시
    disp = frame.copy()
    cv2.rectangle(disp, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # HSV 변환
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    roi = hsv[y1:y2, x1:x2]

    H = roi[:, :, 0].flatten()
    S = roi[:, :, 1].flatten()
    V = roi[:, :, 2].flatten()

    # 너무 검은/흰 픽셀은 제외 (노이즈 줄이기용)
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
