#!/bin/python
"""Sets the squelch level."""
import subprocess
import threading
import time


def bytes_at_squelch_level(squelch_level):
    """Returns the number of bytes received at a squelch level."""
    # Python 3
    if hasattr(subprocess, 'DEVNULL'):
        devnull = subprocess.DEVNULL
    else:
        # Python 2 :(
        devnull = open('/dev/null', 'w')

    p1 = subprocess.Popen(
        (
            'rtl_fm',
            '-f',
            '144.390M',
            '-s',
            '22050',
            '-l',
            str(squelch_level),
            '-'
        ),
        stdout=subprocess.PIPE,
        stderr=devnull
    )
    p2 = subprocess.Popen(('wc', '-c'), stdin=p1.stdout, stdout=subprocess.PIPE)

    def sleep_then_kill_p1():
        time.sleep(2.0)
        p1.kill()
    threading.Thread(target=sleep_then_kill_p1).start()

    bytes_count = int(p2.communicate()[0])
    if isinstance(devnull, file):
        devnull.close()
    return bytes_count


def find_squelch_level():
    """Finds the squelch level."""

    # Binary search up!
    upper_limit = 20
    for i in range(10):
        print('Trying {}'.format(upper_limit))
        bytes_count = bytes_at_squelch_level(upper_limit)
        print('Squelch level {} produced {} bytes'.format(upper_limit, bytes_count))
        if bytes_count < 10000:
            break
        time.sleep(1)
        upper_limit = int(upper_limit * 1.5)

    return upper_limit


def main():
    """Main."""
    level = find_squelch_level()
    print('Setting squelch level to {}'.format(level))
    with open('squelch-level.txt', 'w') as file_:
        file_.write('{}'.format(level))


if __name__ == '__main__':
        main()
