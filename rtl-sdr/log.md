# Description

We have two trackers, operating on different frequencies. I would like to have
a program switch between monitoring them, and have a display of recent messages
received, time since last received, some manual way to switch between the 2
frequencies, and some parsing of the messages. I was thinking a Python script
that starts the radio monitor, reads the stdout, waits for a message to be
decoded. All while live updating every second or so? Maybe just a curses
interface.

I've programmed the trackers to broadcast every 4 minutes and 10 seconds, but
because of reasons, they're not staggered evenly. One might broadcast, then the
other 30 seconds later, then the original 3:40 later.

It would be nice to switch to the other frequency if we don't hear from one
tracker after 4:30 or so of when it's expected. Maybe we missed it, or there
was interference. Also, lots of other people will be broadcasting on 144.390
MHz, because it's the default APRS frequency in North America, so if we could
stay on there as much as possible to parse other people's positions for fun,
that would be neat.

I would love if it could interpolate and show projected position updates
every second or so for my balloon. I don't know if we can hook this up to
Google Earth, but that would be neat. Oh, should at least log all messages
received, even if they're from other people. Would love to see:

    - time since launch
    - ascent rate in mph and m/s
    - bearing in degrees
    - speed in mph and m/s
    - altitude in feet and meters
    - don't know how feasible this is, but if we could predict a landing site...
    - recent raw packets with timestamps, even if they're not from us

The 2 frequencies are 432.560M and 144.390M.

## Parsing

Here's the program I run to listen for packets:

    $ rtl_fm -f 432.560M -p 0 - | direwolf -c sdr.conf -r 24000 -D 1 -t 0 -l . -

And sample output:

    Found 1 device(s):
    Dire Wolf version 1.6
    Includes optional support for:  gpsd hamlib cm108-ptt

    Reading config file sdr.conf
    Audio input device for receive: stdin  (channel 0)
    Audio out device for transmit: null  (channel 0)
    Channel 0: 1200 baud, AFSK 1200 & 2200 Hz, E+, 24000 sample rate.
    Note: PTT not configured for channel 0. (Ignore this if using VOX.)
    Ready to accept AGW client application 0 on port 8000 ...
    Ready to accept KISS TCP client application 0 on port 8001 ...
      0:  Realtek, RTL2838UHIDIR, SN: 00000001

    Using device 0: Generic RTL2832U OEM
    Found Rafael Micro R820T tuner
    Tuner gain set to automatic.
    Tuned to 432812000 Hz.
    Oversampling input by: 42x.
    Oversampling output by: 1x.
    Buffer size: 8.13ms
    Exact sample rate is: 1008000.009613 Hz
    Allocating 15 zero-copy buffers
    Sampling at 1008000 S/s.
    Output at 24000 Hz.

    KE0FZV-11 audio level = 67(15/14)   [NONE]   ___|||___
    [0.4] KE0FZV-11>APZ41N:!3959.88N/10513.70WO293/000/A=005316/S8T29V2455C00
    Position, Original Balloon (think Ham b, Experimental
    N 39 59.8800, W 105 13.7000, 0 MPH, course 293, alt 5316 ft
    /S8T29V2455C00
    Opening log file "2024-02-07.log".

    KE0FZV-11 audio level = 51(15/14)   [NONE]   ___|||___
    [0.4] KE0FZV-11>APZ41N:!3959.88N/10513.70WO293/000/A=005316/S8T28V2458C00
    Position, Original Balloon (think Ham b, Experimental
    N 39 59.8800, W 105 13.7000, 0 MPH, course 293, alt 5316 ft
    /S8T28V2458C00

    KE0FZV-11 audio level = 44(15/14)   [NONE]   ||||||___
    [0.2] KE0FZV-11>APZ41N:!3959.88N/10513.71WO302/001/A=005326/S6T28V2458C00
    Position, Original Balloon (think Ham b, Experimental
    N 39 59.8800, W 105 13.7100, 1 MPH, course 302, alt 5326 ft
    /S6T28V2458C00

    KE0FZV-11 audio level = 42(14/15)   [NONE]   ||||||___
    [0.2] KE0FZV-11>APZ41N:!3959.88N/10513.71WO302/001/A=005326/S6T28V2455C00
    Position, Original Balloon (think Ham b, Experimental
    N 39 59.8800, W 105 13.7100, 1 MPH, course 302, alt 5326 ft
    /S6T28V2455C00

## APRS format

Example APRS packet from above:

    KE0FZV-11>APZ41N:!3959.88N/10513.70WO293/000/A=005316/S8T29V2455C00

And explanations for each part:

    KE0FZV

KE0FZV is my ham radio callsign

    11

This beacon's SSID, it's just a number so one person can have multiple active beacons, 11 usually means balloon

    APZ41N

For APRS messages going to a specific user, this would be the recipient's
callsign. Because we're broadcasting our position to anyone who's listening,
this is the software identifier that created this packet. "AP" means it's
software and not a specific user, "Z" means it's experimental, "41N" is the
software identifier for RS41ng.

    !

The symbol table. This combined with "O" later indicates to mapping software
that a balloon icon should be shown on the map.

    3959.88N/10513.70W

Latitude and longitude in degrees, minutes, and decimal minutes.

    O

The symbol. O for balloon.

    293/000

Bearing in degrees clockwise from north, and speed in knots

    A=005316

Altitude in feet

    S8T29V2455C00

Comment field. Software can add whatever they want here.
For rs41ng,
S=satellites in view
T=internal temperature in degrees Celsius
V=battery voltage in millivolts
C=climb rate in meters / second
rs41ng by default includes the packet number (P12) too, but I removed that.
For my Trackuino tracker, the comment is just "Trackuino".
