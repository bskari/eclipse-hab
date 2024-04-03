# LORA

## Pi receiver

Plug it in, along with a USB WiFi adapter. It will automatically connect to my
phone's hotspot. Plug in the antenna and point it at the balloon.

## Laptop

### Fancy monitoring script

Run `python monitor_lora_pi.py` to have a fancy monitor. This will also
periodically save the coordinates to a Google Earth file. Just open Google
Earth and it will continually reload the coordinate file as it is updated.

### Manual monitoring

Connect to the phone's hotspot. Run `ip addr` to find the computer's IP
address. Run `sudo nmap -sP <IP with last octet range>` to find the Pu's IP
address. For example, if your IP is 192.168.0.120, run `sudo nmap
192.168.0.100-150`. One of those should be the Pi.

Run `ssh-copy-id -i ~/.ssh/id_dsa_eclipse_pi.pub pi@<Pi IP>` to set up auto
login. It might say it's already done, that's fine.

Now you should be able to log into the Pi by running `ssh pi@<Pi IP>`. If not,
the password is "eclipse".

Run `tmux attach -t lora` to see the monitoring program. It looks like it won't
refresh after being resized, so you might need to kill it and restart.

Alternatively, you can just run `nc <Pi IP> 6004` from the laptop to view the
raw messages.

### Photos

The Pi should receive photos about once a minute. After you've set up auto
login, run `sh rsync.sh` to copy the files to this laptop. The script is smart
and will only copy over new files. They'll be stored in the ssdv folder. The
full path is /home/bs/Documents/eclipse-hab/lora/ssdv . `gwenview` is a nice
image viewer. I would just run this script once in a while.

## Shutdown

The Pis can corrupt the filesystem if you just unplug them, that's why Dan
added handy shutdown buttons. You'll need something long, thin, and stiff to
press the button; the RS41 antenna works okay if you don't have anything else.
Press the button once on the Pi in the Sky to kill the PitS program (the yellow
LED indicating GPS lock should shut off). Press it again to shut down the Pi.
The Pi's green LED on the side near the USB port will blink .25s/.25s for about
5 seconds, then on ~2s, then turn off, indicating that the Pi has shut down.
