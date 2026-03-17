import gradio as gr
from tools.step000_video_downloader import download_from_url
from tools.step010_demucs_vr import separate_all_audio_under_folder
from tools.step020_asr import transcribe_all_audio_under_folder
from tools.step030_translation import translate_all_transcript_under_folder
from tools.step040_tts import generate_all_wavs_under_folder
from tools.step050_synthesize_video import synthesize_all_video_under_folder
from tools.do_everything import do_everything
from tools.utils import SUPPORT_VOICE

# One-Click Automation Interface
full_auto_interface = gr.Interface(
    fn=do_everything,
    inputs=[
        gr.Textbox(label='Video Output Folder', value='videos'),
        gr.Textbox(label='Video URL', placeholder='Please enter the URL of a Youtube or Bilibili video, playlist, or channel',
                   value='https://www.bilibili.com/video/BV1kr421M7vz/'),
        gr.Slider(minimum=1, maximum=100, step=1, label='Number of Videos to Download', value=5),
        gr.Radio(['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'], label='Resolution', value='1080p'),

        gr.Radio(['htdemucs', 'htdemucs_ft', 'htdemucs_6s', 'hdemucs_mmi', 'mdx', 'mdx_extra', 'mdx_q', 'mdx_extra_q', 'SIG'], label='Model', value='htdemucs_ft'),
        gr.Radio(['auto', 'cuda', 'cpu'], label='Compute Device', value='auto'),
        gr.Slider(minimum=0, maximum=10, step=1, label='Number of Shifts', value=5),

        gr.Dropdown(['WhisperX', 'FunASR'], label='ASR Model Selection', value='WhisperX'),
        gr.Radio(['large', 'medium', 'small', 'base', 'tiny'], label='WhisperX Model Size', value='large'),
        gr.Slider(minimum=1, maximum=128, step=1, label='Batch Size', value=32),
        gr.Checkbox(label='Separate Multiple Speakers', value=True),
        gr.Radio([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], label='Min Speakers', value=None),
        gr.Radio([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], label='Max Speakers', value=None),

        gr.Dropdown(['OpenAI', 'LLM', 'Google Translate', 'Bing Translate', 'Ernie'], label='Translation Method', value='LLM'),
        gr.Dropdown(['Simplified Chinese', 'Traditional Chinese', 'English', 'Cantonese', 'Japanese', 'Korean', 'Romanian'], label='Target Language (Translation)', value='Simplified Chinese'),

        gr.Dropdown(['xtts', 'cosyvoice', 'EdgeTTS'], label='AI Speech Generation Method', value='xtts'),
        gr.Dropdown(['Chinese', 'English', 'Cantonese', 'Japanese', 'Korean', 'Spanish', 'French', 'Romanian'], label='Target Language (TTS)', value='Chinese'),
        gr.Dropdown(SUPPORT_VOICE, value='zh-CN-XiaoxiaoNeural', label='EdgeTTS Voice Selection'),

        gr.Checkbox(label='Add Subtitles', value=True),
        gr.Slider(minimum=0.5, maximum=2, step=0.05, label='Speed Factor', value=1.00),
        gr.Slider(minimum=1, maximum=60, step=1, label='Frame Rate', value=30),
        gr.Audio(label='Background Music', sources=['upload']),
        gr.Slider(minimum=0, maximum=1, step=0.05, label='BGM Volume', value=0.5),
        gr.Slider(minimum=0, maximum=1, step=0.05, label='Video Volume', value=1.0),
        gr.Radio(['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'], label='Resolution', value='1080p'),

        gr.Slider(minimum=1, maximum=100, step=1, label='Max Workers', value=1),
        gr.Slider(minimum=1, maximum=10, step=1, label='Max Retries', value=3),
    ],
    outputs=[gr.Text(label='Synthesis Status'), gr.Video(label='Sample Result Video')],
    allow_flagging='never',
)    

# Video Download Interface
download_interface = gr.Interface(
    fn=download_from_url,
    inputs=[
        gr.Textbox(label='Video URL', placeholder='Please enter the URL of a Youtube or Bilibili video, playlist, or channel',
                   value='https://www.bilibili.com/video/BV1kr421M7vz/'),
        gr.Textbox(label='Video Output Folder', value='videos'),
        gr.Radio(['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'], label='Resolution', value='1080p'),
        gr.Slider(minimum=1, maximum=100, step=1, label='Number of Videos to Download', value=5),
        # gr.Checkbox(label='Single Video', value=False),
    ],
    outputs=[
        gr.Textbox(label='Download Status'),
        gr.Video(label='Example Video'),
        gr.Json(label='Download Information')
    ],
    allow_flagging='never',
)

# Vocal Separation Interface
demucs_interface = gr.Interface(
    fn=separate_all_audio_under_folder,
    inputs=[
        gr.Textbox(label='Video Folder', value='videos'),
        gr.Radio(['htdemucs', 'htdemucs_ft', 'htdemucs_6s', 'hdemucs_mmi', 'mdx', 'mdx_extra', 'mdx_q', 'mdx_extra_q', 'SIG'], label='Model', value='htdemucs_ft'),
        gr.Radio(['auto', 'cuda', 'cpu'], label='Compute Device', value='auto'),
        gr.Checkbox(label='Show Progress Bar', value=True),
        gr.Slider(minimum=0, maximum=10, step=1, label='Number of Shifts', value=5),
    ],
    outputs=[
        gr.Text(label='Separation Status'),
        gr.Audio(label='Vocals'),
        gr.Audio(label='Accompaniment')
    ],
    allow_flagging='never',
)

