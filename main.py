#!/usr/bin/env python3


#
# TO DO:
#
# 1. Keep track of the --number of files-- being processed AND the filesize.
#    - Add a --"queue number"-- and "file size" property to the instance.
#
# 2. Add Queing (?) to process multiple files in parallel.
#
# 3. Get rid of the temp files when their operation is complete.
#    TL;DR: dispose of the instance once the operation is completed.
#    (the instance lives in a array, and stays there until the program completes)
#    - Perhaps just pop it's index from the array?
#    - Can queues be used here?
#
# 4. Limit how much data is being read when creating the checksum.
#    (don't need the whole 2GB to create a checksum...)
#
# 5. Add arg options to:
#    a. Recurse directories (-r | --recurse)
#    b. Specify output directory (-o | --output)
#    c. Ability to delete the video files on completion (-D | --delete)
#    d. Keep all temp-files created during processing (-k | --keep-all)
#    e. Specify a directory for the temp files during processing (-t | --temp-at)
#
# 6. Do "collision" check before processing.
#    - Same shortened checksum
#    - Same final output name (different video format, maybe same audio codec?)
#
# TO FIX:
#
# 1. Had to press "Enter" on the last two big files for the program to complete. Why?
#    - CPU was idle.
#    - Was at the "Applying image" step of the process.
#


import os
import logging
import subprocess
from sys import argv
from pathlib import Path

from codec.file import File
from codec import constants as c


# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

separator = '~' * (os.get_terminal_size().columns - 1)
separator_half = '~' * (os.get_terminal_size().columns // 2)


target_paths = argv[1:]


def check_dependencies() -> None:
    # Check that ffprobe is installed
    try:
        subprocess.run(['ffprobe', '-loglevel', 'quiet'])
    except FileNotFoundError:
        logger.error(' Missing dependency "FFprobe"!')
        raise FileNotFoundError('FFprobe not found!')

    logger.info(' Dependencies OK')


def check_targets() -> None:
    #check if there are more than 0 targets
    if len(target_paths) == 0:
        raise FileNotFoundError('One or more target directories required!')

    # Check if the given target(s) exists
    for path in target_paths:
        if not os.path.exists(path):
            logger.error(f' Path "{path}" does not exist!')
            raise FileNotFoundError('The given target(s) does not exist!')

    # Check if the given target(s) are directories
    for path in target_paths:
        if not Path.is_dir(path):
            logger.error(f' Path "{path}" is not a directory!')
            raise NotADirectoryError('The given target(s) is not a directory!')

    logger.info(' Target directories OK')


def get_videos_from_path(path: str) -> [Path]:
	return [item for item in Path(path).iterdir() if item.is_file() and item.suffix in c.VIDEO_FORMATS]


def main():
    paths: [Path] = []
    for target in target_paths:
        paths.extend(get_videos_from_path(target))
    files: [File] = [File(path, index, len(paths)) for path, index in paths]

    logger.info(f' {len(paths)} files found')
    logger.info(f' {len(files)} File objects initialized')

    for file in files:
        print(separator)
        print('[>] Video path:', file.video_path)
        print('[>] Video audio codec:', file.audio_codec)
        print('[>] Generated image path:', file.image_path)
        print(separator_half)
        file.extract_temp_audio()
        file.create_temp_cover_image()
        file.apply_cover_image()


if __name__ == '__main__':
	check_dependencies()
	check_targets()
	main()
