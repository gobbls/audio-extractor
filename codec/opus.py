from pathlib import Path


OUTPUT_EXTENSION = '.opus'


class opus:
    def __init__(self, temp_audio_path: Path, image_path: Path, output_name_wo_extension: Path) -> None:
        self.command: [str] = [
            'ffmpeg',
            '-i',
            temp_audio_path,
            '-i',
            image_path,
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
            str(output_name_wo_extension) + OUTPUT_EXTENSION
        ]
