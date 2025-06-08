"""
Conversion Service for FileConverter Pro

This service handles file conversions using multiple engines:
- FFmpeg for video and audio
- ImageMagick/Wand for images
- Pandoc for documents
- LibreOffice for office documents
"""

import os
import subprocess
import tempfile
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from flask import current_app
from PIL import Image, ImageEnhance
import ffmpeg
from wand.image import Image as WandImage
from wand.exceptions import WandException

from app.services.file_handler import FileHandler
from app.utils.helpers import get_file_type, format_file_size


class ConversionEngine:
    """Base class for all conversion engines"""

    @staticmethod
    def can_convert(source_format: str, target_format: str) -> bool:
        """Check if this engine can handle the conversion"""
        raise NotImplementedError

    @staticmethod
    def convert(input_path: str, output_path: str, options: Dict = None) -> Dict:
        """Perform the conversion"""
        raise NotImplementedError


class ImageConverter(ConversionEngine):
    """Image conversion using Pillow and ImageMagick/Wand"""

    # Formats supported by different engines
    PILLOW_FORMATS = {"jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "ico"}
    WAND_FORMATS = {
        "psd",
        "raw",
        "cr2",
        "nef",
        "dng",
        "heic",
        "heif",
        "avif",
        "svg",
        "eps",
        "pdf",
    }

    @staticmethod
    def can_convert(source_format: str, target_format: str) -> bool:
        """Check if we can convert between these image formats"""
        all_formats = ImageConverter.PILLOW_FORMATS | ImageConverter.WAND_FORMATS
        return (
            source_format.lower() in all_formats
            and target_format.lower() in all_formats
        )

    @staticmethod
    def convert(input_path: str, output_path: str, options: Dict = None) -> Dict:
        """Convert image using appropriate engine"""
        if not options:
            options = {}

        source_ext = os.path.splitext(input_path)[1][1:].lower()
        target_ext = os.path.splitext(output_path)[1][1:].lower()

        try:
            # Determine which engine to use
            if (
                source_ext in ImageConverter.WAND_FORMATS
                or target_ext in ImageConverter.WAND_FORMATS
                or options.get("use_imagemagick", False)
            ):
                return ImageConverter._convert_with_wand(
                    input_path, output_path, options
                )
            else:
                return ImageConverter._convert_with_pillow(
                    input_path, output_path, options
                )

        except Exception as e:
            current_app.logger.error(f"Image conversion failed: {e}")
            return {
                "success": False,
                "error": f"Image conversion failed: {str(e)}",
                "engine": "image_converter",
            }

    @staticmethod
    def _convert_with_pillow(input_path: str, output_path: str, options: Dict) -> Dict:
        """Convert using Pillow (PIL)"""
        try:
            with Image.open(input_path) as img:
                # Handle transparency for formats that don't support it
                target_format = os.path.splitext(output_path)[1][1:].upper()

                if target_format in ["JPEG", "JPG"] and img.mode in ["RGBA", "LA"]:
                    # Create white background for JPEG
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background

                # Apply image enhancements if specified
                if options.get("enhance"):
                    img = ImageConverter._apply_enhancements(img, options)

                # Resize if specified
                if options.get("resize"):
                    img = ImageConverter._resize_image(img, options["resize"])

                # Save with format-specific options
                save_options = ImageConverter._get_pillow_save_options(
                    target_format, options
                )
                img.save(output_path, format=target_format, **save_options)

            return {
                "success": True,
                "engine": "pillow",
                "input_size": os.path.getsize(input_path),
                "output_size": os.path.getsize(output_path),
            }

        except Exception as e:
            raise Exception(f"Pillow conversion failed: {str(e)}")

    @staticmethod
    def _convert_with_wand(input_path: str, output_path: str, options: Dict) -> Dict:
        """Convert using ImageMagick via Wand"""
        try:
            with WandImage(filename=input_path) as img:
                # Apply transformations
                if options.get("resize"):
                    width, height = options["resize"]
                    img.resize(width, height)

                if options.get("quality"):
                    img.compression_quality = options["quality"]

                if options.get("enhance"):
                    if options["enhance"].get("contrast"):
                        img.modulate(brightness=100, saturation=100, hue=100)

                # Set output format
                target_format = os.path.splitext(output_path)[1][1:].upper()
                img.format = target_format

                # Save
                img.save(filename=output_path)

            return {
                "success": True,
                "engine": "imagemagick",
                "input_size": os.path.getsize(input_path),
                "output_size": os.path.getsize(output_path),
            }

        except WandException as e:
            raise Exception(f"ImageMagick conversion failed: {str(e)}")

    @staticmethod
    def _apply_enhancements(img: Image.Image, options: Dict) -> Image.Image:
        """Apply image enhancements using Pillow"""
        enhance_options = options.get("enhance", {})

        if enhance_options.get("brightness"):
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(enhance_options["brightness"])

        if enhance_options.get("contrast"):
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(enhance_options["contrast"])

        if enhance_options.get("sharpness"):
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(enhance_options["sharpness"])

        return img

    @staticmethod
    def _resize_image(img: Image.Image, resize_options) -> Image.Image:
        """Resize image with various options"""
        if isinstance(resize_options, tuple):
            # Direct width, height
            return img.resize(resize_options, Image.Resampling.LANCZOS)
        elif isinstance(resize_options, dict):
            width = resize_options.get("width")
            height = resize_options.get("height")
            maintain_aspect = resize_options.get("maintain_aspect", True)

            if maintain_aspect and width and height:
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                return img
            elif width or height:
                original_width, original_height = img.size
                if width and not height:
                    height = int((width / original_width) * original_height)
                elif height and not width:
                    width = int((height / original_height) * original_width)
                return img.resize((width, height), Image.Resampling.LANCZOS)

        return img

    @staticmethod
    def _get_pillow_save_options(format_name: str, options: Dict) -> Dict:
        """Get format-specific save options for Pillow"""
        save_options = {}

        if format_name in ["JPEG", "JPG"]:
            save_options["quality"] = options.get("quality", 85)
            save_options["optimize"] = options.get("optimize", True)
        elif format_name == "PNG":
            save_options["optimize"] = options.get("optimize", True)
        elif format_name == "WEBP":
            save_options["quality"] = options.get("quality", 85)
            save_options["method"] = options.get("method", 6)

        return save_options


class VideoConverter(ConversionEngine):
    """Video conversion using FFmpeg"""

    VIDEO_FORMATS = {
        "mp4",
        "avi",
        "mov",
        "wmv",
        "flv",
        "webm",
        "mkv",
        "3gp",
        "m4v",
        "f4v",
        "asf",
        "rm",
        "rmvb",
        "vob",
        "ts",
        "mts",
        "m2ts",
    }

    @staticmethod
    def can_convert(source_format: str, target_format: str) -> bool:
        """Check if we can convert between these video formats"""
        return (
            source_format.lower() in VideoConverter.VIDEO_FORMATS
            and target_format.lower() in VideoConverter.VIDEO_FORMATS
        )

    @staticmethod
    def convert(input_path: str, output_path: str, options: Dict = None) -> Dict:
        """Convert video using FFmpeg"""
        if not options:
            options = {}

        try:
            # Build FFmpeg command
            input_stream = ffmpeg.input(input_path)

            # Apply video options
            video_options = {}
            audio_options = {}

            # Video quality/bitrate
            if options.get("crf"):
                video_options["crf"] = options["crf"]
            elif options.get("video_bitrate"):
                video_options["video_bitrate"] = options["video_bitrate"]

            # Resolution
            if options.get("resolution"):
                width, height = options["resolution"]
                video_options["s"] = f"{width}x{height}"

            # Frame rate
            if options.get("fps"):
                video_options["r"] = options["fps"]

            # Audio options
            if options.get("audio_bitrate"):
                audio_options["audio_bitrate"] = options["audio_bitrate"]

            # Codec options
            target_ext = os.path.splitext(output_path)[1][1:].lower()
            codec_options = VideoConverter._get_codec_options(target_ext, options)

            # Build and run FFmpeg command
            output_stream = ffmpeg.output(
                input_stream,
                output_path,
                **video_options,
                **audio_options,
                **codec_options,
            )

            # Run conversion
            ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

            return {
                "success": True,
                "engine": "ffmpeg",
                "input_size": os.path.getsize(input_path),
                "output_size": os.path.getsize(output_path),
            }

        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            current_app.logger.error(f"FFmpeg video conversion failed: {error_message}")
            raise Exception(f"Video conversion failed: {error_message}")
        except Exception as e:
            current_app.logger.error(f"Video conversion error: {e}")
            raise Exception(f"Video conversion failed: {str(e)}")

    @staticmethod
    def _get_codec_options(target_format: str, options: Dict) -> Dict:
        """Get codec options for target format"""
        codec_options = {}

        if target_format == "mp4":
            codec_options["vcodec"] = options.get("video_codec", "libx264")
            codec_options["acodec"] = options.get("audio_codec", "aac")
        elif target_format == "webm":
            codec_options["vcodec"] = options.get("video_codec", "libvpx-vp9")
            codec_options["acodec"] = options.get("audio_codec", "libopus")
        elif target_format == "avi":
            codec_options["vcodec"] = options.get("video_codec", "libx264")
            codec_options["acodec"] = options.get("audio_codec", "mp3")

        return codec_options


class AudioConverter(ConversionEngine):
    """Audio conversion using FFmpeg"""

    AUDIO_FORMATS = {
        "mp3",
        "wav",
        "flac",
        "aac",
        "ogg",
        "wma",
        "m4a",
        "opus",
        "ape",
        "ac3",
        "aiff",
        "au",
    }

    @staticmethod
    def can_convert(source_format: str, target_format: str) -> bool:
        """Check if we can convert between these audio formats"""
        return (
            source_format.lower() in AudioConverter.AUDIO_FORMATS
            and target_format.lower() in AudioConverter.AUDIO_FORMATS
        )

    @staticmethod
    def convert(input_path: str, output_path: str, options: Dict = None) -> Dict:
        """Convert audio using FFmpeg"""
        if not options:
            options = {}

        try:
            input_stream = ffmpeg.input(input_path)

            # Audio options
            audio_options = {}

            if options.get("bitrate"):
                audio_options["audio_bitrate"] = options["bitrate"]

            if options.get("sample_rate"):
                audio_options["ar"] = options["sample_rate"]

            if options.get("channels"):
                audio_options["ac"] = options["channels"]

            # Codec for target format
            target_ext = os.path.splitext(output_path)[1][1:].lower()
            codec = AudioConverter._get_audio_codec(target_ext)
            if codec:
                audio_options["acodec"] = codec

            # Run conversion
            output_stream = ffmpeg.output(input_stream, output_path, **audio_options)
            ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

            return {
                "success": True,
                "engine": "ffmpeg_audio",
                "input_size": os.path.getsize(input_path),
                "output_size": os.path.getsize(output_path),
            }

        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            raise Exception(f"Audio conversion failed: {error_message}")
        except Exception as e:
            raise Exception(f"Audio conversion failed: {str(e)}")

    @staticmethod
    def _get_audio_codec(format_name: str) -> Optional[str]:
        """Get appropriate codec for audio format"""
        codec_map = {
            "mp3": "libmp3lame",
            "aac": "aac",
            "ogg": "libvorbis",
            "opus": "libopus",
            "flac": "flac",
            "wav": "pcm_s16le",
        }
        return codec_map.get(format_name)


class DocumentConverter(ConversionEngine):
    """Document conversion using Pandoc and LibreOffice"""

    PANDOC_FORMATS = {"md", "html", "txt", "docx", "epub", "pdf"}
    LIBREOFFICE_FORMATS = {"doc", "docx", "odt", "pdf", "rtf"}

    @staticmethod
    def can_convert(source_format: str, target_format: str) -> bool:
        """Check if we can convert between these document formats"""
        all_formats = (
            DocumentConverter.PANDOC_FORMATS | DocumentConverter.LIBREOFFICE_FORMATS
        )
        return (
            source_format.lower() in all_formats
            and target_format.lower() in all_formats
        )

    @staticmethod
    def convert(input_path: str, output_path: str, options: Dict = None) -> Dict:
        """Convert document using appropriate engine"""
        if not options:
            options = {}

        source_ext = os.path.splitext(input_path)[1][1:].lower()
        target_ext = os.path.splitext(output_path)[1][1:].lower()

        try:
            # Choose conversion method
            if (
                source_ext in DocumentConverter.PANDOC_FORMATS
                and target_ext in DocumentConverter.PANDOC_FORMATS
            ):
                return DocumentConverter._convert_with_pandoc(
                    input_path, output_path, options
                )
            else:
                return DocumentConverter._convert_with_libreoffice(
                    input_path, output_path, options
                )

        except Exception as e:
            current_app.logger.error(f"Document conversion failed: {e}")
            raise Exception(f"Document conversion failed: {str(e)}")

    @staticmethod
    def _convert_with_pandoc(input_path: str, output_path: str, options: Dict) -> Dict:
        """Convert using Pandoc"""
        try:
            cmd = ["pandoc", input_path, "-o", output_path]

            # Add options
            if options.get("template"):
                cmd.extend(["--template", options["template"]])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise Exception(f"Pandoc error: {result.stderr}")

            return {
                "success": True,
                "engine": "pandoc",
                "input_size": os.path.getsize(input_path),
                "output_size": os.path.getsize(output_path),
            }

        except subprocess.TimeoutExpired:
            raise Exception("Pandoc conversion timed out")
        except Exception as e:
            raise Exception(f"Pandoc conversion failed: {str(e)}")

    @staticmethod
    def _convert_with_libreoffice(
        input_path: str, output_path: str, options: Dict
    ) -> Dict:
        """Convert using LibreOffice headless"""
        try:
            # Create temporary directory for output
            temp_dir = tempfile.mkdtemp()

            try:
                # LibreOffice command
                cmd = [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    os.path.splitext(output_path)[1][1:],  # target format
                    "--outdir",
                    temp_dir,
                    input_path,
                ]

                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120
                )

                if result.returncode != 0:
                    raise Exception(f"LibreOffice error: {result.stderr}")

                # Find the converted file and move it to the correct location
                input_filename = os.path.splitext(os.path.basename(input_path))[0]
                target_ext = os.path.splitext(output_path)[1]
                temp_output = os.path.join(temp_dir, f"{input_filename}{target_ext}")

                if not os.path.exists(temp_output):
                    raise Exception("LibreOffice did not create output file")

                # Move to final location
                os.rename(temp_output, output_path)

                return {
                    "success": True,
                    "engine": "libreoffice",
                    "input_size": os.path.getsize(input_path),
                    "output_size": os.path.getsize(output_path),
                }

            finally:
                # Cleanup temp directory
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)

        except subprocess.TimeoutExpired:
            raise Exception("LibreOffice conversion timed out")
        except Exception as e:
            raise Exception(f"LibreOffice conversion failed: {str(e)}")


