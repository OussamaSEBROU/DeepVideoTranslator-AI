import streamlit as st
import os
import assemblyai as aai
import google.generativeai as genai
from tempfile import NamedTemporaryFile
import base64
import streamlit.components.v1 as components
from moviepy.editor import VideoFileClip
import random
import langdetect

# Set up API keys (consider using environment variables for security)
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize AssemblyAI
aai.settings.api_key = ASSEMBLYAI_API_KEY

# Initialize Google Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Define supported languages
LANGUAGES = {
    "Arabic": "Arabic",
    "Chinese (Simplified)": "Chinese (Simplified)",
    "French": "French",
    "German": "German",
    "Hindi": "Hindi",
    "Italian": "Italian",
    "Japanese": "Japanese",
    "Korean": "Korean",
    "Portuguese": "Portuguese",
    "Russian": "Russian",
    "Spanish": "Spanish",
    "Swedish": "Swedish",
    "Turkish": "Turkish",
    "Vietnamese": "Vietnamese"
}

def check_video_duration(video_file):
    """
    Check if the video duration is 10 minutes or less
    """
    with NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(video_file.getvalue())
        tmp_file_path = tmp_file.name

    video = VideoFileClip(tmp_file_path)
    duration = video.duration
    video.close()
    os.unlink(tmp_file_path)

    return duration <= 600  # 600 seconds = 10 minutes

def transcribe_video(video_file):
    """
    Transcribe video and return subtitles as SRT
    """
    with NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(video_file.getvalue())
        tmp_file_path = tmp_file.name

    transcript = aai.Transcriber().transcribe(tmp_file_path)
    subtitles = transcript.export_subtitles_srt()

    os.unlink(tmp_file_path)
    return subtitles

def is_english(text):
    """
    Check if the given text is in English
    """
    try:
        return langdetect.detect(text) == 'en'
    except:
        return False

