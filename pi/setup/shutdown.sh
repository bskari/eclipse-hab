#!/bin/bash
# Shuts down cleanly.
uptime_seconds="$(cut -d '.' -f 1 /proc/uptime)"
if [ "${uptime_seconds}" -lt 300 ] ;
then
	# Sleep, because shutdown blocks new logins from SSH within 5 minutes of
	# shutdown, which is annoying
	sleep 240
fi
sudo shutdown -h +1
