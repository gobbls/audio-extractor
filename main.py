#!/usr/bin/env python3


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

separator = '_' * (os.get_terminal_size().columns - 1)
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
    files: [File] = [File(f) for f in paths]

    logger.info(' Initialized File object for every target files')

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
