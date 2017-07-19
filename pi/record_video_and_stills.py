"""Records video and still images."""
import datetime
import os
import time

import picamera


def record_video_and_stills(seconds_per_video=None, seconds_between_stills=None):
    """Records video in chunks and still images until space runs out or another
    error occurs.

    Warning: the seconds calculation will be off if seconds_per_video is not a
    multiple of seconds_between_stills.
    """
    if seconds_per_video is None:
        seconds_per_video = 5 * 60
    elif seconds_per_video < 15:
        raise ValueError('Invalid seconds_per_video')

    if seconds_between_stills is None:
        seconds_between_stills = 5
    elif seconds_between_stills < 1:
        raise ValueError('Invalid seconds_between_stills')

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
            camera.start_recording(video_file_name, seconds_per_video)

            video_seconds_elapsed = 0
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

            camera.stop_recording()


def main():
    """Main."""
    record_video_and_stills()


if __name__ == '__main__':
    main()
