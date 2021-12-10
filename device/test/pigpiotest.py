import pigpio

GPIO=12

pi = pigpio.pi()
pi.set_mode(GPIO, pigpio.OUTPUT)

minPulse = 500
maxPulse = 2500

try:
    while True:
        percent = int(input())
        t = int(minPulse + (maxPulse - minPulse) * percent/100)
        square = [pigpio.pulse(1<<GPIO, 0, t), pigpio.pulse(0, 1<<GPIO, t)]
        pi.wave_clear()
        pi.wave_add_generic(square)
        wid = pi.wave_create()
        pi.wave_send_once(wid)
        pi.wave_delete(wid)
except KeyboardInterrupt:
    print("exiting")
    pi.stop()
