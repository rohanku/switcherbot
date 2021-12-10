from config import Config
import psycopg2
from errors import RegistryExistsException

def get_conn():
    return psycopg2.connect(Config.DATABASE_URI)

def execute(f, *args):
    with get_conn() as conn:
        return f(conn, *args)

def check_registry_exists_for_user(conn, user_id, registry_name):
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM permissions INNER JOIN registries on permissions.registry_id = registries.id WHERE permissions.user_id = %s AND registries.name = %s;', (user_id, registry_name))
        if cur.fetchone()[0] > 0:
            raise RegistryExistsException()

def create_registry(conn, user_id, registry_name):
    check_registry_exists_for_user(conn, user_id, registry_name)
    with conn.cursor() as cur:
        cur.execute('INSERT INTO registries(name) VALUES (%s) RETURNING id', (registry_name,))
        registry_id = cur.fetchone()[0]
        cur.execute('INSERT INTO permissions VALUES (%s, %s, True)', (user_id, registry_id))
        return registry_id

def get_registries(conn, user_id):
    with conn.cursor() as cur:
        cur.execute('SELECT registries.id, registries.name, permissions.admin FROM permissions INNER JOIN registries on permissions.registry_id = registries.id WHERE permissions.user_id = %s', (user_id,))
        return cur.fetchall()

def get_devices(conn, registry_id):
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM devices WHERE registry_id = %s', (registry_id,))
        return cur.fetchall()

def is_admin(conn, user_id, registry_id):
    with conn.cursor() as cur:
        cur.execute('SELECT permissions.admin FROM permissions INNER JOIN registries on permissions.registry_id = registries.id WHERE permissions.user_id = %s AND registries.id = %s', (user_id, registry_id))
        perms = cur.fetchall()
        return len(perms) > 0 and perms[0][0]

def has_access(conn, user_id, registry_id):
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM permissions INNER JOIN registries on permissions.registry_id = registries.id WHERE permissions.user_id = %s AND registries.id = %s;', (user_id, registry_id))
        return cur.fetchone()[0] > 0

def get_registry_info(conn, registry_id):
    with conn.cursor() as cur:
        cur.execute('SELECT registries.id, registries.name FROM registries WHERE registries.id = %s', (registry_id,))
        return cur.fetchone()

def update_registry_info(conn, registry_id, registry_name):
    with conn.cursor() as cur:
        cur.execute('UPDATE registries SET name = %s WHERE id = %s', (registry_name, registry_id))

def get_members(conn, registry_id):
    with conn.cursor() as cur:
        cur.execute('SELECT user_id, admin FROM permissions WHERE permissions.registry_id = %s', (registry_id,))
        return cur.fetchall()

def get_device_info(conn, device_id):
    with conn.cursor() as cur:
        cur.execute('SELECT id, registry_id FROM devices WHERE id = %s', (device_id,))
        return cur.fetchone()

def update_device_info(conn, device_id, registry_id):
    with conn.cursor() as cur:
        cur.execute('UPDATE devices SET registry_id = %s WHERE id = %s', (registry_id, device_id))

