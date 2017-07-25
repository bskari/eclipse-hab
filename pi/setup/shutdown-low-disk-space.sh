#!/bin/bash

while :;  # Loop forever
do
	free_mibibytes="$(df --output=avail --block-size=M / | grep -P '\d+' | sed 's/M//')"
	echo "$(date) ${free_mibibytes} free MiB"
	if [ "${free_mibibytes}" -lt 100 ] ;
	then
		echo 'Shutting down'
		echo "$(date +'%Y-%m-%d_%H:%M:%S')" > shutdown-time.txt
		sudo shutdown -h -t 15 +1
	fi

	sleep 60
done
