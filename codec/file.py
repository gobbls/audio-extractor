import json
import logging
import hashlib
import subprocess
from pathlib import Path

from .m4a import m4a
from .aac import aac
from .mp3 import mp3
from .opus import opus
from . import constants as c


class File(m4a, mp3, opus, aac):
    # Collect all generated hashes to find duplicate files.
    video_md5_hashes = []

    def __init__(self, path: Path, queue_number: int, queue_length: int) -> None:
        self.video_path: Path = path
        self.queue_number: int = queue_number
        self.queue_length: int = queue_length

        self.video_md5_checksum: str | None = None
        self.video_md5_checksum_short: str | None= None
        self.audio_temp_path: Path | None = None
        self.audio_path_wo_extension: Path | None = None
        self.video_size_b: int | None = None
        self.audio_codec: str | None = None
        self.image_path: Path | None = None

        self._ran_cleanup: bool = False

        # Preconfigured in main.
        self._logger = logging.getLogger(__name__)

        self._logger.debug(f' [{self.queue_number}/{self.queue_length}] Working with path: "{path}"...')

        self._set_video_md5_checksum()
        self._set_audio_codec_and_video_size_b()
        self._set_temp_audio_path()
        self._set_audio_path_wo_extension()
        self._set_image_path()


    def __del__(self) -> None:
        if not self._ran_cleanup:
            self._logger.debug(' Deleting instance...')

            self._remove_temp_audio()
            self._remove_image()


    def clean(self) -> None:
        self._logger.debug(' Deleting instance (manual cleanup)...')

        self._remove_temp_audio()
        self._remove_image()

        self._ran_cleanup = True


    def _check_duplicate_hash(self) -> bool:
        self._logger.debug(' Checking for a duplicate hash...')

        if self.video_md5_checksum in self.video_md5_hashes:
            self._logger.debug(' Duplicate hash found! Terminating...')

            raise Exception(f'"{self.video_md5_checksum}" Has a duplicate that has already been processed!')


    def _set_video_md5_checksum(self) -> None:
        self._logger.debug(' Creating md5 hash...')

        md5: any = hashlib.md5()
        block_s: int = 65536 # 65KB (4096 x 16)

        # 
        # Note:
        #   Should be able to limit the amount of data gathered for the
        #   hash, in order to get a fuzzy hash (not used for integrity here).
        #   But need to figure out how large the header information is
        #   in order to scan past it, so that the hash is unique.
        #

        try:
            with open(self.video_path, 'rb') as f:
                for block in iter(lambda: f.read(block_s), b''):
                    md5.update(block)
        except IOError as e:
            raise Exception(f'"{self.video_path}" Failed to create hash! Got error:\n{e}')

        hash: str = md5.hexdigest()
        self.video_md5_checksum = hash
        self.video_md5_checksum_short = hash[:9]

        self._check_duplicate_hash()

        self.video_md5_hashes.append(hash)


    def _set_audio_codec_and_video_size_b(self) -> None:
        self._logger.debug(' Getting audio codec and file size...')

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

            # Set the file size (bytes).
            self.video_size_b = str(out.get('format').get('size'))

            # Set the audio codec.
            for stream in out.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    self.audio_codec = stream.get('codec_name')

        except subprocess.CalledProcessError as e:
            raise Exception(f'"{self.video_path}" Failure running ffprobe! Got error:\n{e.stderr}!')
        except json.JSONDecodeError:
            raise Exception(f'"{self.video_path}" Failure decoding JSON from ffprobe output!')
        except:
            raise Exception(f'"{self.video_path}" Something else went wrong!')


    def _set_temp_audio_path(self) -> None:
        self._logger.debug(' Setting temp audio path...')

        name: str = '.__' + self.video_md5_checksum_short + '_' + self.video_path.stem + '.' + self.audio_codec
        self.audio_temp_path = self.video_path.parent / name


    def _set_audio_path_wo_extension(self) -> None:
        self._logger.debug(' Setting final output path...')

        name: str = self.video_path.stem
        self.audio_path_wo_extension = self.video_path.parent / name


    def _set_image_path(self) -> None:
        self._logger.debug(' Setting image path...')

        self.image_path: Path = self.video_path.parent / f'.__{self.video_md5_checksum_short}_{c.COVER_ART_NAME}'


    def _remove_image(self) -> None:
        self._logger.debug(' Removing image...')

        if self.image_path.exists():
            self.image_path.unlink()

            if not self.image_path.exists():
                self._logger.debug(f' Image removed: "{self.image_path}"')
            else:
                raise FileExistsError(f'File "{self.image_path}" was generated, but was not able to be deleted!')

        else:
            self._logger.warn(f' "{self.image_path}" Image does not exsist, and couldn\'t be deleted!')


    def _remove_temp_audio(self) -> None:
        self._logger.debug(' Removing temp audio...')

        if self.audio_temp_path.exists():
            self.audio_temp_path.unlink()

            if not self.audio_temp_path.exists():
                self._logger.debug(f' Temp audio removed: "{self.audio_temp_path}"')
            else:
                raise FileExistsError(f'File "{self.audio_temp_path}" was generated, but was not able to be deleted!')

        else:
            self._logger.warn(f' "{self.audio_temp_path}" Temp audio does not exsist, and couldn\'t be deleted!')


    def extract_temp_audio(self) -> None:
        self._logger.debug(' Extracting audio...')

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
        except subprocess.CalledProcessError as e:
            raise Exception(f'Failed to extract audio: "{self.audio_temp_path}"! Got error:\n{e.stderr}')
        except:
            raise Exception(f'"{self.video_path}" Something else went wrong!')

        self._logger.debug(f' Audio extracted to: "{self.audio_temp_path}"')


    def create_temp_cover_image(self) -> None:
        self._logger.debug(f' Extracting image from timestamp: {c.THUMBNAIL_CAPTURE_TIMESTAMP}...')

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
        except subprocess.CalledProcessError as e:
            raise Exception(f'Failed to generate cover image: "{self.image_path}"! Got error:\n{e.stderr}')
        except:
            raise Exception(f'"{self.video_path}" Something else went wrong!')

        self._logger.debug(f' Cover image extracted to: "{self.image_path}"')


    def apply_cover_image(self) -> None:
        self._logger.debug(' Applying image to audio file...')

        # Raise exception if a codec ic NOT defined
        if self.audio_codec not in globals():
            raise NotImplementedError(f'"{self.video_path}" has a undefined codec "{self.audio_codec}"!')

        dynamic_codec = globals()[self.audio_codec]
        codec_instance = dynamic_codec(
            temp_audio_path=self.audio_temp_path,
            image_path=self.image_path,
            output_name_wo_extension=self.audio_path_wo_extension,
        )

        try:
            subprocess.run(codec_instance.command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f'Failed to generate cover image: "{self.image_path}"! Got error:\n{e.stderr}')
        except:
            raise Exception(f'"{self.video_path}" Something else went wrong!')

        self._logger.debug(' Image applied')
