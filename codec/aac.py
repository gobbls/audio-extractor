from pathlib import Path


OUTPUT_EXTENSION = '.m4a' # same as m4a, but m4a containerizes aac


class aac:
    def __init__(self, temp_audio_path: Path, image_path: Path, output_name_wo_extension: Path) -> None:
        self.output_path: str = str(output_name_wo_extension) + OUTPUT_EXTENSION
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
            self.output_path
        ]
