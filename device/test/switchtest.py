import pigpio
import time

GPIO=12

pi = pigpio.pi()
pi.set_mode(GPIO, pigpio.OUTPUT)

minPulse = 500
maxPulse = 2500

def move_to(percent):
    t = int(minPulse+(maxPulse-minPulse)*percent/100)
    square = [pigpio.pulse(1<<GPIO, 0, t), pigpio.pulse(0, 1<<GPIO, t)]
    pi.wave_clear()
    pi.wave_add_generic(square)
    wid = pi.wave_create()
    pi.wave_send_once(wid)
    pi.wave_delete(wid)

upper = 60
middle = 55
lower = 50

move_to(middle)

try:
    while True:
        command = input()
        if command == 'on':
            move_to(upper)
            time.sleep(0.5)
            move_to(middle)
        elif command == 'off':
            move_to(lower)
            time.sleep(0.5)
            move_to(middle)
        else:
            print('invalid command')


except KeyboardInterrupt:
    print("exiting")
    pi.stop()



