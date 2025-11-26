import time, threading, curses
from Arm_Lib import Arm_Device

MIN_ANGLE, MAX_ANGLE = 0, 180

def clamp(v, lo=MIN_ANGLE, hi=MAX_ANGLE):
    return max(lo, min(hi, v))

def read_feedback_loop(Arm, angles_fb, stop_evt, period=0.05):
    while not stop_evt.is_set():
        try:
            for i in range(6):
                val = Arm.Arm_serial_servo_read(i+1)  
                if val is None:
                    continue
                angles_fb[i] = int(round(val))
                time.sleep(0.005)
        except Exception:
            pass
        time.sleep(max(0.0, period - 6*0.005))

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)

    Arm = Arm_Device()
    time.sleep(0.1)

    angles_cmd = [90]*6
    angles_fb  = [90]*6
    step_deg   = 1
    move_time  = 500

    # init position
    Arm.Arm_serial_servo_write6(*angles_cmd, move_time)
    time.sleep(0.6)

    # feedback thread start
    stop_evt = threading.Event()
    t_fb = threading.Thread(target=read_feedback_loop, args=(Arm, angles_fb, stop_evt, 0.05), daemon=True)
    t_fb.start()

    last_move_ts = time.time()

    def draw():
        stdscr.erase()
        stdscr.addstr(0, 0, "DOFBOT Keyboard Teleop + Live Feedback (Q=Quit, R=Reset)")
        stdscr.addstr(1, 0, "S1:A/D  S2:W/S  S3:T/G  S4:Y/H  S5:U/J  S6:I/K   [/]=step  ;/'=time")
        stdscr.addstr(2, 0, f"Step:{step_deg:>2} deg   MoveTime:{move_time} ms")
        stdscr.addstr(4, 0, "Feedback Angles (deg):")
        stdscr.addstr(5, 0, f"S1:{angles_fb[0]:>3}  S2:{angles_fb[1]:>3}  S3:{angles_fb[2]:>3}  "
                             f"S4:{angles_fb[3]:>3}  S5:{angles_fb[4]:>3}  S6:{angles_fb[5]:>3}")
        stdscr.addstr(7, 0, "Cmd Angles (deg):")
        stdscr.addstr(8, 0, f"S1:{angles_cmd[0]:>3}  S2:{angles_cmd[1]:>3}  S3:{angles_cmd[2]:>3}  "
                             f"S4:{angles_cmd[3]:>3}  S5:{angles_cmd[4]:>3}  S6:{angles_cmd[5]:>3}")
        stdscr.refresh()

    def apply_servo(idx, delta):
        angles_cmd[idx] = clamp(angles_cmd[idx] + delta)
        Arm.Arm_serial_servo_write(idx + 1, angles_cmd[idx], move_time)

    draw()

    try:
        while True:
            ch = stdscr.getch()
            if ch != -1:
                c = chr(ch).lower() if 0 <= ch < 256 else None

                if c == 'q':
                    break
                if c == 'r':
                    angles_cmd[:] = [90]*6
                    Arm.Arm_serial_servo_write6(*angles_cmd, 800)
                    time.sleep(0.5)
                    draw(); continue

                if c == '[': step_deg = max(1, step_deg - 1); draw(); continue
                if c == ']': step_deg = min(30, step_deg + 1); draw(); continue
                if c == ';': move_time = max(50,  move_time - 50); draw(); continue
                if c == "'": move_time = min(2000, move_time + 50); draw(); continue

                moved = False
                if c == 'a': apply_servo(0, -step_deg); moved = True
                if c == 'd': apply_servo(0, +step_deg); moved = True
                if c == 'w': apply_servo(1, +step_deg); moved = True
                if c == 's': apply_servo(1, -step_deg); moved = True
                if c == 't': apply_servo(2, +step_deg); moved = True
                if c == 'g': apply_servo(2, -step_deg); moved = True
                if c == 'y': apply_servo(3, +step_deg); moved = True
                if c == 'h': apply_servo(3, -step_deg); moved = True
                if c == 'u': apply_servo(4, +step_deg); moved = True
                if c == 'j': apply_servo(4, -step_deg); moved = True
                if c == 'i': apply_servo(5, +step_deg); moved = True
                if c == 'k': apply_servo(5, -step_deg); moved = True
                if c == 'b':
                  Arm.Arm_serial_set_torque(0)
                if moved:
                    last_move_ts = time.time()

            if time.time() - last_move_ts > 0.3:
                angles_cmd[:] = [int(x) for x in angles_fb]

            draw()
            time.sleep(0.02)

    except KeyboardInterrupt:
        pass
    finally:
        stop_evt.set()
        try: t_fb.join(timeout=0.5)
        except: pass
        del Arm
        curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)
