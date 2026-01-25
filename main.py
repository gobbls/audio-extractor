#!/usr/bin/env python3


import os
import subprocess
from sys import argv
from pathlib import Path
import constants as c
from codec import File


def check_dependencies() -> None:
	# Check that ffprobe is installed
	try:
		subprocess.run(['ffprobe', '-loglevel', 'quiet'])
	except FileNotFoundError:
		raise ValueError('[ERROR] ffprobe not found!')

	# Check that the given path exists
	if not os.path.exists(argv[1]):
		raise ValueError('[ERROR] The given target does not exist!')

	# Check that the given target is a directory
	if not Path.is_dir(argv[1]):
		raise ValueError('[ERROR] The given target is not a directory!')


def parse_args() -> None:
	if len(argv) > 2:
		raise ValueError('[ERROR] Currently only supports a single directory!')


def get_videos_from_path(path: str) -> [Path]:
	return [item for item in Path(path).iterdir() if item.is_file() and item.suffix in c.VIDEO_FORMATS]


def main():
    paths = get_videos_from_path(argv[1])
    files = [File(f) for f in paths]

    for file in files:
        ...


if __name__ == '__main__':
	check_dependencies()
	parse_args()
	main()
