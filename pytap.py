import sqlite3
import json
import base64
from bson import json_util
import pyperclip

# Connect to the database
conn = sqlite3.connect('Level.sqlite')
cursor = conn.cursor()

import plistlib
from plistlib import UID

def get_all():
    funnynoodledoodle = {}
    for x in tables:
        funnynoodledoodle[x] = convert_table(x)

    return funnynoodledoodle

def deep_unarchive(obj):
    """Recursively unarchive nested NSKeyedArchiver blobs."""
    if isinstance(obj, bytes) and obj.startswith(b'bplist00'):
        try:
            obj = plistlib.loads(obj)
        except Exception:
            return obj  # leave as-is if cannot parse

    if isinstance(obj, dict) and obj.get("$archiver") == "NSKeyedArchiver" and "$objects" in obj:
        objects = obj["$objects"]
        top = obj.get("$top", {})

        def resolve(inner):
            if isinstance(inner, UID):
                return resolve(objects[inner.data])
            elif isinstance(inner, bytes) and inner.startswith(b'bplist00'):
                return deep_unarchive(inner)
            elif isinstance(inner, dict):
                return {k: resolve(v) for k, v in inner.items()}
            elif isinstance(inner, list):
                return [resolve(x) for x in inner]
            else:
                return inner

        # Attempt to resolve root, fallback to first UID if not found
        root_uid = top.get("root") or top.get("action")
        if root_uid is not None:
            return resolve(root_uid)
        return {k: resolve(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [deep_unarchive(x) for x in obj]
    if isinstance(obj, dict):
        return {k: deep_unarchive(v) for k, v in obj.items()}

    return obj

def convert_table(tbl, db_path="Level.sqlite"):
    """Fetch a table from SQLite and return fully unarchived JSON."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {tbl}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    results = [dict(zip(columns, row)) for row in rows]

    # Deeply unarchive any bplist bytes
    for row in results:
        for k, v in row.items():
            row[k] = deep_unarchive(v)

    return results
            
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

with open('data.json', 'a') as f:
    data = get_all()

    # Organize ZACTIONS to be clearer
    if "ZBEHAVIOURDATA" in data:
        behaviour_index = 0
        for x in data["ZBEHAVIOURDATA"]:
            key = 0
            behaviour_data = x
            z_actions = {}
            for y in x["ZACTIONS"]["NS.data"]["NS.keys"]:
                z_actions[y] = x["ZACTIONS"]["NS.data"]["NS.objects"][key]
                key = key + 1
            behaviour_data["ZACTIONS"] = z_actions
            data["ZBEHAVIOURDATA"][behaviour_index] = behaviour_data
            behaviour_index = behaviour_index + 1
    
    pyperclip.copy(json_util.dumps(data))
    f.write(json_util.dumps(data))
                