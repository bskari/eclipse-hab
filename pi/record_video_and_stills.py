"""Records video and still images."""
import datetime
import os
import subprocess
import sys
import time

import picamera


def record_video_and_stills(seconds_per_video, seconds_between_stills):
    """Records video in chunks and still images until space runs out or another
    error occurs.

    Warning: the seconds calculation will be off if seconds_per_video is not a
    multiple of seconds_between_stills.
    """
    if seconds_per_video < 15:
        raise ValueError('Invalid seconds_per_video')

    if seconds_between_stills < 1:
        raise ValueError('Invalid seconds_between_stills')

    logger = logging.Logger('temperature')

    video_path = 'videos'
    image_path = 'images'
    if not os.path.isdir(video_path):
        os.mkdir(video_path)
    if not os.path.isdir(image_path):
        os.mkdir(image_path)

    with picamera.PiCamera() as camera:
        camera.resolution = (1920, 1080)
        camera.start_preview()
        # Wait for the camera to initialize
        time.sleep(2)

        # Something in here will eventually throw
        while True:
            video_file_name = video_path + os.sep + datetime.datetime.strftime(
                datetime.datetime.now(),
                '%Y-%m-%d_%H:%M:%S.h264'
            )
            logger.info('Saving {}'.format(video_file_name))
            camera.start_recording(video_file_name)

            video_seconds_elapsed = 0
            image_count = 1
            while video_seconds_elapsed < seconds_per_video:
                camera.wait_recording(seconds_between_stills)
                # TODO: Handle the case where seconds_per_video is not a multiple
                # of second_between_stills
                video_seconds_elapsed += seconds_between_stills

                image_file_name = image_path + os.sep + datetime.datetime.strftime(
                    datetime.datetime.now(),
                    '%Y-%m-%d_%H:%M:%S.jpg'
                )
                camera.capture(image_file_name, use_video_port=True)
                sys.stdout.write('{} '.format(image_count))
                sys.stdout.flush()
                image_count += 1

                try:
                    mibibytes_free = get_free_mibibytes()
                    if mibibytes_free < 100:
                        logger.info('{} mibibytes free, stopping video'.format(mibibytes_free))
                        camera.stop_recording()
                        return
                except Exception as exc:
                    logger.error('Error finding free disk space: {}'.format(exc))

            camera.stop_recording()


def get_free_mibibytes():
    """Returns the number of free mibibytes on /."""
    df_output = subprocess.check_output(('df', '--output=avail', '/', '--block-size=M'))

    # Python 3 support
    if isinstance(df_output, bytes):
        df_output = df_output.decode()

    last_line = df_output.decode().split('\n')[1]
    if last_line.endswith('M'):
        mibibytes_free = int(last_line[:-1])
    else:  # This shouldn't happen, but, maybe try just parsing a number
        mibibytes_free = int(last_line)
    return mibibytes_free


def main():
    """Main."""
    logger = logging.Logger('temperature')
    formatter = logging.Formatter(
        '%(asctime)s:%(levelname)s %(message)s'
    )

    file_handler = logging.FileHandler('temperature.log')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)

    if len(sys.argv) > 2:
        seconds_between_stills = int(sys.argv[1])
    else:
        seconds_between_stills = 5

    if len(sys.argv) > 1:
        seconds_per_video = int(sys.argv[0])
    else:
        seconds_per_video = 5 * 60

    try:
        record_video_and_stills(seconds_per_video, seconds_between_stills)
    except Exception as exc:
        logger.error(exc)


if __name__ == '__main__':
    main()
