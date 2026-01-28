from . import constants as c
from .m4a import m4a
from .mp3 import mp3
from .opus import opus
from .aac import aac

import subprocess
import json
import hashlib
from pathlib import Path


class File(m4a, mp3, opus, aac):
    def __init__(self, path: Path) -> None:
        self.video_path: Path = path

        self.video_md5_checksum: str = None
        self.video_md5_checksum_short: str = None
        self.audio_temp_path: Path = None
        self.audio_path: Path = None
        self.audio_codec: str = None
        self.image_path: Path = None

        self._set_video_md5_checksum()
        self._set_audio_codec()
        self._set_temp_audio_path()
        self._set_audio_path()
        self._set_image_path()


    def __del__(self) -> None:
        self._remove_temp_audio()
        self._remove_image()


    def _set_video_md5_checksum(self) -> None:
        md5: any = hashlib.md5()
        block_s: int = 65536

        try:
            with open(self.video_path, 'rb') as f:
                for block in iter(lambda: f.read(block_s), b""):
                    md5.update(block)
            hash: str = md5.hexdigest()
            self.video_md5_checksum = hash
            self.video_md5_checksum_short = hash[:5]
        except IOError as e:
            raise ValueError(f'[ERROR] @ [{self.video_path}] Failed to create checksum\n\tGot error: {e}')


    def _set_audio_codec(self) -> None:
        command: [str] = [
            'ffprobe',
            '-show_format',
            '-show_streams',
            '-loglevel',
            'quiet',
            '-print_format',
            'json',
            self.video_path
        ]

        try:
            res: any = subprocess.run(command, capture_output=True, text=True, check=True)
            out: any = json.loads(res.stdout)

            for stream in out.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    self.audio_codec = stream.get('codec_name')

        except subprocess.CalledProcessError as e:
            raise ValueError(f'[ERROR] @ [{self.video_path}] Failure running ffprobe\n\tGot error: {e.stderr}!')
        except json.JSONDecodeError:
            raise ValueError(f'[ERROR] @ [{self.video_path}] Failure decoding JSON from ffprobe output!')
        except:
            raise ValueError(f'[ERROR] @ [{self.video_path}] Something else went wrong!')


    def _set_temp_audio_path(self) -> None:
        name: str = self.video_md5_checksum_short + "_" + self.video_path.stem + "." + self.audio_codec
        self.audio_temp_path = self.video_path.parent / name

    def _set_audio_path(self) -> None:
        name: str = self.video_path.stem + "." + self.audio_codec
        self.audio_temp_path = self.video_path.parent / name


    def _set_image_path(self) -> None:
        self.image_path: Path = self.video_path.parent / f"{self.video_md5_checksum_short}_{c.COVER_ART_NAME}"


    def _remove_image(self) -> None:
        if self.image_path.exists():
            self.image_path.unlink()

            if not self.image_path.exists():
                print(f'[LOG] Cover image removed: {self.image_path}')
            else:
                raise ValueError(f'[ERROR] File {self.image_path} was generated, but was not able to be deleted!')

        else:
            print(f'[WARNING] @ [{self.image_path}] Cover image does not exsist, and couldn\'t be deleted!')


    def _remove_temp_audio(self) -> None:
        if self.audio_temp_path.exists():
            self.audio_temp_path.unlink()

            if not self.audio_temp_path.exists():
                print(f'[LOG] Cover image removed: {self.audio_temp_path}')
            else:
                raise ValueError(f'[ERROR] File {self.audio_temp_path} was generated, but was not able to be deleted!')

        else:
            print(f'[WARNING] @ [{self.audio_temp_path}] Cover image does not exsist, and couldn\'t be deleted!')


    def extract_temp_audio(self) -> None:
        command: [str] = [
            'ffmpeg',
            '-i',
            self.video_path,
            '-vn',
            '-acodec',
            'copy',
            self.audio_temp_path,
        ]

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            print(f'[LOG] Audio extracted to: {self.audio_temp_path}')
        except subprocess.CalledProcessError as e:
            raise ValueError(f'[ERROR] Failed to extract audio: {self.audio_temp_path}!\n\tGot error: {e.stderr}')
        except:
            raise ValueError(f'[ERROR] @ [{self.video_path}] Something else went wrong!')


    def create_temp_cover_image(self) -> None:
        command: [str] = [
            'ffmpeg',
            '-loglevel',
            'quiet',
            '-i',
            self.video_path,
            '-ss',
            c.THUMBNAIL_CAPTURE_TIMESTAMP,
            '-frames:v',
            '1',
            self.image_path,
        ]

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            print(f'[LOG] Cover image generated at: {self.image_path}')
        except subprocess.CalledProcessError as e:
            raise ValueError(f'[ERROR] Failed to generate cover image: {self.image_path}!\n\tGot error: {e.stderr}')
        except:
            raise ValueError(f'[ERROR] @ [{self.video_path}] Something else went wrong!')


    def apply_conver_art(self) -> None:
        if self.audio_codec in globals():
            dynamic_codec = globals()[self.audio_codec]
            codec_instance = dynamic_codec(
                temp_audio_path=self.audio_temp_path,
                image_path=self.image_path,
                output=self.audio_path
            )
            codec_instance.apply_cover_image()
        else:
            raise ValueError(f"[ERROR] @ [{self.video_path}] has a undefined codec '{self.audio_codec}'!")
