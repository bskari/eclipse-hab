#!/bin/bash
# Prepares a fresh installation of an SD card for the 2017 Eclipse HAB. This
# should be safe to run multiple times.

# First, download Raspbian Lite and burn it to an SD card.
# Install git and clone the repo:
#   (root password is raspberry)
#   apt-get update
#   apt-get install git
#   git clone https://github.com/bskari/eclipse-2017-hab
# Run this file!

set -u
set -e

if [ "${USER}" != 'root' ];
then
    echo 'You must be root'
    exit 1
fi

apt-get update -y
if [ ! -f 'raspi-config_20160527_all.deb' ];
then
    wget http://archive.raspberrypi.org/debian/pool/main/r/raspi-config/raspi-config_20170705_all.deb
    dpkg -i raspi-config_20170705_all.deb
fi
echo 'Get ready to expand the root FS and enable the camera (press enter)'
read
raspi-config  # Expand the root FS, enable the camera

echo -n 'Want to update the firmware? (y/n) '
read firmware
if [ "${firmware}" == 'y' ];
then
    apt-get install curl  # Curl is needed for the rpi-update script
    apt-get install binutils # readelf is needed for the rpi-update script
    curl https://raw.githubusercontent.com/Hexxeh/rpi-update/master/rpi-update > /usr/bin/rpi-update
    chmod +x /usr/bin/rpi-update
    rpi-update
    reboot
    exit 0
fi

echo 'Cloning Eclipse 2017 HAB repo'
pushd ~pi
    if [ -e eclipse-2017-hab ];
    then
        pushd eclipse-2017-hab
            git pull
        popd
    else
        git clone git@github.com:eclipse-2017-hab
    fi
popd

apt-get upgrade

apt-get install -y $(cat apt-requirements.txt)

# Hell with bash, let's do the rest of this in Python
tmux new -d -s hab-setup
tmux send-keys -t hab-setup 'python3 setup.py' c-m
tmux attach -t hab-setup
