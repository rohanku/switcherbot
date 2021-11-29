from flask import Flask, request
import os
import hashlib, binascii

app = Flask(__name__)

def str_hex(s):
    return "".join(['{:02x}'.format(ord(c)) for c in s])

def wpa_psk(ssid, password):
    dk = hashlib.pbkdf2_hmac('sha1', str.encode(password), str.encode(ssid), 4096, 32)
    return binascii.hexlify(dk)

def overwrite(path, contents):
    f = open(path, "w")
    f.write(contents)
    f.close()

def set_config(dhcpcd_conf_new, wpa_supplicant_new):
    overwrite("/etc/dhcpcd.conf", dhcpcd_conf_new)
    overwrite("/etc/wpa_supplicant/wpa_supplicant.conf", wpa_supplicant_new)

@app.route("/provision")
def provision():
    ssid = request.args.get('ssid')
    psk = request.args.get('psk')
    dk = wpa_psk(ssid, psk)
    dhcpcd_conf_new = open("/home/pi/switcherbot/device/provisioning/templates/provisioned/dhcpcd.conf").read()
    wpa_supplicant_new = open("/home/pi/switcherbot/device/provisioning/templates/provisioned/wpa_supplicant.conf").read() % (str_hex(ssid), dk.decode('utf-8'))
    set_config(dhcpcd_conf_new, wpa_supplicant_new)
    os.system("sudo systemctl disable hostapd && sudo systemctl mask hostapd")
    return "Finished provisioning customer!"

@app.route("/reboot")
def reboot():
    os.system("sleep 1 && sudo reboot &")
    return "Your device will reboot shortly..."

@app.route("/reset")
def reset():
    dhcpcd_conf_old = open("/home/pi/switcherbot/device/provisioning/templates/unprovisioned/dhcpcd.conf").read()
    wpa_supplicant_old = open("/home/pi/switcherbot/device/provisioning/templates/unprovisioned/wpa_supplicant.conf").read()
    set_config(dhcpcd_conf_old, wpa_supplicant_old)
    os.system("sudo systemctl unmask hostapd && sudo systemctl enable hostapd")
    return "Finished resetting device!"

@app.route("/config")
def provision():
    config = open("/home/pi/switcherbot/device/mqtt/device_config.json").read()
    return config

app.run(host='0.0.0.0', port=5000)
