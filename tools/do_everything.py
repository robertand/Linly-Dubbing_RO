import json
import os
import time
import traceback

import torch
from loguru import logger
from .step000_video_downloader import get_info_list_from_url, download_single_video, get_target_folder
from .step010_demucs_vr import separate_all_audio_under_folder, init_demucs, release_model
from .step020_asr import transcribe_all_audio_under_folder
from .step021_asr_whisperx import init_whisperx, init_diarize
from .step022_asr_funasr import init_funasr
from .step030_translation import translate_all_transcript_under_folder
from .step040_tts import generate_all_wavs_under_folder
from .step042_tts_xtts import init_TTS
from .step043_tts_cosyvoice import init_cosyvoice
from .step050_synthesize_video import synthesize_all_video_under_folder
from concurrent.futures import ThreadPoolExecutor, as_completed

# 跟踪模型初始化状态
models_initialized = {
    'demucs': False,
    'xtts': False,
    'cosyvoice': False,
    'whisperx': False,
    'diarize': False,
    'funasr': False
}


def get_available_gpu_memory():
    """Get currently available GPU memory size (GB)"""
    try:
        if torch.cuda.is_available():
            # Get available VRAM of current device
            free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
            return free_memory / (1024 ** 3)  # Convert to GB
        return 0  # If no GPU or CUDA unavailable
    except Exception:
        return 0  # Return 0 on error


def initialize_models(tts_method, asr_method, diarization):
    """
    Initialize required models.
    Only initialize models on first call to avoid redundant loading.
    """
    # Use global state to track initialized models
    global models_initialized

    with ThreadPoolExecutor() as executor:
        try:
            # Demucs model initialization
            if not models_initialized['demucs']:
                executor.submit(init_demucs)
                models_initialized['demucs'] = True
                logger.info("Demucs model initialization complete")
            else:
                logger.info("Demucs model already initialized, skipping")

            # TTS model initialization
            if tts_method == 'xtts' and not models_initialized['xtts']:
                executor.submit(init_TTS)
                models_initialized['xtts'] = True
                logger.info("XTTS model initialization complete")
            elif tts_method == 'cosyvoice' and not models_initialized['cosyvoice']:
                executor.submit(init_cosyvoice)
                models_initialized['cosyvoice'] = True
                logger.info("CosyVoice model initialization complete")

            # ASR model initialization
            if asr_method == 'WhisperX':
                if not models_initialized['whisperx']:
                    executor.submit(init_whisperx)
                    models_initialized['whisperx'] = True
                    logger.info("WhisperX model initialization complete")
                if diarization and not models_initialized['diarize']:
                    executor.submit(init_diarize)
                    models_initialized['diarize'] = True
                    logger.info("Diarize model initialization complete")
            elif asr_method == 'FunASR' and not models_initialized['funasr']:
                executor.submit(init_funasr)
                models_initialized['funasr'] = True
                logger.info("FunASR model initialization complete")

        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(f"Failed to initialize model: {str(e)}\n{stack_trace}")
            # Reset initialization state on error
            models_initialized = {key: False for key in models_initialized}
            release_model()  # Release loaded models
            raise


