#!/bin/bash
# Startup script

tmux new -d -s eclipse-2017-hab
tmux send-keys -t eclipse-2017-hab 'cd ~pi/eclipse-2017-hab/pi' c-m
tmux send-keys -t eclipse-2017-hab 'export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3' c-m
tmux send-keys -t eclipse-2017-hab 'source /usr/local/bin/virtualenvwrapper.sh' c-m
tmux send-keys -t eclipse-2017-hab 'workon eclipse-2017-hab' c-m
tmux send-keys -t eclipse-2017-hab 'python record_video_and_stills.py' c-m
