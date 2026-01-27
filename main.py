#!/usr/bin/env python3


from codec.File import File
import codec.constants as c

import os
import subprocess
from sys import argv
from pathlib import Path


target_path = argv[1]


def check_dependencies() -> None:
    # Check that ffprobe is installed
    try:
        subprocess.run(['ffprobe', '-loglevel', 'quiet'])
    except FileNotFoundError:
        raise ValueError('[ERROR] ffprobe not found!')

    # Check that the given path exists
    if not os.path.exists(target_path):
        raise ValueError('[ERROR] The given target does not exist!')

    # Check that the given target is a directory
    if not Path.is_dir(target_path):
        raise ValueError('[ERROR] The given target is not a directory!')

    print("[LOG] Dependencies OK")


def parse_args() -> None:
    if len(argv) > 2 or len(argv) == 1:
        raise ValueError('[ERROR] Currently only supports a single directory!')
    print("[LOG] Parsed OK")


def get_videos_from_path(path: str) -> [Path]:
	return [item for item in Path(path).iterdir() if item.is_file() and item.suffix in c.VIDEO_FORMATS]


def main():
    paths: [Path] = get_videos_from_path(target_path)
    print("[LOG] Got videos from target")
    for file in paths:
        print("\t>", file)
    files: [File] = [File(f) for f in paths]
    print("[LOG] Initialized File object for every target files")

    for file in files:
        print("[>] Video path:", file.video_path)
        print("[>] Video audio codec:", file.audio_codec)
        print("[>] Generated image path:", file.image_path)


if __name__ == '__main__':
	check_dependencies()
	parse_args()
	main()