def process_video(info, root_folder, resolution,
                  demucs_model, device, shifts,
                  asr_method, whisper_model, batch_size, diarization, whisper_min_speakers, whisper_max_speakers,
                  translation_method, translation_target_language,
                  tts_method, tts_target_language, voice,
                  subtitles, speed_up, fps, background_music, bgm_volume, video_volume,
                  target_resolution, max_retries, progress_callback=None):
    """
    Full workflow for processing a single video, with progress callback.

    Args:
        progress_callback: Callback function to report progress and status, format: progress_callback(progress_percent, status_message)
    """
    local_time = time.localtime()

    # Define progress stages and weights
    stages = [
        ("Downloading video...", 10),  # 10%
        ("Vocal separation...", 15),  # 15%
        ("AI speech recognition...", 20),  # 20%
        ("Subtitle translation...", 25),  # 25%
        ("AI speech synthesis...", 20),  # 20%
        ("Video synthesis...", 10)  # 10%
    ]

    current_stage = 0
    progress_base = 0

    # Report initial progress
    if progress_callback:
        progress_callback(0, "Preparing to process...")

    for retry in range(max_retries):
        try:
            # Report entry to download stage
            stage_name, stage_weight = stages[current_stage]
            if progress_callback:
                progress_callback(progress_base, stage_name)

            if isinstance(info, str) and info.endswith('.mp4'):
                folder = os.path.dirname(info)
                # os.rename(info, os.path.join(folder, 'download.mp4'))
            else:
                folder = get_target_folder(info, root_folder)
                if folder is None:
                    error_msg = f'Could not get video target folder: {info["title"]}'
                    logger.warning(error_msg)
                    return False, None, error_msg

                folder = download_single_video(info, root_folder, resolution)
                if folder is None:
                    error_msg = f'Failed to download video: {info["title"]}'
                    logger.warning(error_msg)
                    return False, None, error_msg

            logger.info(f'Processing video: {folder}')

            # Finish download stage, enter vocal separation stage
            current_stage += 1
            progress_base += stage_weight
            stage_name, stage_weight = stages[current_stage]
            if progress_callback:
                progress_callback(progress_base, stage_name)

            try:
                status, vocals_path, _ = separate_all_audio_under_folder(
                    folder, model_name=demucs_model, device=device, progress=True, shifts=shifts)
                logger.info(f'Vocal separation complete: {vocals_path}')
            except Exception as e:
                stack_trace = traceback.format_exc()
                error_msg = f'Vocal separation failed: {str(e)}\n{stack_trace}'
                logger.error(error_msg)
                return False, None, error_msg

            # Finish vocal separation stage, enter ASR stage
            current_stage += 1
            progress_base += stage_weight
            stage_name, stage_weight = stages[current_stage]
            if progress_callback:
                progress_callback(progress_base, stage_name)

            try:
                status, result_json = transcribe_all_audio_under_folder(
                    folder, asr_method=asr_method, whisper_model_name=whisper_model, device=device,
                    batch_size=batch_size, diarization=diarization,
                    min_speakers=whisper_min_speakers,
                    max_speakers=whisper_max_speakers)
                logger.info(f'Speech recognition complete: {status}')
            except Exception as e:
                stack_trace = traceback.format_exc()
                error_msg = f'Speech recognition failed: {str(e)}\n{stack_trace}'
                logger.error(error_msg)
                return False, None, error_msg

            # Finish ASR stage, enter translation stage
            current_stage += 1
            progress_base += stage_weight
            stage_name, stage_weight = stages[current_stage]
            if progress_callback:
                progress_callback(progress_base, stage_name)

            try:
                status, summary, translation = translate_all_transcript_under_folder(
                    folder, method=translation_method, target_language=translation_target_language)
                logger.info(f'Translation complete: {status}')
            except Exception as e:
                stack_trace = traceback.format_exc()
                error_msg = f'Translation failed: {str(e)}\n{stack_trace}'
                logger.error(error_msg)
                return False, None, error_msg

            # Finish translation stage, enter TTS stage
            current_stage += 1
            progress_base += stage_weight
            stage_name, stage_weight = stages[current_stage]
            if progress_callback:
                progress_callback(progress_base, stage_name)

            try:
                status, synth_path, _ = generate_all_wavs_under_folder(
                    folder, method=tts_method, target_language=tts_target_language, voice=voice)
                logger.info(f'Speech synthesis complete: {synth_path}')
            except Exception as e:
                stack_trace = traceback.format_exc()
                error_msg = f'Speech synthesis failed: {str(e)}\n{stack_trace}'
                logger.error(error_msg)
                return False, None, error_msg

            # Finish TTS stage, enter video synthesis stage
            current_stage += 1
            progress_base += stage_weight
            stage_name, stage_weight = stages[current_stage]
            if progress_callback:
                progress_callback(progress_base, stage_name)

            try:
                status, output_video = synthesize_all_video_under_folder(
                    folder, subtitles=subtitles, speed_up=speed_up, fps=fps, resolution=target_resolution,
                    background_music=background_music, bgm_volume=bgm_volume, video_volume=video_volume)
                logger.info(f'Video synthesis complete: {output_video}')
            except Exception as e:
                stack_trace = traceback.format_exc()
                error_msg = f'Video synthesis failed: {str(e)}\n{stack_trace}'
                logger.error(error_msg)
                return False, None, error_msg

            # Finish all stages, report 100% progress
            if progress_callback:
                progress_callback(100, "Processing complete!")

            return True, output_video, "Processing successful"
        except Exception as e:
            stack_trace = traceback.format_exc()
            error_msg = f'Error occurred during video processing {info["title"] if isinstance(info, dict) else info}: {str(e)}\n{stack_trace}'
            logger.error(error_msg)
            if retry < max_retries - 1:
                logger.info(f'Attempting retry {retry + 2}/{max_retries}...')
            else:
                return False, None, error_msg

    return False, None, f"Reached maximum retry count: {max_retries}"


