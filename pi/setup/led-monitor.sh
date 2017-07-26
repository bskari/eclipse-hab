#!/bin/bash
# Uses the onboard LED to indicate errors

# Disable the disk activity trigger
trigger='/sys/class/leds/led0/trigger'
if [ -f "${trigger}" ] ;
then
	echo none | sudo tee "${trigger}"
fi

function process_grep {
	# If you run:
	#   python foo.py
	# then `pgrep foo.py` will return 1, because it only picks up 'python'
	# This function searches the whole process space.
	ps -ef | grep -v grep | grep -q $1
	return $?
}
# Just a check
process_grep $0
if [ $? -ne 0 ] ;
then
	echo 'Error'
	exit 1
fi

function good {
	status=0
	multiplier=1

	for process in shutdown-low-disk-space log_temperature record_video_and_stills ;
	do
		process_grep "${process}"
		result=$?
		status="$(expr ${status} + ${result} '*' ${multiplier})"
		multiplier="$(expr ${multiplier} '*' 2)"
	done

	return "${status}"
}

function set_led {
	led='/sys/class/leds/led0/brightness'
	if [ -f "${led}" ] ;
	then
		echo $1 | sudo tee "${led}"
	else
		echo "set_led $1"
	fi
}

set_led 0

now_seconds="$(date +%s)"
end_time="$(expr 600 + ${now_seconds})"

while [ "$(date +%s)" -lt "${end_time}" ] ;
do
	good
	status=$?

	echo $status
	if [ "${status}" -ne 0 ] ;
	then
		# Blink an error if set
		for i in $(seq 1 ${status}) ;
		do
			sleep 0.25
			set_led 1
			sleep 0.25
			set_led 0
		done
	else
		set_led 1
		sleep 1
		set_led 0
	fi

	sleep 5
done

# Reenable the disk activity trigger
if [ -f "${trigger}" ] ;
then
	echo mmc0 | sudo tee "${trigger}"
fi
