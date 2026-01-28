#!/usr/bin/env python3


from codec.file import File
import codec.constants as c

import os
import subprocess
import logging
from sys import argv
from pathlib import Path


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


target_paths = argv[1:]


def check_dependencies() -> None:
    # Check that ffprobe is installed
    try:
        subprocess.run(['ffprobe', '-loglevel', 'quiet'])
    except FileNotFoundError:
        logger.error('Missing dependency "FFprobe"!')
        raise FileNotFoundError('[ERROR] FFprobe not found!')

    logger.info('Dependencies OK')


def check_targets() -> None:
    # Check if the given target(s) exists
    for path in target_paths:
        if not os.path.exists(path):
            logger.error('One or more of the given targets does not exist!')
            raise FileNotFoundError('[ERROR] The given target(s) does not exist!')

    # Check if the given target(s) are directories
    for path in target_paths:
        if not Path.is_dir(path):
            logger.error('One or more of the given targets are not directories!')
            raise NotADirectoryError('[ERROR] The given target is not a directory!')

    logger.info('Target directories OK')


def get_videos_from_path(path: str) -> [Path]:
	return [item for item in Path(path).iterdir() if item.is_file() and item.suffix in c.VIDEO_FORMATS]


def main():
    paths: [Path] = []

    for target in target_paths:
        paths.extend(get_videos_from_path(target))

    logger.info('Got videos from target:')
    for path in paths:
        print("  >", path)

    files: [File] = [File(f) for f in paths]

    logger.info("Initialized File object for every target files")

    logger.info("Info:")
    separator = "-" * (os.get_terminal_size().columns - 1)
    for file in files:
        print(separator)
        print("[>] Video path:", file.video_path)
        print("  [>] Video audio codec:", file.audio_codec)
        print("  [>] Generated image path:", file.image_path)


if __name__ == '__main__':
	check_dependencies()
	check_targets()
	main()
