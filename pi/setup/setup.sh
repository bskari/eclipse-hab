#!/bin/bash
# Prepares a fresh installation of an SD card for the 2017 Eclipse HAB. This
# should be safe to run multiple times.

# First, download Raspbian Lite and burn it to an SD card.
#   wget https://raspbian-lite.somehwere
#   sudo burn.sh raspbian.tar.gz /dev/mmcblk0
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

raspi_config_file="$(wget http://archive.raspberrypi.org/debian/pool/main/r/raspi-config/ -O - | grep -o '>raspi-config.*deb<' | grep -o 'raspi-config.*deb' | sort -n | tail -n 1)"
if [ -z "${raspi_config_file}" ] ;
then
    echo 'Unable to find latest version of raspi-config, skipping'
else
    if [ ! -f "${raspi_config_file}" ] ;
    then
        wget "http://archive.raspberrypi.org/debian/pool/main/r/raspi-config/${raspi_config_file}"
        dpkg -i "${raspi_config_file}"
    fi
    echo 'Get ready to expand the root FS, change keyboard/locale/WiFi to US, enable SSH, and enable the camera (press enter)'
    read
    raspi-config  # Expand the root FS, enable the camera
fi

echo -n 'Want to update the firmware? (y/n) '
read firmware
if [ "${firmware}" == 'y' ];
then
    apt-get update
    apt-get install -y curl  # Curl is needed for the rpi-update script
    apt-get install -y binutils # readelf is needed for the rpi-update script
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

apt-get update
apt-get -y upgrade

apt-get install -y $(cat apt-requirements.txt)

# Hell with bash, let's do the rest of this in Python
tmux new -d -s hab-setup
tmux send-keys -t hab-setup 'python3 setup.py' c-m
tmux attach -t hab-setup
