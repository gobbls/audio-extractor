#!/usr/bin/env python3

import time
import subprocess
import json
import os
from sys import argv
from pathlib import Path


VIDEO_FORMATS = ['.mkv', '.mp4', '.webm']
THUMBNAIL_CAPTURE_TIMESTAMP = '00:00:10'
TEMP_AUDIO_NAME_PREFIX = "output"
COVER_ART_NAME = "cover.jpg"


def check_dependencies() -> None:
    # Check that ffprobe is installed
    try:
        subprocess.run(["ffprobe", "-loglevel", "quiet"])
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


def create_temp_cover_image(path: str) -> str:
    full_path = os.path.join(Path(path).parent, COVER_ART_NAME)
    command = [
            'ffmpeg',
            '-loglevel',
            'quiet',
            '-i',
            path,
            '-ss',
            THUMBNAIL_CAPTURE_TIMESTAMP,
            '-frames:v',
            '1',
            full_path
            ]

    try:
        res = subprocess.run(command)
        print(f"[LOG] Cover image generated: {COVER_ART_NAME}")
    except res.CalledProcessError as e:
        raise ValueError(f"[ERROR] Failed to generate cover image: {COVER_ART_NAME}!\n\tGot error: {e.stderr}")

    return full_path


def remove_temp_cover_image(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
        print(f"[LOG] Cover image removed: {path}")
    else:
        raise ValueError(f"[ERROR] File {path} was generated, but was not able to be deleted!")


def remove_temp_audio_file(path: str, codec: str):
    _path = Path(path).parent
    full_path = os.path.join(_path, TEMP_AUDIO_NAME_PREFIX + "." + codec)
    if os.path.exists(full_path):
        os.remove(full_path)
        print(f"[LOG] Temp audio removed: {full_path}")
    else:
        raise ValueError(f"[ERROR] File {full_path} was generated, but was not able to be deleted!")


def get_audio_codec(full_path: str) -> str | None:
    command = [ 'ffprobe', '-show_format', '-show_streams', '-loglevel', 'quiet', '-print_format', 'json', full_path]

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True
        )
        probe_output = json.loads(result.stdout)
        for stream in probe_output.get('streams', []):
            if stream.get('codec_type') == 'audio':

                return stream.get('codec_name')

    except subprocess.CalledProcessError as e:
        raise ValueError(f'[ERROR] Failure running ffprobe: {e.stderr}')
    except json.JSONDecodeError:
        raise ValueError('[ERROR] Failure decoding JSON from ffprobe output!')

    return None


def convert(video_path: str, codec: str, cover_file_name_path: str) -> None:
    temp_audio_name = os.path.join(Path(video_path).parent, TEMP_AUDIO_NAME_PREFIX + "." + codec)
    final_name = os.path.splitext(video_path)[0] + "." + codec


    print(f"[LOG] Temp audio file name: {temp_audio_name}")
    
    copy_audio_command = ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'copy', temp_audio_name]
    #apply_art_command = ['ffmpeg', '-i', temp_audio_name, '-i', cover_file_name_path, '-c', 'copy', '-map', '0', '-map', '1', '-metadata:s:v', 'title="Album cover"', '-metadata:s:v', 'comment="Cover (front)"', final_name]
    apply_art_command = ['ffmpeg', '-i', temp_audio_name, '-i', cover_file_name_path, '-map', '0:a', '-map', '1:0', '-c:a', 'copy', '-c:v:0', 'libtheora', '-q:v:0', '10', '-disposition:v:0', 'attached_pic', final_name]

    print(f"[LOG] Running command: {copy_audio_command}")

    try:
        audio_res = subprocess.run(copy_audio_command)
        print("[LOG] Audio copied, applying cover art...")
        cover_res = subprocess.run(apply_art_command)
        print(f"[LOG] Cover art applied, final name: {final_name}")

    except audio_res.CalledProcessError as e:
        raise ValueError(f"[ERROR] Failed to convert to {temp_audio_name}!\n\tGot error: {e.stderr}")
    except cover_res.CalledProcessError as e:
        raise ValueError(f"[ERROR] Failed to apply cover art!\n\tGot error: {e.stderr}")


def get_videos_from_path(path: str) -> [str]:
    return [item.name for item in Path(path).iterdir() if item.is_file() and item.suffix in VIDEO_FORMATS]


def main():
    check_dependencies()
    parse_args()

    files = get_videos_from_path(argv[1])
    files_and_codecs = [{"name": file, "codec": get_audio_codec(os.path.join(argv[1], file))} for file in files]

    for item in files_and_codecs:
        path = os.path.join(argv[1], item['name'])
        img_path = create_temp_cover_image(path)

        convert(path, item['codec'], img_path)
        remove_temp_cover_image(img_path)
        remove_temp_audio_file(path, item['codec'])

        print()


if __name__ == '__main__':
	main()
