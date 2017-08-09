import sys

import sup800f


class ReadWrapper(object):
    def __init__(self, file_name):
        self._file = open(file_name, 'rb')

    def read(self, count=None):
        """Reads some bytes."""
        if count is None:
            count = 1
        read_bytes = self._file.read(count)
        if len(read_bytes) == 0:
            self._file.close()
            raise EOFError('Nothing more to read')

        return read_bytes


def main(serial_file_name, gui=True):
    """Main."""
    if sys.version_info.major <= 2:
        print('Use Python 3')
        return

    data = []
    serial_file = ReadWrapper(serial_file_name)
    count = 0
    while True:
        try:
            message_bytes = sup800f.get_message(serial_file)
        except EOFError:
            break
        count += 1
        if count % 100 == 0:
            count = 0
            print(message_bytes)
        # The SUP800F dumps some other type of message that's 66 bytes long.
        # We only care about the binary stuff, which is always 41.
        if len(message_bytes) != 41:
            continue

        message = sup800f.parse_binary(message_bytes)
        if message is not None:
            data.append(message)

    print('Received {} messages'.format(count))
    print('Received {} binary messages'.format(len(data)))

    seconds = [i * 0.1 for i in range(len(data))]
    hours = [sec / 3600. for sec in seconds]

    try:
        import matplotlib.pyplot as pyplot
    except ImportError:
        print('matplotlib not installed, skipping GUI')
        gui = False

    for attribute in (
            'acceleration_g_x',
            'acceleration_g_y',
            'acceleration_g_z',
            'magnetic_flux_ut_x',
            'magnetic_flux_ut_y',
            'magnetic_flux_ut_z',
            'pressure_p',
            'temperature_c',
    ):
        if gui:
            plot_data = [getattr(d, attribute) for d in data]

            pyplot.plot(hours, plot_data)
            pyplot.xlabel('time (hours)')
            pyplot.ylabel(attribute)
            pyplot.grid(True)
            pyplot.show()

        else:
            # Just print them
            print('***** {} ******'.format(attribute))
            for d in data:
                print(getattr(d, attribute))
            print('')


if __name__ == '__main__':
    # Poverty command line argument parsing
    if '-h' in sys.argv or len(sys.argv) < 2:
        print('Usage: {} <file> [--no-gui]'.format(sys.argv[0]))
        sys.exit(0)
    main(sys.argv[1], '--no-gui' not in sys.argv)
