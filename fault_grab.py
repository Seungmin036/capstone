# !/usr/bin/env python
# coding: utf-8
import cv2
import numpy as np
import random
import time
from Arm_Lib import Arm_Device
import threading

class fault_grab():
    def __init__(self, capture_source):
        
        self.Arm = Arm_Device()
        self.color_name = None
        self.image = None

        self.look_at = [90, 164, 18, 0, 90, 90]
        self.p_top = [90, 80, 50, 50, 270]

        self.p_Yellow = [70, 73, 11, 33, 270]
        self.p_Red = [112, 73, 11, 33, 270]
        self.p_Green = [152, 73, 11, 33, 270]
        self.p_Blue = [32, 73, 11, 33, 270]
        self.p_gray = [90, 52, 35, 30, 270]
        
        self.p_Yellow_check = [72, 58, 40, 0, 90] 
        self.p_Red_check = [112, 58, 40, 0, 90]
        self.p_Green_check = [152, 58, 40, 0, 90]
        self.p_Blue_check = [32, 58, 40, 0, 90]

        self.g_state_arm = 0
        self.started = 0
        self.grab_start = 0
        
        self.target_area = (80, 30, 560, 450) 
        self.debug_img = None
        
        # [수정] 외부에서 초기화된 단일 카메라 객체를 저장1
        self.cap = capture_source
        if not self.cap.isOpened():
            print(" camera initializaiton failed in main script.")
            
    def arm_move(self, p, s_time = 500):
        for i in range(5):
            id = i + 1
            if id == 5:
                time.sleep(.1)
                self.Arm.Arm_serial_servo_write(id, p[i], int(s_time*1.2))
            elif id == 1 :
                self.Arm.Arm_serial_servo_write(id, p[i], int(3*s_time/4))
            else:
                self.Arm.Arm_serial_servo_write(id, p[i], int(s_time))
            time.sleep(.01)
        time.sleep(s_time/1000)
    
    def arm_clamp_block(self, enable):
        if enable == 0:
            self.Arm.Arm_serial_servo_write(6, 60, 400)
        else:
            self.Arm.Arm_serial_servo_write(6, 135, 400)
        time.sleep(.5)
        
    def arm_clamp_move(self, angle):
        self.Arm.Arm_serial_servo_write(5, angle, 400)
        time.sleep(.5)

    def ctrl_arm_move(self, index):
        self.arm_clamp_block(0)
        if index == 1:
            print("yellow")
            self.Arm.Arm_Buzzer_On(1)
            time.sleep(1)
            self.number_action(index)
        elif index == 2:
            print("RED")
            self.Arm.Arm_Buzzer_On(1)
            time.sleep(1)
            self.number_action(index)
        elif index == 3:
            print("Green")
            self.Arm.Arm_Buzzer_On(1)
            time.sleep(1)
            self.number_action(index)
        elif index == 4:
            print("Blue")
            self.Arm.Arm_Buzzer_On(1)
            time.sleep(1)
            self.number_action(index)
        self.g_state_arm = 0

    
    def number_action(self, index): 

        if index == 1:       # Yellow
            check_pose = self.p_Yellow_check
            pick_pose  = self.p_Yellow
        elif index == 2:     # Red
            check_pose = self.p_Red_check
            pick_pose  = self.p_Red
        elif index == 3:     # Green
            check_pose = self.p_Green_check
            pick_pose  = self.p_Green
        elif index == 4:     # Blue
            check_pose = self.p_Blue_check
            pick_pose  = self.p_Blue
        else:
            print(f"[number_action] 잘못된 index: {index}")
            return

        self.arm_move(check_pose, 1000)

        time.sleep(5)

        # 3) 카메라 이미지 업데이트
        if not self.update_image(): 
            print("image update failed, return to top.")
            self.arm_move(self.p_top, 1000)
            self.Arm.Arm_serial_servo_write6_array(self.p_Yellow, 1000)
        
            return

        # 4) 색 / 위치 검사 수행
        color_ok = self.check_color_cv(index=index)
        pos_ok, obj_angle  = self.check_position_cv(tolerance=80)

        # 5) 두 조건이 모두 만족해야만 집기 수행
        if color_ok and pos_ok:
            if obj_angle < 20 or obj_angle > 70:
                print("조건 만족")
                self.grab_start = 1
                self.arm_move(self.p_top, 1000)
                self.arm_move(pick_pose, 1000)
                time.sleep(5)
                self.arm_clamp_block(1)
                self.arm_move(self.p_top, 1000)
                self.put_down_block()
                    
            else :
                print("각도 오류 ... 수정 중 ... ")
                self.grab_start = 1
                self.arm_move(self.p_top, 1000)
                self.arm_move(pick_pose, 1000)
                if obj_angle < 45:
                    obj_angle = 270 + obj_angle
                else :    
                    obj_angle = 270 - (90 - obj_angle)
                self.arm_clamp_move(obj_angle)
                time.sleep(5)
                self.arm_clamp_block(1)
                self.arm_move(self.p_top, 1000)
                self.put_down_block()
            
        else:
            print("조건불만족")
            if not color_ok: 
                print("color error")
            if not pos_ok: 
                print("position error")
            self.grab_start = 0
            self.arm_move(self.look_at, 1000)
    
    def put_down_block(self):
        self.arm_move(self.p_gray, 1000)
        self.arm_clamp_block(0) 
        self.Arm.Arm_serial_servo_write6_array(self.look_at, 1000)
        time.sleep(1)

    def start_move_arm(self, index):
        # 开启机械臂控制线程
        if self.g_state_arm == 0:
            closeTid = threading.Thread(target = self.ctrl_arm_move, args = [index])
            closeTid.setDaemon(True)
            closeTid.start()
            
            self.g_state_arm = 1
 

    def get_color(self, img):
        H = []
        S = []
        color_name = {}
        img = cv2.resize(img, (640, 480))
        HSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        x1, y1, x2, y2 = 280, 180, 360, 260
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
        # 2) ROI 내 H, S 값 수집
        for i in range(x1, x2):
            for j in range(y1, y2):
                H.append(HSV[j, i][0])
                S.append(HSV[j, i][1])
    
        H_min = min(H)
        H_max = max(H)
        S_mean = float(np.mean(S))  # S 평균값
    
        # 디버깅용으로 보고 싶으면 주석 해제
        # print(f"H_min={H_min}, H_max={H_max}, S_mean={S_mean:.1f}")
        if H_min == 0 and H_max == 179 and (140 <= S_mean <= 180):
            color_name['name'] = 'red'
        elif H_min >= 16 and H_max <= 34:
            color_name['name'] = 'yellow'
        elif (H_min >= 60 and H_max <= 95) and (60 <= S_mean <= 139):
            color_name['name'] = 'green'
        elif H_min >= 100 and H_max <= 124:
            color_name['name'] = 'blue'
    
        return img, color_name


    def reset_state(self):
        self.started = 0

    def check_color_cv(self, index) -> bool:
        if self.image is None: return (0, 0, 0, 0)
        img = cv2.resize(self.image, (640, 480), )
        HSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        H = []
        for i in range(280, 360):
            for j in range(180, 260): H.append(HSV[j, i][0])
            
        H_min = min(H); H_max = max(H)
        if index == 1:  
            if H_min >= 16 and H_max <= 34:
                print("Color check passed for Yellow.")
                return True
            else:
                print("Color check failed for Yellow.")
                return False
        elif index == 2:
            if H_min == 0 and H_max == 179 or H_min >= 156 and H_max <= 180:
                print("Color check passed for Red.")
                return True
            else:
                print("Color check failed for Red.")
                return False
        elif index == 3:
            if H_min >= 60 and H_max <= 95:
                print("Color check passed for Green.")
                return True
            else:
                print("Color check failed for Green.")
                return False
        elif index == 4:
            if H_min >= 100 and H_max <= 124:
                print('Color Correction Checked')
                print("Color check passed for Blue.")
                print('')
                return True
            else:
                print('Color Correction Checked')
                print("Color check failed for Blue.")
                print('')
                return False
        

    def Color_Recongnize(self, frame):
        if self.started == 0:
            self.Arm.Arm_serial_servo_write6_array(self.look_at, 1000)
            time.sleep(1)
            # 고개 끄덕이기
            self.Arm.Arm_Buzzer_On(1)
            s_time = 300
            self.Arm.Arm_serial_servo_write(4, 10, s_time)
            time.sleep(s_time/1000)
            self.Arm.Arm_serial_servo_write(4, 0, s_time)
            time.sleep(s_time/1000)
            self.Arm.Arm_serial_servo_write(4, 10, s_time)
            time.sleep(s_time/1000)
            self.Arm.Arm_serial_servo_write(4, 0, s_time)
            time.sleep(s_time/1000)
            self.started = 1
        
        
        frame, color_name = self.get_color(frame)
        
        if len(color_name)==1:
            if color_name['name'] == 'yellow':
                self.start_move_arm(1)
            elif color_name['name'] == 'red':
                self.start_move_arm(2)
            elif  color_name['name'] == 'green':
                self.start_move_arm(3)
            elif color_name['name'] == 'blue':
                self.start_move_arm(4)
                
        return frame
            
            
    def get_object_bounding_box(self):
        
        if self.image is None: return (0, 0, 0, 0)
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 40, 170) 
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours: return (0, 0, 0, 0)
        max_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(max_contour)
        return (x, y, x + w, y + h)
    
    def get_object_rotated_info(self):
        
        if self.image is None: return (0, 0, 0, 0, 0)
        
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 40, 170) 
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours: return (0, 0, 0, 0, 0)
        
        max_contour = max(contours, key=cv2.contourArea)
        
        rect = cv2.minAreaRect(max_contour)
        (cx, cy), (w, h), angle = rect
        
        return (int(cx), int(cy), w, h, angle)
    # def check_position_cv(self, tolerance: int = 25) -> bool:
        if self.image is None:
            print(" self.image가 없어 위치를 계산할 수 없습니다.")
            self.grab_start = 0
            return False

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 40, 170)
        debug_img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        obj_x_min, obj_y_min, obj_x_max, obj_y_max = self.get_object_bounding_box()
        target_x_min, target_y_min, target_x_max, target_y_max = self.target_area
        tgt_cx = (target_x_min + target_x_max) / 2.0
        tgt_cy = (target_y_min + target_y_max) / 2.0

        # 타겟 영역도 디버그 이미지에 그려주기 (파란색 박스)
        cv2.rectangle(
            debug_img,
            (target_x_min, target_y_min),
            (target_x_max, target_y_max),
            (255, 0, 0), 2
        )
        cv2.circle(debug_img, (int(tgt_cx), int(tgt_cy)), 4, (255, 0, 0), -1)

        if obj_x_min == 0 and obj_y_min == 0 and obj_x_max == 0 and obj_y_max == 0:
            print(" Canny 엣지 디텍션으로 큐브를 찾지 못했습니다.")
            self.grab_start = 0

            cv2.putText(
                debug_img, "No object",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 0, 255), 2
            )
            cv2.imshow("position_debug", debug_img)
            cv2.waitKey(1)
            return False

        obj_cx = (obj_x_min + obj_x_max) / 2.0
        obj_cy = (obj_y_min + obj_y_max) / 2.0

        dx = obj_cx - tgt_cx
        dy = obj_cy - tgt_cy
        dist = (dx**2 + dy**2) ** 0.5
        print(f"dx={dx:.1f}, dy={dy:.1f}, dist={dist:.1f}")

        cv2.rectangle(
            debug_img,
            (int(obj_x_min), int(obj_y_min)),
            (int(obj_x_max), int(obj_y_max)),
            (0, 255, 0), 2
        )
        cv2.circle(debug_img, (int(obj_cx), int(obj_cy)), 4, (0, 255, 0), -1)

        cv2.line(
            debug_img,
            (int(tgt_cx), int(tgt_cy)),
            (int(obj_cx), int(obj_cy)),
            (255, 255, 255), 1
        )
        status_text = f"dx={dx:.1f}, dy={dy:.1f}, dist={dist:.1f}"
        cv2.putText(
            debug_img, status_text,
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            (255, 255, 255), 2
        )

        # 허용 오차 안/밖 여부 표시
        if dist <= tolerance:
            self.grab_start = 1
            ok_flag = True
        else:
            self.grab_start = 0
            ok_flag = False
        
        self.debug_img = debug_img
        return ok_flag

    def check_position_cv(self, tolerance: int = 25) -> bool:
        if self.image is None:
            print(" self.image가 없어 위치를 계산할 수 없습니다.")
            self.grab_start = 0
            return False

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 40, 170)
        debug_img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # ❗ 1. 새 함수 호출 및 각도 정보 획득 ❗
        obj_cx, obj_cy, obj_w, obj_h, obj_angle = self.get_object_rotated_info()
        
        target_x_min, target_y_min, target_x_max, target_y_max = self.target_area
        tgt_cx = (target_x_min + target_x_max) / 2.0
        tgt_cy = (target_y_min + target_y_max) / 2.0

        # 타겟 영역 디버그 이미지에 그리기 (파란색 박스)
        cv2.rectangle(
            debug_img,
            (target_x_min, target_y_min),
            (target_x_max, target_y_max),
            (255, 0, 0), 2
        )
        cv2.circle(debug_img, (int(tgt_cx), int(tgt_cy)), 4, (255, 0, 0), -1)

        # ❗ 2. 객체 미발견 조건 수정 ❗
        if obj_cx == 0 and obj_cy == 0:
            print(" Canny 엣지 디텍션으로 큐브를 찾지 못했습니다.")
            self.grab_start = 0
            cv2.putText(
                debug_img, "No object",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 0, 255), 2
            )
            self.debug_img = debug_img
            cv2.imshow("position_debug", debug_img)
            cv2.waitKey(1)
            return False

        dx = obj_cx - tgt_cx
        dy = obj_cy - tgt_cy
        dist = (dx**2 + dy**2) ** 0.5
        print(f"dx={dx:.1f}, dy={dy:.1f}, dist={dist:.1f}, angle={obj_angle:.1f}")

        # ❗ 4. 회전된 경계 상자 그리기 (minAreaRect 시각화) ❗
        rect = ((obj_cx, obj_cy), (obj_w, obj_h), obj_angle)
        box = cv2.boxPoints(rect)
        box = np.int0(box) # 4개의 꼭짓점을 정수형으로 변환
        cv2.drawContours(debug_img, [box], 0, (0, 255, 255), 2) # 노란색으로 그리기

        # 5. 객체 중심점 그리기 (녹색 원)
        cv2.circle(debug_img, (int(obj_cx), int(obj_cy)), 4, (0, 255, 0), -1)

        # 6. 타겟-객체 중심 연결선 및 텍스트 표시
        cv2.line(
            debug_img,
            (int(tgt_cx), int(tgt_cy)),
            (int(obj_cx), int(obj_cy)),
            (255, 255, 255), 1
        )
        status_text = f"dx={dx:.1f}, dy={dy:.1f}, dist={dist:.1f}, angle={obj_angle:.1f}"
        cv2.putText(
            debug_img, status_text,
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            (255, 255, 255), 2
        )

        # 7. 허용 오차 확인 (위치만 확인)
        if dist <= tolerance:
            self.grab_start = 1
            ok_flag = True
        else:
            self.grab_start = 0
            ok_flag = False
        
        self.debug_img = debug_img
        return ok_flag, obj_angle
    


    def update_image(self) -> bool:
        if not self.cap.isOpened():
            print(" 카메라가 열려있지 않아 이미지 업데이트에 실패했습니다.")
            return False
            
        ret = False
        frame = None
        read_attempts = 0
        
        while not ret:
            time.sleep(0.05) 
            
            ret, frame = self.cap.read()
            read_attempts += 1

            if not ret:
                time.sleep(0.1) 
        self.image = frame  
        return True

    def start_grab(self, img):
        
        self.image = img 
        
        frame = self.Color_Recongnize(img)

        return frame
    
    
if __name__ == '__main__':
    
    capture = cv2.VideoCapture(0)
    grab = fault_grab(capture_source=capture)
    
    while capture.isOpened():
        _, img = capture.read()
        img = grab.start_grab(img)
        if grab.debug_img is not None:
           cv2.imshow("position_debug", grab.debug_img)
        cv2.imshow("img", img)
        action = cv2.waitKey(10) & 0xff
        if action == ord('q') or action == 27:
            cv2.destroyAllWindows()
            capture.release()
            break

    cv2.destroyAllWindows()
    capture.release()
