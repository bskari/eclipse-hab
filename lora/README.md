# LORA

## Pi receiver

Plug it in, along with a USB WiFi adapter. It will automatically connect to my
phone's hotspot. Plug in the antenna and point it at the balloon.

## Laptop

Run `ssh-agent fish` and `ssh-add ~/.ssh/id_ed25519` to unlock my SSH key.
Connect to my phone's hotspot. Run `ip addr` to find your IP address. It should
be listed under "wlp2s0" or something, and be something like "192.168.0.110".
Run `sudo nmap -sP <IP range>`, e.g. 192.168.0.100-120, to find other computer
IP addresses that are up. One of those should be the Pi. You can connect to it
by running `ssh pi@<IP>`, e.g. `ssh pi@192.168.0.104`. Because you unlocked the
SSH key, it should automatically log in. Run `exit` to log out. Otherwise, the
password is the same as this laptop's.

(TODO) Now you can run this script and it will automatically show images from
the Pi. Neat!

## Shutdown

The Pis can corrupt the filesystem if you just unplug them, that's why Dan
added handy shutdown buttons. You'll need something long, thin, and stiff to
press the button; the RS41 antenna works okay if you don't have anything else.
Press the button once on the Pi in the Sky to kill the PitS program (the yellow
LED indicating GPS lock should shut off). Press it again to shut down the Pi.
The Pi's green LED on the side near the USB port will blink .25s/.25s for about
5 seconds, then on ~2s, then turn off, indicating that the Pi has shut down.
