#!/bin/python
"""Sets the squelch level."""
import subprocess
import threading
import time
import io


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
    if isinstance(devnull, io.IOBase):
        devnull.close()
    return bytes_count


def find_squelch_level() -> int:
    """Finds the squelch level."""

    def squelched(limit: int) -> bool:
        """Returns true if it was squelched."""
        print(f"Trying {limit}")
        bytes_count = bytes_at_squelch_level(upper_limit)
        print(f'Squelch level {limit} produced {bytes_count} bytes')
        if bytes_count < 10000:
            return True
        return False

    # Binary search up!
    lower_limit = 10
    upper_limit = 20
    for i in range(15):
        if squelched(upper_limit):
            break
        time.sleep(1)
        lower_limit = upper_limit
        upper_limit = int(upper_limit * 1.5)

    while lower_limit + 1 <= upper_limit:
        mid = (lower_limit + upper_limit) // 2
        if squelched(mid):
            upper_limit = mid
        else:
            lower_limit = mid + 1

    return mid


def main():
    """Main."""
    level = find_squelch_level() + 10
    print('Setting squelch level to {}'.format(level))
    with open('squelch-level.txt', 'w') as file_:
        file_.write('{}'.format(level))


if __name__ == '__main__':
        main()
