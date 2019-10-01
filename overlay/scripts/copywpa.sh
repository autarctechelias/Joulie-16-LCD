#!/bin/bash
mv /boot/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant-wlan0.conf && chmod 600 /etc/wpa_supplicant/wpa_supplicant-wlan0.conf || echo "no file found"
#sleep 0.1
exit 0
