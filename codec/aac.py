import subprocess
from pathlib import Path


# same as m4a, but m4a containerizes aac
class aac:
    def __init__(self, temp_audio_path: Path, image_path: Path, output: str) -> None:
        self.audio_path = temp_audio_path
        self.image_path = image_path
        self.output = output

    def apply_cover_image(self) -> None:
        command = [
            'ffmpeg',
            '-i',
            self.audio_path,
            '-i',
            self.image_path,
            '-map',
            '0:a',
            '-map',
            '1:v',
            '-c',
            'copy',
            '-disposition:v',
            'attached_pic',
            self.output,
        ]

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(f'[ERROR] Failed to convert to {self.output}!\n\tGot error: {e.stderr}')