class ConversionService:
    """Main conversion service that coordinates different engines"""

    def __init__(self):
        self.file_handler = FileHandler()
        self.engines = [
            ImageConverter,
            VideoConverter,
            AudioConverter,
            DocumentConverter,
        ]

    def convert_single_file(
        self, file_info: Dict, target_format: str, options: Dict = None
    ) -> Dict:
        """
        Convert a single file to target format

        Args:
            file_info: Information about the source file
            target_format: Target format extension
            options: Conversion options

        Returns:
            Dictionary with conversion result
        """
        if not options:
            options = {}

        start_time = time.time()

        try:
            source_path = file_info["path"]
            source_format = file_info["extension"]

            # Validate source file exists
            if not os.path.exists(source_path):
                return {
                    "success": False,
                    "error": "Source file not found",
                    "file_info": file_info,
                }

            # Create output path
            output_path = self.file_handler.create_conversion_path(
                file_info, target_format
            )

            # Find appropriate conversion engine
            engine = self._find_conversion_engine(source_format, target_format)
            if not engine:
                return {
                    "success": False,
                    "error": f"No conversion engine available for {source_format} to {target_format}",
                    "file_info": file_info,
                }

            # Perform conversion
            current_app.logger.info(
                f"Converting {source_format} to {target_format} using {engine.__name__}"
            )
            conversion_result = engine.convert(source_path, output_path, options)

            if conversion_result["success"]:
                # Create file info for converted file
                converted_file_info = {
                    "id": file_info["id"],
                    "original_filename": f"{os.path.splitext(file_info['original_filename'])[0]}.{target_format}",
                    "filename": os.path.basename(output_path),
                    "path": output_path,
                    "size": os.path.getsize(output_path),
                    "extension": target_format,
                    "converted_at": datetime.utcnow().isoformat(),
                    "conversion_time": round(time.time() - start_time, 2),
                    "engine": conversion_result.get("engine", "unknown"),
                }

                return {
                    "success": True,
                    "file_info": converted_file_info,
                    "conversion_stats": {
                        "input_size": conversion_result.get("input_size", 0),
                        "output_size": conversion_result.get("output_size", 0),
                        "compression_ratio": self._calculate_compression_ratio(
                            conversion_result.get("input_size", 0),
                            conversion_result.get("output_size", 0),
                        ),
                        "time_seconds": round(time.time() - start_time, 2),
                        "engine": conversion_result.get("engine"),
                    },
                }
            else:
                return {
                    "success": False,
                    "error": conversion_result.get("error", "Conversion failed"),
                    "file_info": file_info,
                }

        except Exception as e:
            current_app.logger.error(f"Conversion error: {e}")
            return {
                "success": False,
                "error": f"Conversion failed: {str(e)}",
                "file_info": file_info,
            }

    def convert_batch(
        self,
        job_id: str,
        files: List[Dict],
        target_format: str | None,
        options: Dict = None,
    ) -> Dict:
        """
        Convert multiple files in batch

        Args:
            job_id: Conversion job ID
            files: List of file information dictionaries
            target_format: Target format for all files
            options: Conversion options

        Returns:
            Dictionary with batch conversion results
        """
        if not options:
            options = {}

        start_time = time.time()
        converted_files = []
        errors = []

        current_app.logger.info(
            f"Starting batch conversion job {job_id}: {len(files)} files to {target_format or 'mixed'}"
        )

        for i, file_info in enumerate(files):
            try:
                # Update progress (this would typically update Redis/database)
                progress = int(((i + 1) / len(files)) * 100)
                current_app.logger.debug(f"Job {job_id} progress: {progress}%")

                # Convert single file
                per_target = file_info.get("target_format", target_format)
                result = self.convert_single_file(file_info, per_target, options)

                if result["success"]:
                    converted_files.append(result["file_info"])
                    current_app.logger.info(
                        f"Converted: {file_info['original_filename']}"
                    )
                else:
                    errors.append(
                        {
                            "filename": file_info["original_filename"],
                            "error": result["error"],
                        }
                    )
                    current_app.logger.error(
                        f"Failed to convert {file_info['original_filename']}: {result['error']}"
                    )

            except Exception as e:
                error_msg = f"Unexpected error converting {file_info.get('original_filename', 'unknown')}: {str(e)}"
                errors.append(
                    {
                        "filename": file_info.get("original_filename", "unknown"),
                        "error": error_msg,
                    }
                )
                current_app.logger.error(error_msg)

        # Calculate final results
        total_time = time.time() - start_time
        success_count = len(converted_files)
        error_count = len(errors)

        result = {
            "success": success_count > 0,
            "job_id": job_id,
            "completed_count": success_count,
            "error_count": error_count,
            "total_files": len(files),
            "converted_files": converted_files,
            "errors": errors,
            "total_time_seconds": round(total_time, 2),
            "average_time_per_file": round(total_time / len(files), 2) if files else 0,
        }

        current_app.logger.info(
            f"Batch conversion job {job_id} completed: "
            f"{success_count}/{len(files)} files converted in {total_time:.2f}s"
        )

        return result

    def _find_conversion_engine(self, source_format: str, target_format: str):
        """Find appropriate conversion engine for format pair"""
        for engine in self.engines:
            if engine.can_convert(source_format, target_format):
                return engine
        return None

    def _calculate_compression_ratio(self, input_size: int, output_size: int) -> float:
        """Calculate compression ratio"""
        if input_size == 0:
            return 0.0
        return round((1 - output_size / input_size) * 100, 2)

    def get_supported_conversions(self) -> Dict:
        """Get all supported conversion combinations"""
        conversions = {}

        # Get all supported formats from config
        supported_formats = current_app.config["ALLOWED_EXTENSIONS"]

        for category, formats in supported_formats.items():
            category_conversions = []

            for source_format in formats:
                for target_format in formats:
                    if source_format != target_format:
                        engine = self._find_conversion_engine(
                            source_format, target_format
                        )
                        if engine:
                            category_conversions.append(
                                {
                                    "from": source_format,
                                    "to": target_format,
                                    "engine": engine.__name__,
                                }
                            )

            if category_conversions:
                conversions[category] = category_conversions

        return conversions
