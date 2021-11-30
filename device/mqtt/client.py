import datetime
import ssl
import jwt
import paho.mqtt.client as mqtt
import json
import time
import RPi.GPIO as GPIO

project_id='switcherbot'
cloud_region='us-central1'
registry_id='registry'
private_key_file='/home/pi/switcherbot/device/mqtt/secret/rsa_private.pem'
algorithm='RS256'
ca_certs='/home/pi/switcherbot/device/mqtt/roots.pem'
mqtt_bridge_hostname='mqtt.googleapis.com'
mqtt_bridge_port=8883
device_config = json.load(open('/home/pi/switcherbot/device/mqtt/device_config.json'))
device_id = device_config['device_id']


minimum_backoff_time = 1
MAXIMUM_BACKOFF_TIME = 32
should_backoff = False

led_gpio_pin = 12
led_on = False

GPIO.setmode(GPIO.BCM)
GPIO.setup(led_gpio_pin, GPIO.OUT)
GPIO.output(led_gpio_pin, GPIO.LOW)

def wait_for_connection(client):
    while True:
        try:
            client.connect(mqtt_bridge_hostname, mqtt_bridge_port)
            return
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            time.sleep(1)

def create_jwt(project_id, private_key_file, algorithm):
    """Creates a JWT (https://jwt.io) to establish an MQTT connection.
    Args:
     project_id: The cloud project ID this device belongs to
     private_key_file: A path to a file containing either an RSA256 or
             ES256 private key.
     algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
    Returns:
        A JWT generated from the given project_id and private key, which
        expires in 20 minutes. After 20 minutes, your client will be
        disconnected, and a new JWT will have to be generated.
    Raises:
        ValueError: If the private_key_file does not contain a known key.
    """

    token = {
        # The time that the token was issued at
        "iat": datetime.datetime.now(tz=datetime.timezone.utc),
        # The time the token expires.
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=20),
        # The audience field should always be set to the GCP project id.
        "aud": project_id,
    }

    # Read the private key file.
    with open(private_key_file, "r") as f:
        private_key = f.read()

    print(
        "Creating JWT using {} from private key file {}".format(
            algorithm, private_key_file
        )
    )

    return jwt.encode(token, private_key, algorithm=algorithm)

def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return "{}: {}".format(rc, mqtt.error_string(rc))


def on_connect(unused_client, unused_userdata, unused_flags, rc):
    """Callback for when a device connects."""
    print("on_connect", mqtt.connack_string(rc))

    # After a successful connect, reset backoff time and stop backing off.
    global should_backoff
    global minimum_backoff_time
    should_backoff = False
    minimum_backoff_time = 1


def on_disconnect(unused_client, unused_userdata, rc):
    """Paho callback for when a device disconnects."""
    print("on_disconnect", error_str(rc))

    # Since a disconnect occurred, the next loop iteration will wait with
    # exponential backoff.
    global should_backoff
    should_backoff = True


def on_publish(unused_client, unused_userdata, unused_mid):
    """Paho callback when a message is sent to the broker."""
    print("on_publish")


def on_message(unused_client, unused_userdata, message):
    """Callback when the device receives a message on a subscription."""
    global led_on
    payload = str(message.payload.decode("utf-8"))
    print(
        "Received message '{}' on topic '{}' with Qos {}".format(
            payload, message.topic, str(message.qos)
        )
    )
    if payload == 'toggle':
        if led_on:
            print("turning off LED")
            GPIO.output(led_gpio_pin, GPIO.LOW)
        else:
            print("turning on LED")
            GPIO.output(led_gpio_pin, GPIO.HIGH)
        led_on = not led_on


def get_client():
    """Create our MQTT client. The client_id is a unique string that identifies
    this device. For Google Cloud IoT Core, it must be in the format below."""
    client_id = "projects/{}/locations/{}/registries/{}/devices/{}".format(
        project_id, cloud_region, registry_id, device_id
    )
    print("Device client_id is '{}'".format(client_id))

    client = mqtt.Client(client_id=client_id)

    # With Google Cloud IoT Core, the username field is ignored, and the
    # password field is used to transmit a JWT to authorize the device.
    client.username_pw_set(
        username="unused", password=create_jwt(project_id, private_key_file, algorithm)
    )

    # Enable SSL/TLS support.
    client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

    # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
    # describes additional callbacks that Paho supports. In this example, the
    # callbacks just print to standard out.
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Connect to the Google MQTT bridge.
    wait_for_connection(client)

    # This is the topic that the device will receive configuration updates on.
    mqtt_config_topic = "/devices/{}/config".format(device_id)

    # Subscribe to the config topic.
    client.subscribe(mqtt_config_topic, qos=1)

    # The topic that the device will receive commands on.
    mqtt_command_topic = "/devices/{}/commands/#".format(device_id)

    # Subscribe to the commands topic, QoS 1 enables message acknowledgement.
    print("Subscribing to {}".format(mqtt_command_topic))
    client.subscribe(mqtt_command_topic, qos=1)

    return client




def listen_for_messages():
    """Listens for messages sent to the gateway and bound devices."""
    # [START iot_listen_for_messages]
    global minimum_backoff_time

    jwt_iat = datetime.datetime.now(tz=datetime.timezone.utc)
    jwt_exp_mins = 60
    # Use gateway to connect to server
    client = get_client()

    # Wait for about a minute for config messages.
    while True:
        client.loop()

        if should_backoff:
            # If backoff time is too large, give up.
            if minimum_backoff_time > MAXIMUM_BACKOFF_TIME:
                print("Exceeded maximum backoff time. Giving up.")
                break

            delay = minimum_backoff_time + random.randint(0, 1000) / 1000.0
            time.sleep(delay)
            minimum_backoff_time *= 2
            client.connect(mqtt_bridge_hostname, mqtt_bridge_port)

        seconds_since_issue = (datetime.datetime.now(tz=datetime.timezone.utc) - jwt_iat).seconds
        if seconds_since_issue > 60 * jwt_exp_mins:
            print("Refreshing token after {}s".format(seconds_since_issue))
            jwt_iat = datetime.datetime.now(tz=datetime.timezone.utc)
            client.loop()
            client.disconnect()
            client = get_client(
                project_id,
                cloud_region,
                registry_id,
                gateway_id,
                private_key_file,
                algorithm,
                ca_certs,
                mqtt_bridge_hostname,
                mqtt_bridge_port,
            )

        time.sleep(1)

while True:
    try:
        listen_for_messages()
    except KeyboardInterrupt:
        print("Quitting...")
        break
    except Exception as error:
        print(error)
