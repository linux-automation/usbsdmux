import os
import sys
import configparser
import json


class Config:
    """
    Reads the configuration file by default at /etc/usbsdmux.config
    """

    def __init__(self, configfile):
        if configfile is not None:
            if not os.path.isfile(configfile):
                raise FileNotFoundError("Config file {configfile} not found")
        else:
            configfile = "/etc/usbsdmux.config"

        config = configparser.ConfigParser()
        config.read(configfile)

        if "mqtt" not in config or "send" not in config:
            self.mqtt_enabled = False
            return

        mqtt_section = config["mqtt"]

        for argument in ("server", "port", "topic"):
            if argument not in mqtt_section:
                raise ValueError(f"Config value mqtt/{argument} not found. Please check {configfile}")

        self.mqtt_server = mqtt_section["server"]
        self.mqtt_port = int(mqtt_section["port"])
        self.mqtt_topic = mqtt_section["topic"]

        if "username" in mqtt_section and "password" in mqtt_section:
            self.mqtt_auth = {"username": mqtt_section["username"], "password": mqtt_section["password"]}
        else:
            self.mqtt_auth = None

        send_section = config["send"]

        self.send_on_host = send_section.get("host", False)
        self.send_on_dut = send_section.get("dut", False)


def _gather_data(ctl):
    data = {"card_info": ctl.get_card_info()}
    return data

def publish_info(ctl, config):
    """
    Publish info to mqtt server, if mqtt is enabled.
    This requires installing REQUIREMENTS.mqtt.txt.
    """
    try:
        import paho.mqtt.publish as mqtt
    except ImportError:
        print(
            "Sending data to an mqtt server requires paho-mqtt",
            "Please install REQUIREMENTS.mqtt.txt",
            sep="\n",
            file=sys.stderr,
        )
        exit(1)

    data = _gather_data(ctl)
    mqtt.single(
        config.mqtt_topic,
        payload=json.dumps(data),
        hostname=config.mqtt_server,
        port=config.mqtt_port,
        auth=config.mqtt_auth
    )
