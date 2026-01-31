from pathlib import Path


OUTPUT_EXTENSION = '.mp3'


class mp3:
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
            '0:0',
            '-map',
            '1:0',
            '-c',
            'copy',
            '-id3v2_version',
            '3',
            self.output_path
        ]
