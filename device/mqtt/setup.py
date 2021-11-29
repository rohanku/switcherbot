import os
import psycopg2
from uuid import uuid4
import json
from decouple import config

DATABASE_URI = config('DATABASE_URI')
DEVICE_URI = config('DEVICE_URI')
DEVICE_PWD = config('DEVICE_PWD')

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
        cur.execute('INSERT INTO devices(id, cert) VALUES (%s, %s);', (device_id, device_cert))

def copy_to_device(relative_file_path):
    os.system(f'sshpass -p {DEVICE_PWD} scp -r {relative_file_path} {DEVICE_URI}:/home/pi/switcherbot/device/mqtt/{relative_file_path}')


if __name__=="__main__":
    os.system('openssl req -x509 -newkey rsa:2048 -keyout secret/rsa_private.pem -nodes -out rsa_cert.pem -subj "/CN=unused"')
    device_id = str(uuid4())
    with get_conn() as conn:
        while not check_uuid:
            device_id = uuid4()
        with open('device_config.json', 'w') as conf:
            conf.write(json.dumps({'device_id': device_id}))
        with open('rsa_cert.pem', 'rb') as cert:
            create_device(conn, device_id, cert.read())

    for f in ('secret/rsa_private.pem', 'rsa_cert.pem', 'device_config.json'):
        copy_to_device(f)



