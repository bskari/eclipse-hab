"""Does the rest of the setup."""
from __future__ import print_function

import os
import re
import subprocess
import sys


def main():
    """Does the rest of the setup."""

    def newer(file_name_1, file_name_2):
        """Returns true if file_1 is newer than file_2."""
        return os.stat(file_name_1).st_atime > os.stat(file_name_2).st_mtime


    def exists(file_name):
        """Returns true if file exists."""
        return os.access(file_name, os.F_OK)

    def grep(file_name, pattern):
        """Searches a file for a regex pattern."""
        regex = re.compile(pattern)
        with open(file_name) as file_:
            for line in file_:
                if regex.search(line):
                    return True
        return False


    section_test_command_tuples = (
        (
            'start up',
            (
                not exists('/etc/init.d/eclipse-2017-hab-rc')
                or newer('eclipse-2017-hab-rc', '/etc/init.d/eclipse-2017-hab-rc')
            ),
            (
                'sudo cp eclipse-2017-hab-rc /etc/init.d/',
                'sudo chmod +x /etc/init.d/eclipse-2017-hab-rc',
                'sudo update-rc.d eclipse-2017-hab-rc defaults',
            )
        ),
        (
            'virtualenv',
            not exists('/home/pi/.virtualenvs/eclipse-2017-hab'),
            (
                'bash setup-virtualenv.sh',
            )
        ),
        (
            'SSH banner',
            not exists('/etc/banner'),
            (
                'sudo cp banner /etc',
                'sudo bash add-banner-to-sshd.sh',
            )
        ),
        (
            'network interfaces',
            (
                not exists('/etc/network/interfaces')
                or newer('interfaces', '/etc/network/interfaces')
            ),
            (
                'sudo cp interfaces /etc/network/interfaces',
            )
        ),
        (
            'disable HDMI',
            not grep('/etc/rc.local', 'tvservice'),
            (
                ('sudo', 'sed', '-i', 's/^exit 0$/\/usr\/bin\/tvservice -o\nexit 0/', '/etc/rc.local'),
            )
        ),
        (
            'disable Bluetooth',
            not grep('/boot/config.txt', 'pi3-disable-bt'),
            (
                'sudo bash append.sh /boot/config.txt dtoverlay=pi3-disable-bt',
            )
        ),
        (
            'disable WiFi',
            not grep('/boot/config.txt', 'pi3-disable-wifi'),
            (
                'sudo bash append.sh /boot/config.txt dtoverlay=pi3-disable-wifi',
            )
        ),
    )

    for section, test, commands in section_test_command_tuples:
        if test:
            print('+++ Running section {section}'.format(section=section))
            for command in commands:
                print(command)
                if isinstance(command, str):
                    return_code = subprocess.call(command.split(' '))
                else:
                    # Already split
                    return_code = subprocess.call(command)

                if return_code != 0:
                    print(
                        'Command failed with code {code}, aborting'.format(
                            code=return_code
                        )
                    )
                    sys.exit(return_code)
        else:
            print('Skipping section {section}'.format(section=section))


if __name__ == '__main__':
    main()
