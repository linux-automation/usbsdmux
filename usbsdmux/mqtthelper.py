import configparser
import json
import os
import sys


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
        else:
            self.mqtt_enabled = True

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


def _read_file(filename):
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None


def _read_int(filename, base=10):
    try:
        return int(_read_file(filename).strip(), base)
    except TypeError:
        return None


def _gather_data(ctl, sg, mode):
    import socket

    import pkg_resources

    base_sg = os.path.realpath(sg)
    sg_name = os.path.basename(base_sg)

    # only file in this directory is a hard link pointing to the block device
    sd_name = os.listdir(f"/sys/class/scsi_generic/{sg_name}/device/block/")[0]

    # using that name we can obtain further information
    stat_data = [int(part) for part in _read_file(f"/sys/class/block/{sd_name}/stat").split()]

    # https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-block
    stat_names = (
        "reads_completed_successfully",
        "reads_merged",
        "sectors_read",
        "time_spent_reading",
        "writes_completed",
        "writes_merged",
        "sectors_written",
        "time_spent_writing",
        "IOs_currently_in_progress",
        "time_spent_doing_IOs",
        "weighted_time_spent_doing_IOs",
        "discards_completed",
        "discards_merged",
        "sectors_discarded",
        "time_spent_discarding",
        "flush_requests_completed",
        "time_spent_flushing",
    )

    stat = dict(zip(stat_names, stat_data))

    usb_path = os.path.realpath(f"/sys/class/scsi_generic/{sg_name}")

    max_depth = 10
    while not os.path.isfile(os.path.join(usb_path, "serial")) and max_depth > 0:
        usb_path = os.path.dirname(usb_path)
        max_depth -= 1

    card_info = ctl.get_card_info() if ctl.get_mode() == "host" or mode == "dut" else None

    data = {
        "command": " ".join(sys.argv),
        "mode": mode,
        "sg": sg_name,
        "sd": sd_name,
        "usb": usb_path,
        "username": os.getlogin(),
        "hostname": socket.gethostname(),
        "labgrid-place": os.environ.get("LG_PLACE"),
        "model": type(ctl).__name__,
        "serial": _read_file(os.path.join(usb_path, "serial")).strip(),
        "version": pkg_resources.get_distribution("usbsdmux").version,
        "diskseq": _read_int(f"/sys/class/block/{sd_name}/diskseq"),
        "size": _read_int(f"/sys/class/block/{sd_name}/size"),
        "ioerr_cnt": _read_int(f"/sys/class/scsi_generic/{sg_name}/device/ioerr_cnt", 16),
        "stat": stat,
        "card_info": card_info,
    }

    return data


def publish_info(ctl, config, sg, mode):
    """
    Publish info to mqtt server, if mqtt is enabled.
    This requires installing REQUIREMENTS.mqtt.txt.
    """

    if not config.mqtt_enabled:
        return

    if (mode == "client" and not config.send_on_dut) or (mode == "host" and not config.send_on_host):
        return

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

    data = _gather_data(ctl, sg, mode)
    mqtt.single(
        config.mqtt_topic,
        payload=json.dumps(data),
        hostname=config.mqtt_server,
        port=config.mqtt_port,
        auth=config.mqtt_auth,
    )
