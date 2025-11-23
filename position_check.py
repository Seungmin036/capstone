
import cv2
import numpy as np
import random
import time
from Arm_Lib import Arm_Device
import threading

class position_check():
    def __init__(self):
        
        self.Arm = Arm_Device()
        self.color_name = None

        self.look_at = [90, 164, 18, 0, 90, 90]
        self.p_top = [90, 80, 50, 50, 90]

        self.p_Yellow = [65, 22, 64, 56, 270]
        self.p_Red = [118, 19, 66, 56, 270]
        self.p_Green = [136, 66, 20, 29, 270]
        self.p_Blue = [44, 66, 20, 28, 270]
        self.p_gray = [90, 48, 35, 30, 270]
        
        self.p_Yellow_check = [65, 80, 18, 0, 90] 
        self.p_Red_check = [118, 19, 66, 56, 270]
        self.p_Green_check = [136, 83, 23, 0, 90]
        self.p_Blue_check = [44, 83, 23, 0, 90]

        self.g_state_arm = 0
        self.started = 0
        self.grab_start = 0
            
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
        if index == 1: 
            self.arm_move(self.p_top, 1000) 
            self.arm_move(self.p_Yellow_check, 1000)
            time.sleep(3)
            self.arm_move(self.p_Yellow, 1000)
            time.sleep(3)
            self.arm_move(self.p_top, 1000)

        elif index == 2: 
            self.arm_move(self.p_top, 1000)
            self.arm_move(self.p_Red_check, 1000)
            time.sleep(3)
            self.arm_move(self.p_Red, 1000)
            time.sleep(3)
            self.arm_move(self.p_top, 1000)
            
        elif index == 3: 
            self.arm_move(self.p_top, 1000)
            self.arm_move(self.p_Green_check, 1000)
            time.sleep(3)
            self.arm_move(self.p_Green, 1000)
            time.sleep(3)
            self.arm_move(self.p_top, 1000)
            
        elif index == 4: 
            self.arm_move(self.p_top, 1000)
            self.arm_move(self.p_Blue_check, 1000)
            time.sleep(3)
            self.arm_move(self.p_Blue, 1000)
            time.sleep(3)
            self.arm_move(self.p_top, 1000)
    
    def put_down_block(self):
        self.arm_move(self.p_gray, 1000)
        self.arm_clamp_block(0) 
        self.Arm.Arm_serial_servo_write6_array(self.look_at, 1000)
        time.sleep(1)
        
    def start_move_arm(self, index):
        if self.g_state_arm == 0:
            closeTid = threading.Thread(target = self.ctrl_arm_move, args = [index])
            closeTid.setDaemon(True)
            closeTid.start()
            
            self.g_state_arm = 1

    def Color_Recongnize(self):
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
        
        if self.g_state_arm == 0:
            input_color = input("색상 입력하기 (yellow/red/green/blue, 종료: q): ").strip().lower()
            
            if input_color == 'q':
                return False 
            
            color_name = {'name': input_color}
            
            if color_name['name'] == 'yellow':
                self.start_move_arm(1) 
            elif color_name['name'] == 'red':
                self.start_move_arm(2)
            elif  color_name['name'] == 'green':
                self.start_move_arm(3)
            elif color_name['name'] == 'blue':
                self.start_move_arm(4)
            else:
                print("유효하지 않은 색상입니다. 다시 입력해 주세요.")
        else:
            print("로봇 동작 중... 입력 대기 중.")
            
        return True
            
if __name__ == '__main__':
    
    pos = position_check()
    
    running = True
    while running:
        running = pos.Color_Recongnize()
        time.sleep(0.5) 
        
    print("프로그램 종료.")
