#!/bin/bash
# Startup script

base_dir=''
virtualenvwrapper=''


function main() {
	set_globals

	tmux new -d -s eclipse-2017-hab

	# Launch the video and image recording
	tmux send-keys -t eclipse-2017-hab "cd ${base_dir}/pi" c-m
	tmux send-keys -t eclipse-2017-hab "source ${virtualenvwrapper}" c-m
	tmux send-keys -t eclipse-2017-hab 'workon eclipse-2017-hab' c-m
	tmux send-keys -t eclipse-2017-hab 'python record_video_and_stills.py' c-m
	# record_videos_and_stills.py monitors for low disk space, so when it exits,
	# it's time to shut down
	tmux send-keys -t eclipse-2017-hab 'bash setup/shutdown.sh' c-m
	wait_for_process 'record_video_and_stills.py'

	# Launch the temperature recording
	tmux new-window -t eclipse-2017-hab
	tmux send-keys -t eclipse-2017-hab "cd ${base_dir}/pi" c-m
	tmux send-keys -t eclipse-2017-hab "source ${virtualenvwrapper}" c-m
	tmux send-keys -t eclipse-2017-hab 'workon eclipse-2017-hab' c-m
	tmux send-keys -t eclipse-2017-hab 'python log_temperature.py' c-m
	wait_for_process 'log_temperature.py'

	# Launch the serial dumper
	tmux new-window -t eclipse-2017-hab
	tmux send-keys -t eclipse-2017-hab "cd ${base_dir}/pi" c-m
	tmux send-keys -t eclipse-2017-hab "source ${virtualenvwrapper}" c-m
	tmux send-keys -t eclipse-2017-hab 'workon eclipse-2017-hab' c-m
	tmux send-keys -t eclipse-2017-hab 'python dump_serial.py' c-m
	wait_for_process 'dump_serial.py'

	# Launch the watchdog that blinks the LED to indicate status. This needs to be
	# done last, because it checks for all of the above processes.
	tmux new-window -t eclipse-2017-hab
	tmux send-keys -t eclipse-2017-hab "cd ${base_dir}/pi" c-m
	tmux send-keys -t eclipse-2017-hab 'bash setup/led-monitor.sh' c-m
}


function wait_for_process() {
	local process="$1"
	for i in $(seq 60); do
		sleep 1
		ps -ef | grep -v grep | grep -q "${process}"
		if [ "$?" -eq 0 ];
		then
			break
		fi
	done
	echo "Waited for ${i} seconds for ${process} to start"
}


function set_globals() {
	function abort_if_not_set() {
		if [ -z "${!1}" ] ;
		then
			echo "$1 not set"
			exit 1
		fi
	}

	for i in \
		"${HOME}/eclipse-2017-hab" \
		"${HOME}/Documents/eclipse-2017-hab" \
	; do
		if [ -d "${i}" ] ;
		then
			base_dir="${i}"
		fi
	done
	abort_if_not_set 'base_dir'

	for i in \
		/usr/local/bin/virtualenvwrapper.sh \
		/usr/share/virtualenvwrapper/virtualenvwrapper.sh \
	; do
		if [ -f "${i}" ] ;
		then
			virtualenvwrapper="${i}"
		fi
	done
	abort_if_not_set 'virtualenvwrapper'
}


main
