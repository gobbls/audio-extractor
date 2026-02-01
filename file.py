import json
import logging
import hashlib
import subprocess
from pathlib import Path

import constants as c
from codec.codec import Codec


class File(Codec):
    video_md5_hashes: [str] = []
    final_output_paths: [str] = []

    def __init__(self, path: Path, queue_number: int, queue_length: int) -> None:
        """
        Inherits the Codec class wich is used to evaluate what
        codec to initialize based on the audio codec of the given video file.

        Args:
            `path` (Path): The path of the target video file.
            `queue_number` (int): The queue number of the video file.
            `queue_length` (int): How many other video files are in the queue.

        Attributes:
            `video_path` (Path): The path of the target video file.
            `queue_number` (int): The queue number of the video file.
            `queue_length` (int): How many other video files are in the queue.
            `video_md5_checksum` (str): The checksum of the video file.
            `video_md5_checksum_short` (str): The shortened version of the checksum.
            `audio_temp_path` (Path): The path of the temporary extracted audio file.
            `audio_path_wo_extension` (Path): The same path as `audio_temp_path` but without the file extension.
            `video_size_b` (int): The size of the video file in bytes.
            `audio_codec` (str): The codec of the __first found__ audio in the video.
            `image_path` (Path): The path of the temporary extracted (cover-)image file.
            `audio_codec_instance` (Codec): The Codec object instance, used to get the correct FFMPEG command.
        """
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
        self.audio_codec_instance: Codec | None = None

        self._cleaned: bool = False

        self._logger = logging.getLogger(__name__) # Preconfigured in main.
        self._logger.debug(f' [{self.queue_number}/{self.queue_length}] Working with path: "{path}"...')

        self._set_video_md5_checksum()
        self._set_audio_codec_and_video_size_b()
        self._set_temp_audio_path()
        self._set_audio_path_wo_extension()
        self._set_image_path()
        self._set_audio_codec_instance()


    def __del__(self) -> None:
        self.clean()


    def clean(self) -> None:
        """
        Remove the temporary assets the instance created.
        """
        self._logger.debug(' Deleting instance...')

        if not self._cleaned:
            self._remove_temp_audio()
            self._remove_image()


    def _check_duplicate_hash(self) -> bool:
        """
        Check if the video has a duplicate by matching the
        generated checksum with already initialized instance checksums.

        This also accounts for duplicates in other given targest as well,
        meaning; __if a duplicate is found in another directory, the exception is risen.__
        """
        self._logger.debug(' Checking for a duplicate hash...')

        if self.video_md5_checksum in self.video_md5_hashes:
            self._logger.debug(' Duplicate hash found! Terminating...')

            raise Exception(f'"{self.video_md5_checksum}" Has a duplicate that has already been processed!')


    def _set_video_md5_checksum(self) -> None:
        """
        Generates an md5 hash for the video file this instance is initialized for
        and sets the `video_md5_checksum` and `video_md5_checksum_short` properties.

        NOTE: Also checks for duplicate hashes before setting the property.
        """
        self._logger.debug(' Creating md5 hash...')

        md5: any = hashlib.md5()
        block_s: int = 65536 # 65KB (4096 x 16)

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
        """
        Gets the audio codec from the video file and sets it to the
        `video_md5_checksum` and `video_md5_checksum_short` properties.
        """
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

            self.video_size_b = str(out.get('format').get('size'))

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
        """
        Creates the path for the temporary extracted audio file
        and sets it to the `audio_temp_path` property.
        """
        self._logger.debug(' Setting temp audio path...')

        name: str = '.__' + self.video_md5_checksum_short + '_' + self.video_path.stem + '.' + self.audio_codec
        self.audio_temp_path = self.video_path.parent / name


    def _set_audio_path_wo_extension(self) -> None:
        """
        Takes the `audio_temp_path` path, removes the extension and sets
        it to the `audio_path_wo_extension` property.
        """
        self._logger.debug(' Setting final output path...')

        name: str = self.video_path.stem
        self.audio_path_wo_extension = self.video_path.parent / name


    def _set_image_path(self) -> None:
        """
        Creates the path for the temporary extracted image file
        and sets it to the `image_path` property.
        """
        self._logger.debug(' Setting image path...')

        self.image_path: Path = self.video_path.parent / f'.__{self.video_md5_checksum_short}_{c.COVER_ART_NAME}'


    def _fix_codec_instance_output_path(self) -> None:
        """
        Renames the final output in the Codec instance
        (__by appending the short checksum in front of the extension__)
        before the file is created, avoiding the collision.
        """
        self._logger.debug(' Fixing final name by appending short checksum for uniqueness...')

        path = Path(self.audio_codec_instance.output_path)
        new_path = str(path.parent / (path.stem + "_" + self.video_md5_checksum_short + "_" + path.suffix))
        self.audio_codec_instance.output_path = new_path


    def _check_duplicate_final_name(self) -> bool:
        """
        Check if there is a `Codec` instance `final_output`
        with the same name and extension as this `Codec` instance.
        """
        self._logger.debug(' Checking for a duplicate final output name...')

        while(self.audio_codec_instance.output_path in self.final_output_paths):
            self._logger.debug(' Duplicate final output name found! Renaming...')
            self._fix_codec_instance_output_path()


    def _set_audio_codec_instance(self) -> None:
        """
        Uses the inherited `Codec` class to set the correct audio
        codec instance to the `audio_codec_instance` property.

        NOTE: Also checks for duplicate final output names
        before setting the property.
        """
        codec = Codec(
            codec=self.audio_codec,
            audio_temp_path=self.audio_temp_path,
            image_path=self.image_path,
            output_name_wo_extension=self.audio_path_wo_extension,
        )

        self.audio_codec_instance = codec.get()

        self._check_duplicate_final_name()

        self.final_output_paths.append(self.audio_codec_instance.output_path)


    def _remove_image(self) -> None:
        """
        Removes the temporary generated image file,
        doing some checks before doing so.
        """
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
        """
        Removes the temporary generated audio file,
        doing some checks before doing so.
        """
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
        """
        Extracts a temporary audio file that will be duplicated
        __and then removed__ once the cover image is applied.

        __FFMPEG can't overwrite the file by itself,
        so a temporary file is required.__
        """
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
        """
        Extracts a temporary image file from the video.

        NOTE:
            Timestamp is specified by the `THUMBNAIL_CAPTURE_TIMESTAMP` constant.
        """
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
        """
        Applies the temporary image file to the temporary
        audio file __creating a duplicate audio file with
        the image applied as a cover.__
        """
        self._logger.debug(' Applying image to audio file...')

        try:
            subprocess.run(self.audio_codec_instance.get_command(), capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f'Failed to generate cover image: "{self.image_path}"! Got error:\n{e.stderr}')
        except:
            raise Exception(f'"{self.video_path}" Something else went wrong!')

        self._logger.debug(' Image applied')
