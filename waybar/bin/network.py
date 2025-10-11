#!/usr/bin/env python3

import subprocess
import sys
import json
import time

ETHERNET = "󰈀"
WIFI_CONNECTED = "󰖩"
WIFI_NOTCONNECTED = "󰖪"
BLUETOOTH_ON = "󰂯"
BLUETOOTH_OFF = "󰂲"

speed = ""
network = ""
bluetooth = ""


def speedtest():
    speedtest = (
        subprocess.run(
            ["/usr/bin/speedtest --no-upload --csv --bytes"],
            check=True,
            capture_output=True,
            shell=True,
        )
        .stdout.decode()
        .split(",")[6]
    )

    speed = float(speedtest) / 1024 / 1024
    return str(round(speed) if round(speed, 1) == round(speed) else round(speed, 1))


def is_bluetooth_active():
    try:
        bluetoothctl = subprocess.run(
            ["/usr/bin/bluetoothctl show"],
            check=True,
            capture_output=True,
            shell=True,
        ).stdout.decode()
        informations = bluetoothctl.split("\n\t")

        is_Active = False
        for info in informations:
            info = info.split(":")
            if info[0] == "Powered" and info[1] == " yes":
                is_Active = True

        return is_Active
    except Exception as e:
        return None


def get_devices():
    nmcli = subprocess.run(
        ["/usr/bin/nmcli -f TYPE,STATE -t d"],
        check=True,
        capture_output=True,
        shell=True,
    ).stdout.decode()
    devices = nmcli.split("\n")
    devices.pop()

    i = 0
    for device in devices:
        device = device.split(":")
        device[1] = device[1].split(" ")[0]

        devices[i] = device

        i = i + 1

    return devices


def main():
    global speed
    global network
    global bluetooth

    className = "custom-network"

    devices = get_devices()
    for device in devices:
        deviceType = device[0]
        deviceStatus = device[1]

        if network == "":
            if deviceType == "ethernet" or deviceType == "wifi":
                if deviceType == "ethernet" and deviceStatus == "connected":
                    network = ETHERNET
                elif deviceType == "wifi":
                    if deviceStatus == "connected":
                        network = WIFI_CONNECTED
                    else:
                        network = WIFI_NOTCONNECTED
        elif network == WIFI_CONNECTED:
            if deviceType == "ethernet" and deviceStatus == "connected":
                network = ETHERNET
        elif network == WIFI_NOTCONNECTED:
            if deviceType == "ethernet" and deviceStatus == "connected":
                network = ETHERNET
            elif deviceType == "wifi" and deviceStatus == "connected":
                network = WIFI_CONNECTED

        if bluetooth == "":
            bluetooth_status = is_bluetooth_active()

            if bluetooth_status == True:
                bluetooth = BLUETOOTH_ON
            elif bluetooth_status == False:
                bluetooth = BLUETOOTH_OFF

    text = f"{speed + ' Mbps ' if speed != '' else ''}{network}{' ' + bluetooth if bluetooth != '' else ''}"

    sys.stdout.write(
        json.dumps({"text": text, "class": className, "alt": "network"}) + "\n"
    )
    sys.stdout.flush()

    if speed == "" and network != "" and network != WIFI_NOTCONNECTED:
        try:
            speed = speedtest()
        except Exception as e:
            pass

    text = f"{speed + ' Mbps ' if speed != '' else ''}{network}{' ' + bluetooth if bluetooth != '' else ''}"

    sys.stdout.write(
        json.dumps({"text": text, "class": className, "alt": "network"}) + "\n"
    )
    sys.stdout.flush()


i = 1
if __name__ == "__main__":
    while True:
        main()
        if i > 3:
            exit(0)
        elif network == "" or network == WIFI_NOTCONNECTED:
            time.sleep(i * 10)
            i += 1
        else:
            exit(0)
