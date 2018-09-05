#! /usr/bin/env python3

from .usbsdmux import UsbSdMux
import socket
import time
import argparse
import json
import os
import sys

"""
This service is intended as systemd-socket-activated unit and provides an
interface to the USB-SD-Mux without the need for root privileges.

The service uses a SOCK_SEQPACKET UNIX-socket for communication with the a
client. Packets always contain a JSON-encoded dict as payload.

From client to service:
The service expects the following parameter inside the payload:
* 'sg'   -- /dev/sg* - device to use to control the USB-SD-Mux
* 'mode' -- Mode to set the USB-SD-Mux to

For example:
{"sg": "/dev/sg1", "mode": "dut"}

From service to client:
The service always answers with a payload like the following:
* 'error' -- Boolean: True if an error occurred. False on success.
* 'text'  -- Text that describes the result.
             Contains the Text of an exception if one occurred.

For example:
{"error": False, "text": "Success"}
"""
# Default filedescriptor used by systemd to pass us a socket
systemd_socket_fd = 3

def create_answer(had_error=False, err_text=""):
    """
    Creates a JSON-formatted answer for socket-communication.

    Arguments:
    had_error -- Defines if the return value represents an error. Will be
                 written into the 'error'-field of the answer.
    err_text -- Free Text that will be passed to the client along with the
                error state.
    """
    answer = dict()
    answer["error"] = had_error
    answer["text"] =  err_text
    return json.dumps(answer)

def process_request(raw_string):
    """
    Parses a message received from the communication-socket and tries to execute
    the request.

    This function will try to parse the message as JSON and expects the
    following keys inside a dict:

    * 'sg'   -- /dev/sg* - device to use to control the USB-SD-Mux
    * 'mode' -- Mode to set the USB-SD-Mux to


    Arguments:
    raw_string -- Message recieved as string."""

    try:
        payload = json.loads(raw_string)
        ctl = UsbSdMux(payload["sg"])

        if payload["mode"].lower() == "off":
            ctl.mode_disconnect()

        elif payload["mode"].lower() == "dut" or\
             payload["mode"].lower() == "client":
            ctl.mode_DUT()

        elif payload["mode"].lower() == "host":
            ctl.mode_host()

        else:
            return create_answer(had_error=True, err_text="Unknown mode")

        return create_answer(had_error=False, err_text="Success")

    except Exception as e:
        return create_answer(had_error=True, err_text=str(e))

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-t",
        "--timeout",
        help="Time without connection before the service terminates in seconds.",
        default=120,
        type=int)
    parser.add_argument(
        "--socket",
        help="Will use given socket for standalone-mode instead of socket-activation with systemd.")

    args = parser.parse_args()

    if args.socket is not None:
        # try to create our own socket
        sock_name = args.socket
        try:
            os.remove(sock_name)
        except FileNotFoundError:
            pass
        except PermissionError as e:
            print(e, file=sys.stderr)
            print("Could not remove old socket. Correct access rights?", file=sys.stderr)
            exit(-1)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        sock.bind(sock_name)
        sock.listen(0)
    else:
        # get socket from systemd
        sock = socket.fromfd(
            systemd_socket_fd,
            socket.AF_UNIX,
            socket.SOCK_SEQPACKET)


    sock.settimeout(1)
    timeout = time.time() + args.timeout

    # connection loop
    while True:
        try:
            conn, addr = sock.accept()
            answer = process_request(conn.recv(4096).decode())
            conn.send(answer.encode())
            conn.close()
            timeout = time.time() + args.timeout
        except socket.timeout:
            pass

        if time.time() > timeout:
            break

    # we need to close the socket if the created it ourselves:
    if args.socket is not None:
        sock.close()
