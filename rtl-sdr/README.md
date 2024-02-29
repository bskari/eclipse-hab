SDR instructions
================

Installation
------------

Need to install `rtl_fm` and `direwolf`.

    sudo apt install rtl_fm direwolf

Running
-------

Run

    python monitor-aprs.py

And it will start a nice interface showing recently received packets from the
weather balloon. The upper left has a clock, top is a line for error or warning
messages, left is the most recent status received from the balloon, right is
the most recent received status for each station we've recently heard, and
bottom is each raw message as it is received.

Run

    ./play-aprs.sh

to listen to the APRS stream through the speakers of the computer. If you're
picking up the TrackSoar from your RTL-SDR, you should be able to hear it.

To try to decode the APRS messages from the Tracksoar, run

    ./decode-aprs-tracksoar.sh

And for the RS41 radiosonde:

    ./decode-aprs-rs41.sh

Or you can just choose your frequency yourself:

    ./decode-aprs.sh 144.390M
