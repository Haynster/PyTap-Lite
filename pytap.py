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

def get_nsdata(data):
    dictionary = {}
    if "NS.keys" in data and "NS.objects" in data:
        # Sometimes the dictionaries in the converted SQL are in 2 seperate arrays of keys and values, this puts those together.
        key = 0
        for y in data["NS.keys"]:
            dictionary[y] = data["NS.objects"][key]
            key = key + 1
        return dictionary
    elif "NS.objects" in data:
        # If its just an Array this gets it.
        return data["NS.objects"]
    elif "NS.string" in data:
        # If its just an String this gets it.
        return data["NS.string"]

with open('data.json', 'a') as f:
    data = get_all()

    # Organize ZACTIONS in ZBEHAVIOURDATA to be clearer
    if "ZBEHAVIOURDATA" in data:
        for x in data["ZBEHAVIOURDATA"]:
            z_actions = get_nsdata(x["ZACTIONS"]["NS.data"])
            x["ZACTIONS"] = z_actions

    
    pyperclip.copy(json_util.dumps(data))
    f.write(json_util.dumps(data))
                