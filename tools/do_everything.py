import json
import os
import time
import traceback

import torch
from loguru import logger
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

# Track model initialization status
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


def process_video(video_path, root_folder,
                  demucs_model, device, shifts,
                  asr_method, whisper_model, batch_size, diarization, whisper_min_speakers, whisper_max_speakers,
                  translation_method, translation_target_language,
                  tts_method, tts_target_language, voice,
                  subtitles, speed_up, fps, background_music, bgm_volume, video_volume,
                  target_resolution, max_retries, progress_callback=None):
    """
    Full workflow for processing a single local video, with progress callback.

    Args:
        progress_callback: Callback function to report progress and status, format: progress_callback(progress_percent, status_message)
    """
    # Define progress stages and weights
    stages = [
        ("Vocal separation...", 20),  # 20%
        ("AI speech recognition...", 25),  # 25%
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
            # Prepare folder for local video
            import shutil
            original_file_name = os.path.basename(video_path)
            new_folder_name = os.path.splitext(original_file_name)[0]
            folder = os.path.join(root_folder, new_folder_name)
            os.makedirs(folder, exist_ok=True)

            new_file_path = os.path.join(folder, "download.mp4")
            if not os.path.exists(new_file_path):
                logger.info(f"Copying {video_path} to {new_file_path}")
                shutil.copy(video_path, new_file_path)

            logger.info(f'Processing video in folder: {folder}')

            # Vocal separation stage
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
            error_msg = f'Error occurred during video processing {os.path.basename(video_path)}: {str(e)}\n{stack_trace}'
            logger.error(error_msg)
            if retry < max_retries - 1:
                logger.info(f'Attempting retry {retry + 2}/{max_retries}...')
            else:
                return False, None, error_msg

    return False, None, f"Reached maximum retry count: {max_retries}"


def do_everything(root_folder, video_path,
                  demucs_model='htdemucs_ft', device='auto', shifts=5,
                  asr_method='WhisperX', whisper_model='large', batch_size=32, diarization=False,
                  whisper_min_speakers=None, whisper_max_speakers=None,
                  translation_method='LLM', translation_target_language='Simplified Chinese',
                  tts_method='xtts', tts_target_language='Chinese', voice='zh-CN-XiaoxiaoNeural',
                  subtitles=True, speed_up=1.00, fps=30,
                  background_music=None, bgm_volume=0.5, video_volume=1.0, target_resolution='1080p',
                  max_retries=5, progress_callback=None):
    """
    Main entry point to process local video workflow, with progress callback.

    Args:
        progress_callback: Callback function to report progress and status, format: progress_callback(progress_percent, status_message)
    """
    try:
        # Log task start and all parameters
        logger.info("-" * 50)
        logger.info(f"Starting task with local video: {video_path}")
        logger.info(f"Params: Output Folder={root_folder}")
        logger.info(f"Vocal Separation: Model={demucs_model}, Device={device}, Shifts={shifts}")
        logger.info(f"Speech Recognition: Method={asr_method}, Model={whisper_model}, Batch Size={batch_size}")
        logger.info(f"Translation: Method={translation_method}, Target Language={translation_target_language}")
        logger.info(f"Speech Synthesis: Method={tts_method}, Target Language={tts_target_language}, Voice={voice}")
        logger.info(f"Video Synthesis: Subtitles={subtitles}, Speed={speed_up}, FPS={fps}, Resolution={target_resolution}")
        logger.info("-" * 50)

        # Initialize models
        try:
            if progress_callback:
                progress_callback(5, "Initializing models...")
            initialize_models(tts_method, asr_method, diarization)
        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(f"Failed to initialize models: {str(e)}\n{stack_trace}")
            return f"Failed to initialize models: {str(e)}", None

        success, output_video, error_msg = process_video(
            video_path, root_folder,
            demucs_model, device, shifts,
            asr_method, whisper_model, batch_size, diarization, whisper_min_speakers, whisper_max_speakers,
            translation_method, translation_target_language,
            tts_method, tts_target_language, voice,
            subtitles, speed_up, fps, background_music, bgm_volume, video_volume,
            target_resolution, max_retries, progress_callback
        )

        if success:
            logger.info(f"Video processing successful: {video_path}")
            return 'Processing successful', output_video
        else:
            logger.error(f"Video processing failed: {video_path}, Error: {error_msg}")
            return f'Processing failed: {error_msg}', None

    except Exception as e:
        # Catch any errors in the overall process
        stack_trace = traceback.format_exc()
        error_msg = f"Error occurred during process: {str(e)}\n{stack_trace}"
        logger.error(error_msg)
        return error_msg, None


if __name__ == '__main__':
    # Example local video processing
    do_everything(
        root_folder='videos',
        video_path='input_video.mp4',
        translation_method='LLM',
    )