#!/bin/bash
set -u
set -e

if [ "${USER}" != 'root' ] ;
then
	echo 'Please run as root, e.g.'
	echo "sudo bash $0"
	exit 0
fi

set +e
blacklisted=0
for i in dvb_usb_rtl28xxu rtl_2832 rtl_2830 ;
do
	grep -q "${i}" /etc/modprobe.d/*
	if [ $? -eq 1 ] ;
	then
		echo "Blacklisting driver ${i}"
		echo "blacklist ${i}" >> /etc/modprobe.d/blacklist.conf
		blacklisted=1
	fi
done
set -e
if [ "${blacklisted}" -eq 1 ] ;
then
	echo 'You need to reboot to make this blacklist take effect'
	exit 1
fi


temp_dir="$(mktemp -d)"
cd "${temp_dir}"

echo 'Installing rtl-sdr'
apt install git build-essential cmake libusb-1.0-0-dev
git clone git://git.osmocom.org/rtl-sdr.git
cd rtl-sdr
mkdir build
cd build
cmake .. -DINSTALL_UDEV_RULES=ON
make
make install
ldconfig

echo 'Installing sox'
apt install sox

echo 'Installing Kalibrate'
cd "${temp_dir}"
apt install libtool autoconf automake libfftw3-dev
git clone https://github.com/asdil12/kalibrate-rtl.git
cd kalibrate-rtl
if [ "$(uname -m)" == 'armv7l'] ;
then
	git checkout arm_memory
elif [ "$(uname -m)" == 'x86_64' -o "$(uname -m)" == 'x86' -o "$(uname -m)" == 'x86_32' ];
then
	echo '' # Nothing to do, this is fine
else
	echo "********** Unknown uname -m version! $(uname -m)"
fi
./bootstrap
./configure
make
make install

echo 'Installing Multimon-NG decoder'
cd "${temp_dir}"
apt install qt4-qmake libpulse-dev libx11-dev
git clone https://github.com/EliasOenal/multimonNG.git
cd multimonNG
mkdir build
cd build
qmake ../multimon-ng.pro
make
sudo make install
