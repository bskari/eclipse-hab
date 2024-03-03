SDR instructions
================

Installation
------------

Need to install `rtl_fm` and `direwolf`.

    sudo apt install rtl_fm direwolf

Download the aprslib:

    curl -L -O https://github.com/rossengeorgiev/aprs-python/archive/refs/heads/master.zip
    unzip master.zip
    rm master.zip
    mv aprs-python-master/aprslib/ .
    rm -rf aprs-python-master

Running
-------

### Python monitor

Run

    python monitor_aprs.py

And it will start a nice interface showing recently received packets from the
weather balloon. The upper left has a clock, top is a line for error or warning
messages, left is the most recent status received from the balloon, right is
the most recent received status for each station we've recently heard, and
bottom is each raw message as it is received.

You can also specify your call sign:

    --call-sign KE0FZV

and your position:

    --launch-site 40.0000,-105.0000

If you don't provide a launch site, the first packet it hears from your call
sign will be assumed as the launch site.

### Google Earth monitor

Once you're running the Python monitor, you can have Google Earth display the data and update it
periodically. Run the Python monitor as above, then in Google Earth, click File -> Add Network Link.
Name it "Balloon" and in Link, enter "http://localhost:8080". In the Refresh tab, change "Time-Based
Refresh" to "Periodically" and "30 secs". Enable "Fly to View on Refresh" if you want. It should
show up in "My Places" under "Balloon". Expand it and enable my call sign.

### Direwolf monitor

To listen to the APRS stream through the speakers of the computer, run

    ./play-aprs.sh

If you're picking up the TrackSoar from your RTL-SDR, you should be able to
hear it.

To try to decode the APRS messages from the Tracksoar, run

    ./decode-aprs-tracksoar.sh

And for the RS41 radiosonde:

    ./decode-aprs-rs41.sh

Or you can just choose your frequency yourself:

    ./decode-aprs.sh 144.390M
