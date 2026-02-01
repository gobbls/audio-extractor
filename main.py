#!/usr/bin/env python3


#
# TO DO:
#
# 5. Add arg options to:
#    a. Recurse directories                                                          [ -r | --recurse ]
#    b. Specify output directory                                                     [ -o | --output [INPUT] ]
#    c. Ability to delete the video files on completion                              [ -D | --delete ]
#    d. Keep all temp-files created during processing                                [ -k | --keep-all ]
#    e. Specify a directory for the temp files during processing                     [ -t | --temp-at [INPUT] ]
#    f. Get debug logger print-outs                                                  [ --debug ]
#    g. Ability to "walk" given directories with named directories to add to targets [ -w | --walk [INPUT] ]
#


import os
import logging
import subprocess
from sys import argv
from pathlib import Path

from file import File
import constants as c


# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
separator = '~' * os.get_terminal_size().columns


target_paths = argv[1:]


def check_dependencies() -> None:
    """
    Checks for the dependencies:
        1. `FFProbe`

    Rises an exception if not found.
    """
    try:
        subprocess.run(['ffprobe', '-loglevel', 'quiet'])
    except FileNotFoundError:
        logger.error(' Missing dependency "FFprobe"!')
        raise FileNotFoundError('FFprobe not found!')

    logger.debug(' Dependencies OK')


def check_targets() -> None:
    """
    Check that the given targets follows the rules:
        1. There are more than `0` targets.
        2. That all the targets `exists`.
        3. That all the targets are `directories`.
    """
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

    logger.debug(' Target directories OK')


def get_videos_from_path(path: str) -> [Path]:
    """
    Returns all files from a given path if the files suffix exists in
    a list of supported formats.

    Returns:
        `[str]`: An array of file paths.
    """
    return [item for item in Path(path).iterdir() if item.is_file() and item.suffix in c.VIDEO_FORMATS]


def main():
    paths: [Path] = []
    for target in target_paths:
        paths.extend(get_videos_from_path(target))

    logger.info(f' {len(paths)} files found, gathering metadata...')

    files: [File] = [File(path, index, len(paths)) for index, path in enumerate(paths, start=1)]

    logger.info(f' {len(files)} File objects initialized')

    for file in files:
        print(separator)
        print('[>] Queue:               ', f'{file.queue_number}/{len(paths)}')
        print('[>] Video path:          ', file.video_path)
        print('[>] Video audio codec:   ', file.audio_codec)
        print('[>] Video size (bytes):  ', file.video_size_b)
        print('[>] Video checksum:      ', file.video_md5_checksum)
        print('[>] Extracted image path:', file.image_path)

        file.extract_temp_audio()
        file.create_temp_cover_image()
        file.apply_cover_image()
        file.clean()


if __name__ == '__main__':
    check_dependencies()
    check_targets()
    main()

    print("\nDone!")
