from pathlib import Path


OUTPUT_EXTENSION = '.m4a'


class m4a:
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
            '1:v',
            '-c',
            'copy',
            '-disposition:v',
            'attached_pic',
            str(output_name_wo_extension) + OUTPUT_EXTENSION
        ]
