# -*- coding: UTF-8 -*-
import json
from base64 import b64decode, b64encode
from pickle import APPEND
from re import findall, sub


def decode(s):
    """Return a string containing a save code decoded from Base64 encoding."""
    # Changing some parts of the string for proper decoding.
    s = s.replace("%21END%21", "").replace("%3D", "=")

    # Decoding from Base64 encoding.
    s = s.encode()
    s = b64decode(s)
    s = s.decode()

    return s


def encode(s):
    """Return a string containing a save code encoded to Base64 encoding."""
    # Encoding to Base64 encoding.
    s = s.encode()
    s = b64encode(s)
    s = s.decode()

    # Changing some parts of the string for proper encoding.
    s = s.replace("=", "%3D") + "%21END%21"

    return s


def uncompress(s):
    """
    Return a string containing a JSON string representation of a save code
    (decoded from Base64 encoding) paired with metadata telling what each bit
    of information means.
    """
    metadata = json.load(open("metadata.json", "rt", encoding="utf-8"))

    # Splitting and pairing.6
    data = s.split("|")
    del data[1]

    # Asegurar que 'data' tenga entradas para todas las secciones del metadata
    expected = len(metadata.get("Sections", []))
    if len(data) < expected:
        data += [""] * (expected - len(data))
 
    save = {}
    save["Version"] = float(data[0])
    save["Save stats"] = dict(zip(metadata["Save stats"], data[1].split(";")))
    save["Appearance"] = dict(zip(metadata["Appearance"], data[1].split(",")))
    save["Appearance"]["Hair"] = save["Appearance"]["Hair"].split(";")[-1]
    print(save)
    save["Settings"] = dict(zip(metadata["Settings"], data[2]))
    save["Stats"] = dict(zip(metadata["Stats"], data[3].split(";")[:-1]))

    save["Buildings"] = {}
    data[4] = data[4].split(";")
    data[4] = [i.split(",") for i in data[4][:-1]]
    for building, building_dataset in zip(metadata["Buildings"], data[4]):
        save["Buildings"][building] = dict(
                zip(metadata["Buildings data"], building_dataset)
            )

    save["Upgrades"] = dict(zip(metadata["Upgrades"], findall("..", data[5])))
    save["Achievements"] = dict(zip(metadata["Achievements"], data[6]))
    save["Buffs"] = data[7][:-1].split(";") if data[7] else []
    save["Mod data"] = data[8][-1].split(";") if data[8] else []

    # Translating and typecasting.
    for k, vt in zip(save["Save stats"], metadata["Save stats types"]):
        save["Save stats"][k] = eval(vt)(save["Save stats"][k])

    for s, svt in zip(save["Stats"], metadata["Stats types"]):
        save["Stats"][s] = eval(svt)(save["Stats"][s])

    for b, bd in save["Buildings"].items():
        for d, bdvt in zip(bd, metadata["Buildings data types"]):
            save["Buildings"][b][d] = eval(bdvt)(save["Buildings"][b][d])

    for setting, value in save["Settings"].items():
        save["Settings"][setting] = "OFF" if value == "0" else "ON"

    d = {"0": False, "1": True}
    for upgrade in save["Upgrades"]:
        save["Upgrades"][upgrade] = {
            "Unlocked": d[save["Upgrades"][upgrade][0]],
            "Purchased":d[save["Upgrades"][upgrade][1]]
        }

    for achievement in save["Achievements"]:
        save["Achievements"][achievement] = {
            "Unlocked": d[save["Achievements"][achievement]]
        }

    print(save)
    # Output ##################################################################
    s = json.dumps(save, ensure_ascii=False, indent=4)
    s = "\n".join([sub("\.0,$", ",", line) for line in s.split("\n")])

    return s
    

def compress(save_code):
    """
    Return a save code (decoded from Base64 encoding) from a JSON string
    representation of save data paired with metadata telling what each bit of
    information means.
    """
    save = json.loads(save_code)

    # Translating and converting values #######################################
    save["Version"] = str(save["Version"])
    for section in ("Save stats", "Stats", "Buildings"):
        if section == "Buildings":
            for building in save[section]:
                for key, value in save[section][building].items():
                    save[section][building][key] = str(value)
            else:
                continue

        for key, value in save[section].items():
            save[section][key] = str(value)

    for setting, value in save["Settings"].items():
        save["Settings"][setting] = "0" if value == "OFF" else "1"

    d = {False: "0", True: "1"}
    for i, j in save["Upgrades"].items():
        save["Upgrades"][i] = d[j["Unlocked"]] + d[j["Purchased"]]

    for i, j in save["Achievements"].items():
        save["Achievements"][i] = d[j["Unlocked"]]

    # Putting things together #################################################
    for building in save["Buildings"] :
        building_values = save["Buildings"][building].values()
        save["Buildings"][building] = ",".join(building_values)

    save["Version"] = save["Version"] + "||"
    save["Save stats"] = ";".join(save["Save stats"].values()) + ";"
    save["Appearance"] = ",".join(save["Appearance"].values()) + "|"
    save["Settings"] = "".join(save["Settings"].values()) + "|"
    save["Stats"] = ";".join(save["Stats"].values()) + ";|"
    save["Buildings"] = ";".join(save["Buildings"].values()) + ";|"
    save["Upgrades"] = "".join(save["Upgrades"].values()) + "|"
    save["Achievements"] = "".join(save["Achievements"].values()) + "|"
    save["Buffs"] = ";".join(save["Buffs"])
    save["Mod data"] = ";".join(save["Mod data"]) if save["Mod data"] else ""

    save["Buffs"] += ";|" if save["Buffs"] else "|"
    save["Mod data"] += ";" if save["Mod data"] else ""

    save_code = "".join(save.values())

    # Output ##################################################################
    return save_code

def main():
    print("Opening file...")
    with open("original_save.txt", "r") as f:
        s = f.read()
    print("Read OK")

    s = decode(s)
    print("Decoded OK")

    with open("original_save_decoded.txt", "w") as f:
        f.write(s)

    s = uncompress(s)
    print("Uncompressed OK")

    with open("original_save_uncompressed.txt", "w") as f:
        f.write(s)

    s = compress(s)
    print("Compressed OK")

    with open("save_compressed.txt", "w") as f:
        f.write(s)

main()