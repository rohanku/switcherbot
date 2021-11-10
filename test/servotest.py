import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)

GPIO.output(12, GPIO.LOW)

minPulse = 500
maxPulse = 2500

try:
    while True:
        percent = int(input())
        t = (minPulse+(maxPulse-minPulse)*percent/100)/1e6
        GPIO.output(12, GPIO.HIGH)
        time.sleep(t)
        GPIO.output(12, GPIO.LOW)
        time.sleep(1/50-t)
        GPIO.output(12, GPIO.HIGH)
        time.sleep(t)
        GPIO.output(12, GPIO.LOW)
except KeyboardInterrupt:
    print("exiting")
    GPIO.cleanup()