# AI Speech Recognition Interface
asr_inference = gr.Interface(
    fn=transcribe_all_audio_under_folder,
    inputs=[
        gr.Textbox(label='Video Folder', value='videos'),
        gr.Dropdown(['WhisperX', 'FunASR'], label='ASR Model Selection', value='WhisperX'),
        gr.Radio(['large', 'medium', 'small', 'base', 'tiny'], label='WhisperX Model Size', value='large'),
        gr.Radio(['auto', 'cuda', 'cpu'], label='Compute Device', value='auto'),
        gr.Slider(minimum=1, maximum=128, step=1, label='Batch Size', value=32),
        gr.Checkbox(label='Separate Multiple Speakers', value=True),
        gr.Radio([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], label='Min Speakers', value=None),
        gr.Radio([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], label='Max Speakers', value=None),
    ],
    outputs=[
        gr.Text(label='ASR Status'),
        gr.Json(label='Recognition Details')
    ],
    allow_flagging='never',
)

# Subtitle Translation Interface
translation_interface = gr.Interface(
    fn=translate_all_transcript_under_folder,
    inputs=[
        gr.Textbox(label='Video Folder', value='videos'),
        gr.Dropdown(['OpenAI', 'LLM', 'Google Translate', 'Bing Translate', 'Ernie'], label='Translation Method', value='LLM'),
        gr.Dropdown(['Simplified Chinese', 'Traditional Chinese', 'English', 'Cantonese', 'Japanese', 'Korean', 'Romanian'], label='Target Language', value='Simplified Chinese'),
    ],
    outputs=[
        gr.Text(label='Translation Status'),
        gr.Json(label='Summary Result'),
        gr.Json(label='Translation Result')
    ],
    allow_flagging='never',
)

# AI Speech Synthesis Interface
tts_interface = gr.Interface(
    fn=generate_all_wavs_under_folder,
    inputs=[
        gr.Textbox(label='Video Folder', value='videos'),
        gr.Dropdown(['xtts', 'cosyvoice', 'EdgeTTS'], label='AI Speech Generation Method', value='xtts'),
        gr.Dropdown(['Chinese', 'English', 'Cantonese', 'Japanese', 'Korean', 'Spanish', 'French', 'Romanian'], label='Target Language', value='Chinese'),
        gr.Dropdown(SUPPORT_VOICE, value='zh-CN-XiaoxiaoNeural', label='EdgeTTS Voice Selection'),
    ],
    outputs=[
        gr.Text(label='Synthesis Status'),
        gr.Audio(label='Synthesized Speech'),
        gr.Audio(label='Original Audio')
    ],
    allow_flagging='never',
)

# Video Synthesis Interface
synthesize_video_interface = gr.Interface(
    fn=synthesize_all_video_under_folder,
    inputs=[
        gr.Textbox(label='Video Folder', value='videos'),
        gr.Checkbox(label='Add Subtitles', value=True),
        gr.Slider(minimum=0.5, maximum=2, step=0.05, label='Speed Factor', value=1.00),
        gr.Slider(minimum=1, maximum=60, step=1, label='Frame Rate', value=30),
        gr.Audio(label='Background Music', sources=['upload'], type='filepath'),
        gr.Slider(minimum=0, maximum=1, step=0.05, label='BGM Volume', value=0.5),
        gr.Slider(minimum=0, maximum=1, step=0.05, label='Video Volume', value=1.0),
        gr.Radio(['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'], label='Resolution', value='1080p'),

    ],
    outputs=[
        gr.Text(label='Synthesis Status'),
        gr.Video(label='Synthesized Video')
    ],
    allow_flagging='never',
)

linly_talker_interface = gr.Interface(
    fn=lambda: None,
    inputs=[
        gr.Textbox(label='Video Folder', value='videos'),
        gr.Dropdown(['Wav2Lip', 'Wav2Lipv2','SadTalker'], label='AI Dubbing Method', value='Wav2Lip'),
    ],      
    outputs=[
        gr.Markdown(value="Under construction, please stay tuned. Refer to [https://github.com/Kedreamix/Linly-Talker](https://github.com/Kedreamix/Linly-Talker)"),
        gr.Text(label='Synthesis Status'),
        gr.Video(label='Synthesized Video')
    ],
)

my_theme = gr.themes.Soft()
# Application Interface
app = gr.TabbedInterface(
    theme=my_theme,
    interface_list=[
        full_auto_interface,
        download_interface,
        demucs_interface,
        asr_inference,
        translation_interface,
        tts_interface,
        synthesize_video_interface,
        linly_talker_interface
    ],
    tab_names=[
        'One-Click Automation',
        'Automatic Video Download', 'Vocal Separation', 'AI Speech Recognition', 'Subtitle Translation', 'AI Speech Synthesis', 'Video Synthesis',
        'Linly-Talker Lip-Sync (Developing)'],
    title='Intelligent Multi-language AI Dubbing/Translation Tool - Linly-Dubbing'
)

if __name__ == '__main__':
    app.launch(
        server_name="127.0.0.1", 
        server_port=6006,
        share=True,
        inbrowser=True
    )