def translate_content(content, target_language):
    """
    Translate the content to the target language using Google Gemini
    """
    prompt = f"""Translate the following text to professional with high accuracy of understand context {target_language}. Keep all numbers, punctuation, and special characters unchanged. Only translate the words:

{content}

Translated text:"""

    generation_config = genai.GenerationConfig(
        temperature=0.4,
        top_p=1,
        top_k=1,)

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    response = model.generate_content(
        prompt,
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    return response.text

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

def get_random_wisdom():
    wisdoms = [
        "Patience is the companion of wisdom.",
        "The only true wisdom is in knowing you know nothing.",
        "Wisdom is the reward you get for a lifetime of listening when you'd have preferred to talk.",
        # ... (other wisdom quotes)
    ]
    return random.choice(wisdoms)

def main():
    st.set_page_config(page_title="Multi-Language Subtitle Translator", layout="wide")

    # Sidebar
    st.sidebar.title("Subtitle Translator")
    st.sidebar.markdown("---")

    # Instructions in sidebar
    with st.sidebar.expander("Help", expanded=True):
        st.markdown("""
        1. Upload your English video file (MP4, MOV, AVI, or MKV format, 10 minutes or less).
        2. Select the target language for translation.
        3. Click the 'Process Video' button.
        4. Wait for the processing to complete. You'll see some wisdom quotes while waiting.
        5. Download the generated subtitle files.
        6. Watch your video with the newly created subtitles in the preview player.
        7. For offline viewing, follow the instructions provided after processing.
        """)
        
    with st.sidebar.expander("About"):
        st.markdown("""
        ### Multi-Language Video Subtitle Translator

        This powerful application leverages cutting-edge AI technologies to streamline your video subtitling workflow:

        **Video Transcription**:
        Utilizing LLM AI's advanced speech recognition, we accurately transcribe your video content into text.

        **Multi-Language Translation**:
        Powered by LLM's AI, we offer translation into 15+ languages, including:
        - Arabic, Chinese, French, German, Hindi
        - Italian, Japanese, Korean, Portuguese, Russian
        - Spanish, Dutch, Swedish, Turkish, Vietnamese
        ...and more!

        **Key Features**:
        - Support for various video formats (MP4, MOV, AVI, MKV)
        - High-quality transcription and translation
        - User-friendly interface for easy language selection
        - Downloadable SRT files for both original and translated subtitles
        - Video with embedded subtitles for easy playback
        - Handles videos 10 Min!
        - Enhanced video player with subtitle support and customizable settings

        **Perfect for**:
        - Content creators expanding to international audiences
        - Educational institutions creating multilingual materials
        - Businesses localizing video content
        - Anyone needing quick, accurate video subtitles in multiple languages

        Created to make video content accessible across language barriers.

        © 2024 Subtitle Translator Team. All rights reserved.
        """)
        

    # Main area
    st.title("DeepTranslator - AI Video Translator")
    st.markdown("### Important: This app only works with English videos. Please ensure your video has English audio.")

    # File uploader
    uploaded_file = st.file_uploader("Choose an English video file (10 minutes or less)", type=["mp4", "mov", "avi", "mkv"], accept_multiple_files=False)

    # Language selection
    target_language = st.selectbox("Select target language for translation:", list(LANGUAGES.keys()))

    if uploaded_file is not None:
        file_name = os.path.splitext(uploaded_file.name)[0]

        # Check video duration
        if not check_video_duration(uploaded_file):
            st.error("The uploaded video exceeds the 10-minute limit. Please upload a shorter video.")
        else:
            if st.button("Process Video"):
                with st.spinner(f"Processing video and translating to {target_language}... This may take a while."):
                    # Display random wisdoms during processing
                    wisdom_placeholder = st.empty()
                    for _ in range(30):  # Display 30 wisdoms
                        wisdom_placeholder.info(f"While you wait... {get_random_wisdom()}")
                        #st.sleep(3)  # Wait for 3 seconds before showing the next wisdom

                    # Transcribe video
                    subtitles = transcribe_video(uploaded_file)

                    # Check if the subtitles are in English
                    if not is_english(subtitles):
                        wisdom_placeholder.empty()
                        st.error("The video appears to be in a language other than English. Please upload an English video.")
                        return

                    # Save original subtitles
                    original_subtitle_file = f"{file_name}_original.srt"
                    with open(original_subtitle_file, "w", encoding="utf-8") as f:
                        f.write(subtitles)

                    # Translate subtitles
                    translated_subtitles = translate_content(subtitles, LANGUAGES[target_language])

                    # Save translated subtitles
                    translated_subtitle_file = f"{file_name}_{target_language.lower().replace(' ', '_')}.srt"
                    with open(translated_subtitle_file, "w", encoding="utf-8") as f:
                        f.write(translated_subtitles)

                    wisdom_placeholder.empty()  # Remove the wisdom messages
                    st.success("Processing complete!")

                    # Download buttons
                    st.markdown(get_binary_file_downloader_html(original_subtitle_file, "Original Subtitles"), unsafe_allow_html=True)
                    st.markdown(get_binary_file_downloader_html(translated_subtitle_file, f"{target_language} Subtitles"), unsafe_allow_html=True)

                    # Display video with subtitles
                    st.subheader("Video Preview with Subtitles")
                    st.video(uploaded_file, subtitles=translated_subtitle_file)

                    # Instructions for offline viewing
                    st.markdown("""
                    ### Instructions for Offline Viewing:
                    1. Create a new folder on your computer (e.g., "Subtitled_Videos").
                    2. Download both the original video and the subtitle file you want to use.
                    3. Place both files in the folder you created. Make sure they have the same name (except for the file extension).
                    4. To watch with subtitles:
                       - Use VLC Media Player: Open the video, right-click > Subtitles > Add Subtitle File, and select the .srt file.
                       - Use Windows Media Player: It should automatically detect the subtitle file if it's in the same folder and has the same name as the video.
                    5. Enjoy your video with translated subtitles!
                    """)

    else:
        st.markdown("""
        ### Welcome to the Multi-Language Video Subtitle Translator!

        Upload your English video (10 minutes or less) and select a target language to get started. 

        We're excited to help you transcribe, translate, and watch your video with multilingual subtitles!
        """)

if __name__ == "__main__":
    main()
