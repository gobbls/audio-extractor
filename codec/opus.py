from pathlib import Path


OUTPUT_EXTENSION = '.opus'


class opus:
    def __init__(self, temp_audio_path: Path, image_path: Path, output_name_wo_extension: Path) -> None:
        self.output_path: str = str(output_name_wo_extension) + OUTPUT_EXTENSION
        self.temp_audio_path: Path = temp_audio_path
        self.image_path: Path = image_path

    def get_command(self) -> [str]:
        return [
            'ffmpeg',
            '-i',
            self.temp_audio_path,
            '-i',
            self.image_path,
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
            self.output_path
        ]
