from . import constants as c
from . import m4a, mp3, opus

import subprocess
import json
import os
import hashlib
from pathlib import Path


class File(m4a, mp3, opus):
    def __init__(self, full_path: Path) -> None:
        self.file_full_path: Path = full_path

        self.file_checksum: str = None
        self.file_checksum_short: str = None
        self.codec: str = None
        self.cover_image_path: Path = None

        self._set_md5_hash()
        self._set_audio_codec()


    def __del__(self) -> None:
        self._remove_temp_cover_image()
        self._remove_temp_audio_file()


    def _set_md5_hash(self) -> None:
        md5: any = hashlib.md5()
        block_s: int = 65536

        try:
            with open(self.file_full_path, 'rb') as f:
                for block in iter(lambda: f.read(block_s), b""):
                    md5.update(block)
            hash: str = md5.hexdigest()
            self.file_checksum = hash
            self.file_checksum_short = hash[:5]
        except IOError as e:
            raise ValueError(f'[ERROR] @ [{self.file_full_path}] Failed to hash: {e}')


    def _set_audio_codec(self) -> None:
        command: [str] = [
            'ffprobe',
            '-show_format',
            '-show_streams',
            '-loglevel',
            'quiet',
            '-print_format',
            'json',
            self.file_full_path
        ]

        try:
            res: any = subprocess.run(command, capture_output=True, text=True, check=True)
            out: any = json.loads(res.stdout)

            for stream in out.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    self.codec = stream.get('codec_name')

        except subprocess.CalledProcessError as e:
            raise ValueError(f'[ERROR] @ [{self.file_full_path}] Failure running ffprobe: {e.stderr}!')
        except json.JSONDecodeError:
            raise ValueError(f'[ERROR] @ [{self.file_full_path}] Failure decoding JSON from ffprobe output!')
        except:
            raise ValueError(f'[ERROR] @ [{self.file_full_path}] Something else went wrong!')


    def _remove_temp_cover_image(self) -> None:
        if self.cover_image_path.exists():
            self.cover_image_path.unlink()

            if not self.cover_image_path.exists():
                print(f'[LOG] Cover image removed: {self.cover_image_path}')
            else:
                raise ValueError(f'[ERROR] File {self.cover_image_path} was generated, but was not able to be deleted!')

        else:
            print(f'[WARNING] @ [{self.cover_image_path}] Cover image does not exsist, and couldn\'t be deleted!')
            return


    def _remove_temp_audio_file(self) -> None:
        ...


    def extract_temp_audio(self) -> None:
        audio_temp_name: str = self.file_full_path.name + '.' + self.codec

        final_name: str = os.path.splitext(self.file_full_path)[0] + '.' + self.codec

        command: [str] = [
            'ffmpeg',
            '-i',
            self.file_full_path,
            '-vn',
            '-acodec',
            'copy',
            audio_temp_name,
        ]


    def create_temp_cover_image(self) -> None:
        name: str = self.file_checksum_short + "_" + c.COVER_ART_NAME
        output: str = Path(os.path.join(self.file_full_path.parent, name))
        command: [str] = [
            'ffmpeg',
            '-loglevel',
            'quiet',
            '-i',
            self.file_full_path,
            '-ss',
            c.THUMBNAIL_CAPTURE_TIMESTAMP,
            '-frames:v',
            '1',
            output,
        ]

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            self.cover_image_path = output
            print(f'[LOG] Cover image generated at: {output}')
        except subprocess.CalledProcessError as e:
            raise ValueError(f'[ERROR] Failed to generate cover image: {output}!\n\tGot error: {e.stderr}')
        except:
            raise ValueError(f'[ERROR] @ [{self.file_full_path}] Something else went wrong!')


    def extract_audio(self) -> None:
        ...


    def apply_conver_art(self) -> None:
        if self.codec in globals():
            dynamic_codec = globals()[self.codec]
            codec_instance = dynamic_codec()
            codec_instance.apply_cover_image(
                audio_path=Path(),      # temp
                cover_file_path=Path(), # temp
                final_name=""           # temp
            )
        else:
            raise ValueError(f"[ERROR] @ [{self.file_full_path}] has a undefined codec '{self.codec}'!")
