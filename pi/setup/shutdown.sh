#!/bin/bash
# Shuts down cleanly.
uptime_seconds="$(cut -d '.' -f 1 /proc/uptime)"
if [ "${uptime_seconds}" -lt 300 ] ;
then
	sudo shutdown -h +5
else
	sudo shutdown -h +1
fi
