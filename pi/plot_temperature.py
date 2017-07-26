import datetime
import matplotlib.pyplot as pyplot
import os
import re
import sys


def main():
    """Main."""
    if sys.version_info.major <= 2:
        print('Use Python 3')
        return

    lines = []
    for file_name in sorted(os.listdir('.{}temperatures'.format(os.sep))):
        if file_name.endswith('csv'):
            # Do a line at a time because some lines might be corrupted due to
            # power loss
            file_name = '.{sep}temperatures{sep}{f}'.format(sep=os.sep, f=file_name)
            with open(file_name) as file_:
                for line in file_.readlines():
                    if line.startswith('"') and line.endswith('\n'):
                        lines.append(line)

    def parse_time(line):
        """Returns the time from a line."""
        time_str = line.split(',')[0].replace('"', '')
        parts = [int(i) for i in re.split('[: -]', time_str)]
        return datetime.datetime(*parts)

    def parse_temperature(line):
        """Returns the temperature from a line."""
        return float(line.split(',')[1][:-1])

    initial_time = parse_time(lines[0])

    seconds = [(parse_time(line) - initial_time).total_seconds() for line in lines]
    temperatures = [parse_temperature(line) for line in lines]
    hours = [sec / 3600. for sec in seconds]

    pyplot.plot(hours, temperatures)
    pyplot.xlabel('time (hours)')
    pyplot.ylabel('temperature (degrees C)')
    pyplot.grid(True)
    pyplot.show()


if __name__ == '__main__':
    main()
