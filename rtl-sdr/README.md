SDR instructions
================

Installation
------------

TODO

Running
-------

After you've plugged in an SDR, run

    python set_squelch.py

to find and set the squelch level. Then run

    ./play-aprs.sh

to listen to the APRS stream through the speakers of the computer. If you're
picking up the TrackSoar from your RTL-SDR, you should be able to hear it.

To try to decode the APRS messages, run

    ./decode-aprs.sh

Note that I haven't gotten this to work yet.
