import os
import io
import psycopg2
from uuid import uuid4
import json
from decouple import config

from google.api_core.exceptions import AlreadyExists
from google.cloud import iot_v1
from google.cloud import pubsub
from google.oauth2 import service_account
from google.protobuf import field_mask_pb2 as gp_field_mask
from googleapiclient import discovery
from googleapiclient.errors import HttpError

DATABASE_URI = config('DATABASE_URI')
DEVICE_URI = config('DEVICE_URI')
DEVICE_PWD = config('DEVICE_PWD')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '../../server/secret/switcherbot-1fa22af39786.json'

project_id = 'switcherbot'
cloud_region = 'us-central1'
registry_id = 'registry'

client = iot_v1.DeviceManagerClient()

def get_conn():
    return psycopg2.connect(DATABASE_URI)

def execute(f, *args):
    with get_conn() as conn:
        return f(conn, *args)

def check_uuid(conn, uuid):
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM devices WHERE id = %s;', (uuid,))
        return cur.fetchone()[0] == 0
    

def create_device(conn, device_id, device_cert):
    with conn.cursor() as cur:
        cur.execute('INSERT INTO devices(id) VALUES (%s);', (device_id,))

    parent = client.registry_path(project_id, cloud_region, registry_id)

    with io.open('rsa_cert.pem') as f:
        certificate = f.read()

    # Note: You can have multiple credentials associated with a device.
    device_template = {
        "id": device_id,
        "credentials": [
            {
                "public_key": {
                    "format": iot_v1.PublicKeyFormat.RSA_X509_PEM,
                    "key": certificate,
                }
            }
        ],
    }

    return client.create_device(request={"parent": parent, "device": device_template}) 

def copy_to_device(relative_file_path):
    os.system(f'sshpass -p {DEVICE_PWD} scp -r {relative_file_path} {DEVICE_URI}:/home/pi/switcherbot/device/mqtt/{relative_file_path}')


if __name__=="__main__":
    os.system('openssl req -x509 -newkey rsa:2048 -keyout secret/rsa_private.pem -nodes -out rsa_cert.pem -subj "/CN=unused"')
    device_id = f'dev{str(uuid4())}'
    with get_conn() as conn:
        while not check_uuid:
            device_id = uuid4()
        with open('device_config.json', 'w') as conf:
            conf.write(json.dumps({'device_id': device_id}))
        with open('rsa_cert.pem', 'rb') as cert:
            create_device(conn, device_id, cert.read())

    for f in ('secret/rsa_private.pem', 'rsa_cert.pem', 'device_config.json'):
        copy_to_device(f)



