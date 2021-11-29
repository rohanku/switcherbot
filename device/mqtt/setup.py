import os
import psycopg2
from uuid import uuid4
import json

def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URI'])

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

if __name__=="__main__":
    os.system('openssl req -x509 -newkey rsa:2048 -keyout secret/rsa_private.pem -nodes -out rsa_cert.pem -subj "/CN=unused"')
    os.system('curl -O https://pki.goog/roots.pem')
    device_id = uuid4()
    with get_conn() as conn:
        while not check_uuid:
            device_id = uuid4()
        with open('device_config.json', 'wb') as conf:
            conf.write(json.dumps({'device_id': device_id}))
        with open('rsa_cert.pem', 'rb') as cert:
            create_device(conn, device_id, cert.read())



