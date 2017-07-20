"""Logs the internal temperature."""
from __future__ import print_function

import datetime
import os
import sys
import time


def log_temperature(delay_seconds=None, swap_file_seconds=None):
    """Logs the internal temperature."""
    temperature_path = 'temperatures'
    if not os.path.isdir(temperature_path):
        os.mkdir(temperature_path)

    if delay_seconds is None:
        delay_seconds = 10
    elif delay_seconds < 1:
        raise ValueError('Invalid delay_seconds ')

    if swap_file_seconds is None:
        swap_file_seconds = 60 * 5
    elif swap_file_seconds < 60:
        raise ValueError('Invalid swap_file_seconds')

    while True:
        seconds = 0
        temperature_file_name = temperature_path + os.sep + datetime.datetime.strftime(
            datetime.datetime.now(),
            '%Y-%m-%d_%H:%M:%S.csv'
        )
        with open(temperature_file_name, 'w') as temperature_file:
            while seconds < swap_file_seconds:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as thermal_zone_file:
                    temperature_c = float(thermal_zone_file.read()) * 1e-3

                time_stamp = datetime.datetime.strftime(
                    datetime.datetime.now(),
                    '%Y-%m-%d %H:%M:%S'
                )
                temperature_file.write('"{}",{}\n'.format(time_stamp, temperature_c))
                temperature_file.flush()
                time.sleep(delay_seconds)
                seconds += delay_seconds


if __name__ == '__main__':
    if len(sys.argv) > 2:
        log_temperature(int(sys.argv[0]), int(sys.argv[1]))
    elif len(sys.argv) > 1:
        log_temperature(int(sys.argv[0]))
    else:
        log_temperature()
