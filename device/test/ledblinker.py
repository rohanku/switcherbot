import RPi.GPIO as GPIO
import time

led = 12

GPIO.setmode(GPIO.BCM)
GPIO.setup(led, GPIO.OUT)

from flask import Flask

app = Flask(__name__)

@app.route("/on")
def led_on():
    GPIO.output(led, GPIO.HIGH)
    return "<p>LED on</p>"

@app.route("/off")
def led_off():
    GPIO.output(led, GPIO.LOW)
    return "<p>LED off</p>"

@app.route("/blink")
def led_blink():
    for i in range(25):
        GPIO.output(led, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(led, GPIO.LOW)
        time.sleep(0.2)
    return "<p>LED blink</p>"
