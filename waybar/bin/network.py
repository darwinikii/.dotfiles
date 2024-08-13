#!/usr/bin/env python3

import subprocess
import sys
import json

def speedtest():
    speedtest = subprocess.run(["/usr/bin/speedtest --no-upload --csv --bytes"], check=True, capture_output=True, shell=True).stdout.decode().split(",")[6]
    speed = float(speedtest) / 1024 / 1024
    return str(speed)[0:4]

nmcli = subprocess.run(["/usr/bin/nmcli -f TYPE,STATE -t d"], check=True, capture_output=True, shell=True).stdout.decode()
devices = nmcli.split("\n")
devices.pop()

i = 0
for device in devices:
    device = device.split(":")
    device[1] = device[1].split(" ")[0]
    devices[i] = device
    i = i + 1

devices = [device[0] for device in devices if (device[0] == 'ethernet' or device[0] == 'wifi') and device[1] == "connected"][::-1]

text = "󰖪"

if "ethernet" in devices:
    text = "󰈀"
elif "wifi" in devices:
    text = ""

sys.stdout.write(json.dumps({"text": text, "class": "custom-network", "alt": "network"}) + "\n")
sys.stdout.flush()

text = "󰖪"

if "ethernet" in devices:
    try:
        text = speedtest() + "Mbps 󰈀"
    except Exception as e:
        text = "󰈀"
elif "wifi" in devices:
    try:
        text = speedtest() + "Mbps "
    except Exception as e:
        text = ""

sys.stdout.write(json.dumps({"text": text, "class": "custom-network", "alt": "network"}) + "\n")
sys.stdout.flush()

exit(0)