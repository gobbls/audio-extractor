import subprocess
from pathlib import Path


class opus:
    @staticmethod
    def apply_cover_image(
            self,
            audio_path: Path,
            cover_file_path: Path,
            final_name: str
            ) -> None:

        command = [
            'ffmpeg',
            '-i',
            audio_path,
            '-i',
            cover_file_path,
            '-map',
            '0:a',
            '-map',
            '1:0',
            '-c:a',
            'copy',
            '-c:v:0',
            'libtheora',
            '-q:v:0',
            '10',
            '-disposition:v:0',
            'attached_pic',
            final_name,
        ]

        try:
            res = subprocess.run(command)
        except subprocess.CalledProcessError as e:
            raise ValueError(f'[ERROR] Failed to convert to {final_name}!\n\tGot error: {e.stderr}')