def do_everything(root_folder, url, num_videos=5, resolution='1080p',
                  demucs_model='htdemucs_ft', device='auto', shifts=5,
                  asr_method='WhisperX', whisper_model='large', batch_size=32, diarization=False,
                  whisper_min_speakers=None, whisper_max_speakers=None,
                  translation_method='LLM', translation_target_language='Simplified Chinese',
                  tts_method='xtts', tts_target_language='Chinese', voice='zh-CN-XiaoxiaoNeural',
                  subtitles=True, speed_up=1.00, fps=30,
                  background_music=None, bgm_volume=0.5, video_volume=1.0, target_resolution='1080p',
                  max_workers=3, max_retries=5, progress_callback=None):
    """
    Main entry point to process entire video workflow, with progress callback.

    Args:
        progress_callback: Callback function to report progress and status, format: progress_callback(progress_percent, status_message)
    """
    try:
        success_list = []
        fail_list = []
        error_details = []

        # Log task start and all parameters
        logger.info("-" * 50)
        logger.info(f"Starting task: {url}")
        logger.info(f"Params: Output Folder={root_folder}, Video Count={num_videos}, Resolution={resolution}")
        logger.info(f"Vocal Separation: Model={demucs_model}, Device={device}, Shifts={shifts}")
        logger.info(f"Speech Recognition: Method={asr_method}, Model={whisper_model}, Batch Size={batch_size}")
        logger.info(f"Translation: Method={translation_method}, Target Language={translation_target_language}")
        logger.info(f"Speech Synthesis: Method={tts_method}, Target Language={tts_target_language}, Voice={voice}")
        logger.info(f"Video Synthesis: Subtitles={subtitles}, Speed={speed_up}, FPS={fps}, Resolution={target_resolution}")
        logger.info("-" * 50)

        url = url.replace(' ', '').replace('，', '\n').replace(',', '\n')
        urls = [_ for _ in url.split('\n') if _]

        # Initialize models
        try:
            if progress_callback:
                progress_callback(5, "Initializing models...")
            initialize_models(tts_method, asr_method, diarization)
        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(f"Failed to initialize models: {str(e)}\n{stack_trace}")
            return f"Failed to initialize models: {str(e)}", None

        out_video = None
        if url.endswith('.mp4'):
            try:
                import shutil
                # Get original video filename (without path)
                original_file_name = os.path.basename(url)

                # Remove extension to generate folder name
                new_folder_name = os.path.splitext(original_file_name)[0]

                # Build full path of new folder
                new_folder_path = os.path.join(root_folder, new_folder_name)

                # Create folder under root_folder
                os.makedirs(new_folder_path, exist_ok=True)

                # Build full path of original file
                original_file_path = os.path.join(root_folder, original_file_name)

                # Build full path of new location
                new_file_path = os.path.join(new_folder_path, "download.mp4")

                # Copy video file to new folder and rename
                shutil.copy(original_file_path, new_file_path)
                # Create folder under root_folder
                os.makedirs(new_folder_path, exist_ok=True)

                success, output_video, error_msg = process_video(
                    new_file_path, root_folder, resolution,
                    demucs_model, device, shifts,
                    asr_method, whisper_model, batch_size, diarization, whisper_min_speakers, whisper_max_speakers,
                    translation_method, translation_target_language,
                    tts_method, tts_target_language, voice,
                    subtitles, speed_up, fps, background_music, bgm_volume, video_volume,
                    target_resolution, max_retries, progress_callback
                )

                if success:
                    logger.info(f"Video processing successful: {new_file_path}")
                    return 'Processing successful', output_video
                else:
                    logger.error(f"Video processing failed: {new_file_path}, Error: {error_msg}")
                    return f'Processing failed: {error_msg}', None
            except Exception as e:
                stack_trace = traceback.format_exc()
                logger.error(f"Failed to process local video: {str(e)}\n{stack_trace}")
                return f"Failed to process local video: {str(e)}", None
        else:
            try:
                videos_info = []
                if progress_callback:
                    progress_callback(10, "Fetching video information...")

                for video_info in get_info_list_from_url(urls, num_videos):
                    videos_info.append(video_info)

                if not videos_info:
                    return "Failed to fetch video information, please check URL", None

                for info in videos_info:
                    try:
                        success, output_video, error_msg = process_video(
                            info, root_folder, resolution,
                            demucs_model, device, shifts,
                            asr_method, whisper_model, batch_size, diarization, whisper_min_speakers,
                            whisper_max_speakers,
                            translation_method, translation_target_language,
                            tts_method, tts_target_language, voice,
                            subtitles, speed_up, fps, background_music, bgm_volume, video_volume,
                            target_resolution, max_retries, progress_callback
                        )

                        if success:
                            success_list.append(info)
                            out_video = output_video
                            logger.info(f"Successfully processed video: {info['title'] if isinstance(info, dict) else info}")
                        else:
                            fail_list.append(info)
                            error_details.append(f"{info['title'] if isinstance(info, dict) else info}: {error_msg}")
                            logger.error(
                                f"Failed to process video: {info['title'] if isinstance(info, dict) else info}, Error: {error_msg}")
                    except Exception as e:
                        stack_trace = traceback.format_exc()
                        fail_list.append(info)
                        error_details.append(f"{info['title'] if isinstance(info, dict) else info}: {str(e)}")
                        logger.error(
                            f"Error processing video: {info['title'] if isinstance(info, dict) else info}, Error: {str(e)}\n{stack_trace}")
            except Exception as e:
                stack_trace = traceback.format_exc()
                logger.error(f"Failed to get video list: {str(e)}\n{stack_trace}")
                return f"Failed to get video list: {str(e)}", None

        # Log summary of processing results
        logger.info("-" * 50)
        logger.info(f"Processing complete: Successful={len(success_list)}, Failed={len(fail_list)}")
        if error_details:
            logger.info("Failure details:")
            for detail in error_details:
                logger.info(f"  - {detail}")

        return f'Successful: {len(success_list)}\nFailed: {len(fail_list)}', out_video

    except Exception as e:
        # Catch any errors in the overall process
        stack_trace = traceback.format_exc()
        error_msg = f"Error occurred during process: {str(e)}\n{stack_trace}"
        logger.error(error_msg)
        return error_msg, None


if __name__ == '__main__':
    do_everything(
        root_folder='videos',
        url='https://www.bilibili.com/video/BV1kr421M7vz/',
        translation_method='LLM',
        # translation_method = 'Google Translate', translation_target_language = 'Simplified Chinese',
    )