Raspberry Pi Eclipse HAB
========================

This has setup for the Raspberry Pi for the high altitude balloon.

First, download Raspbian OS Lite (32-bit for Pi Zero). Find the right partition
by running
`sudo fdisk -l`
Then burn the image by 
`sudo bash burn.sh raspbian.tar.xz /dev/mmcblk0`

For headless setup, you need to do a few things.  SSH can be enabled by placing
a file named "ssh" onto the boot partition. The Pi will delete this file each
time it boots. You'll also need to create a file named "userconf.txt" in the
boot directory in the boot directory. It should have
"username:encryptedpassword". You can generate the encrypted password by
running `openssl passwd -6`. Also create a file named "wpa\_supplicant.conf"
with
```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
  ssid="NETWORK-NAME"
  psk="NETWORK-PASSWORD"
}
```
