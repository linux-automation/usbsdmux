#!/bin/bash

set -ex

self="$(realpath "${0}")" && selfdir="$(dirname "${self}")"

cd "${selfdir}"

for json in *.json; do
    text="$(basename -s .json "${json}").text"
    ../../usbsdmux/sd_regs.py --json "${json}" > "${json}.tmp"
    ../../usbsdmux/sd_regs.py "${json}.tmp" > "${text}.tmp"
    mv "${json}.tmp" "${json}"
    mv "${text}.tmp" "${text}"
done
