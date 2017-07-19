"""Does the rest of the setup."""
from __future__ import print_function

import os
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

    section_test_command_tuples = (
        (
            'start up',
            (
                not exists('/etc/init.d/eclipse-2017-hab-rc')
                or newer('eclipse-2017-hab-rc', '/etc/init.d/eclipse-2017-hab-rc')
            ),
            (
                'cp eclipse-2017-hab-rc /etc/init.d/',
                'update-rc.d eclipse-2017-hab-rc defaults',
            )
        ),
        (
            'virtualenv',
            not exists('/home/pi/.virtualenvs/eclipse-2017-hab'),
            (
                'bash setup-virtualenv.sh',
            )
        ),
    )

    for section, test, commands in section_test_command_tuples:
        if test:
            print('+++ Running section {section}'.format(section=section))
            for command in commands:
                print(command)
                return_code = subprocess.call(command.split(' '))
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
