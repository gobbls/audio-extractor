from pathlib import Path

from .m4a import m4a
from .aac import aac
from .mp3 import mp3
from .opus import opus


class Codec(m4a, aac, mp3, opus):
    def __init__(self, codec: str, audio_temp_path: Path, image_path: Path, output_name_wo_extension: Path) -> None:

        if codec not in globals():
            raise NotImplementedError(f'Undefined codec "{codec}"!')

        self.codec_class: str = globals()[codec]
        self.audio_temp_path: Path = audio_temp_path
        self.image_path: Path = image_path
        self.output_name_wo_extension: Path = output_name_wo_extension


    def get(self):
        audio_codec_instance = self.codec_class(self.audio_temp_path, self.image_path, self.output_name_wo_extension)

        return audio_codec_instance
