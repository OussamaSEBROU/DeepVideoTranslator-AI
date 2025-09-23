import streamlit as st
import os
import google.generativeai as genai
from tempfile import NamedTemporaryFile
import base64
import random
import langdetect
import subprocess
import re

# Set up API keys (consider using environment variables for security)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Google Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

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

def format_time(seconds):
    """Formats seconds into SRT time format (HH:MM:SS,ms)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"

def create_srt_from_text(text, duration_seconds):
    """
    Creates a basic SRT string from plain text and total duration.
    Splits text into sentences and assigns approximate timings.
    """
    if not text:
        return ""

    # Split text into sentences or manageable chunks
    # This regex tries to split by common sentence endings, but keeps the delimiter.
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return ""

    srt_content = []
    num_sentences = len(sentences)
    time_per_sentence = duration_seconds / num_sentences if num_sentences > 0 else 0

    for i, sentence in enumerate(sentences):
        start_time_seconds = i * time_per_sentence
        end_time_seconds = (i + 1) * time_per_sentence

        # Ensure end time doesn't exceed total duration
        if end_time_seconds > duration_seconds:
            end_time_seconds = duration_seconds

        start_time_str = format_time(start_time_seconds)
        end_time_str = format_time(end_time_seconds)

        srt_content.append(f"{i + 1}")
        srt_content.append(f"{start_time_str} --> {end_time_str}")
        srt_content.append(sentence)
        srt_content.append("") # Empty line for next entry

    return "\n".join(srt_content)


def check_video_duration(video_file_path):
    """
    Check if the video duration is 10 minutes or less using ffprobe
    Returns duration in seconds.
    """
    try:
        command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                   "default=noprint_wrappers=1:nokey=1", video_file_path]
        duration_str = subprocess.check_output(command).decode().strip()
        duration = float(duration_str)
    except Exception as e:
        st.error(f"Error getting video duration: {e}")
        duration = 0
    return duration

def extract_audio_from_video(video_file_path, audio_output_path):
    """
    Extracts audio from a video file using ffmpeg.
    """
    command = [
        "ffmpeg",
        "-i", video_file_path,
        "-vn", # No video
        "-acodec", "libmp3lame", # Use MP3 codec
        "-q:a", "2", # VBR quality 2 (good quality)
        "-ar", "44100", # Audio sample rate
        "-ac", "1", # Mono audio
        audio_output_path
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Error extracting audio: {e.stderr.decode()}")
        return False

def transcribe_audio_with_gemini(audio_file_path):
    """
    Transcribe audio using Google Gemini API.
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        
        base64_audio_data = base64.b64encode(audio_bytes).decode('utf-8')

        # Construct the parts for the generateContent call
        parts = [
            {"text": "Transcribe the audio content of this file."},
            {"inlineData": {"mimeType": "audio/mpeg", "data": base64_audio_data}} # Use audio/mpeg for MP3
        ]

        # Call Gemini API
        response = model.generate_content(parts)
        
        return response.text
    except Exception as e:
        st.error(f"Error during Gemini transcription: {e}")
        return None

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
    prompt = f"""translate the full text to {target_language} with professional, high-quality translation. Keep all numbers, punctuation, and special characters unchanged. Only translate the words. Ensure the output format matches the input structure as much as possible (e.g., if it's an SRT, maintain the SRT format, otherwise just the text):

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

    try:
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        return response.text
    except Exception as e:
        st.error(f"Error during Gemini translation: {e}")
        return None

def burn_subtitles_into_video(video_path, subtitle_path, output_path):
    """
    Burns subtitles into a video using ffmpeg.
    """
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f'subtitles="{subtitle_path.replace("\\\\", "/")}"'
        "-c:a", "copy",
        output_path
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Error burning subtitles: {e.stderr.decode()}")
        return False

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
        "The greatest wisdom is to be kind.",
        "Knowing yourself is the beginning of all wisdom.",
        "It is the mark of an educated mind to be able to entertain a thought without accepting it.",
        "The wise man knows he is a fool, the fool thinks he is wise.",
        "Don't gain the world and lose your soul; wisdom is better than silver or gold.",
        "The true sign of intelligence is not knowledge but imagination.",
        "Science is organized knowledge. Wisdom is organized life.",
        "The art of being wise is the art of knowing what to overlook.",
        "Never confuse motion with action.",
        "The quieter you become, the more you can hear.",
        "The more I learn, the more I realize how much I don't know.",
        "Seek not to find the answer, but to understand the question.",
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
        st.markdown("This app was developed by Mr. Oussama SEBROU")
        st.markdown("""
        ### Multi-Language Video Subtitle Translator

        This powerful application leverages cutting-edge AI technologies to streamline your video subtitling workflow:

        **Video Transcription**:
        Utilizing Google Gemini's advanced speech recognition, we accurately transcribe your video content into text.

        **Multi-Language Translation**:
        Powered by Google Gemini AI, we offer translation into 15+ languages, including:
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
    st.warning("Note: Transcription is done using Google Gemini, which provides plain text. Subtitle timings are approximated based on video duration and sentence count, not word-level accuracy.")

    # File uploader
    uploaded_file = st.file_uploader("Choose an English video file (10 minutes or less)", type=["mp4", "mov", "avi", "mkv"], accept_multiple_files=False)

    # Language selection
    target_language = st.selectbox("Select target language for translation:", list(LANGUAGES.keys()))

    if uploaded_file is not None:
        file_name_base = os.path.splitext(uploaded_file.name)[0]

        # Save uploaded file to a temporary path for ffmpeg
        with NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_video_file:
            tmp_video_file.write(uploaded_file.getvalue())
            tmp_video_path = tmp_video_file.name

        # Check video duration
        video_duration = check_video_duration(tmp_video_path)
        if video_duration == 0 or video_duration > 600: # 600 seconds = 10 minutes
            st.error("The uploaded video exceeds the 10-minute limit or duration could not be determined. Please upload a shorter video.")
            os.unlink(tmp_video_path)
            return

        if st.button("Process Video"):
            with st.spinner(f"Processing video and translating to {target_language}... This may take a while."):
                # Display random wisdoms during processing
                wisdom_placeholder = st.empty()
                # Display 3 wisdoms during the entire process
                for _ in range(3):
                    wisdom_placeholder.info(f"While you wait... {get_random_wisdom()}")

                # Step 1: Extract audio
                audio_temp_file = NamedTemporaryFile(delete=False, suffix=".mp3")
                audio_temp_path = audio_temp_file.name
                audio_temp_file.close() # Close the file immediately so ffmpeg can write to it

                if not extract_audio_from_video(tmp_video_path, audio_temp_path):
                    wisdom_placeholder.empty()
                    st.error("Failed to extract audio from video.")
                    os.unlink(tmp_video_path)
                    os.unlink(audio_temp_path)
                    return

                # Step 2: Transcribe audio using Gemini
                transcribed_text = transcribe_audio_with_gemini(audio_temp_path)
                if transcribed_text is None:
                    wisdom_placeholder.empty()
                    st.error("Failed to transcribe audio using Gemini.")
                    os.unlink(tmp_video_path)
                    os.unlink(audio_temp_path)
                    return

                # Step 3: Create SRT from transcribed text
                original_subtitles = create_srt_from_text(transcribed_text, video_duration)

                # Check if the subtitles are in English
                if not is_english(transcribed_text): # Use transcribed_text for language detection
                    wisdom_placeholder.empty()
                    st.error("The video appears to be in a language other than English. Please upload an English video.")
                    os.unlink(tmp_video_path)
                    os.unlink(audio_temp_path)
                    return

                # Save original subtitles
                original_subtitle_file = f"{file_name_base}_original.srt"
                with open(original_subtitle_file, "w", encoding="utf-8") as f:
                    f.write(original_subtitles)

                # Step 4: Translate subtitles
                translated_subtitles = translate_content(original_subtitles, LANGUAGES[target_language])
                if translated_subtitles is None:
                    wisdom_placeholder.empty()
                    st.error("Failed to translate subtitles using Gemini.")
                    os.unlink(tmp_video_path)
                    os.unlink(audio_temp_path)
                    os.unlink(original_subtitle_file)
                    return

                # Save translated subtitles
                translated_subtitle_file = f"{file_name_base}_{target_language.lower().replace(' ', '_')}.srt"
                with open(translated_subtitle_file, "w", encoding="utf-8") as f:
                    f.write(translated_subtitles)

                # Step 5: Burn subtitles into video
                output_video_file = f"{file_name_base}_translated.mp4"
                if burn_subtitles_into_video(tmp_video_path, translated_subtitle_file, output_video_file):
                    st.success("Subtitles successfully burned into the video!")
                else:
                    st.error("Failed to burn subtitles into the video.")
                
                # Clean up temporary files
                os.unlink(tmp_video_path)
                os.unlink(audio_temp_path)

                wisdom_placeholder.empty()  # Remove the wisdom messages
                st.success("Processing complete!")

                # Download buttons
                st.markdown(get_binary_file_downloader_html(original_subtitle_file, "Original Subtitles"), unsafe_allow_html=True)
                st.markdown(get_binary_file_downloader_html(translated_subtitle_file, f"{target_language} Subtitles"), unsafe_allow_html=True)
                st.markdown(get_binary_file_downloader_html(output_video_file, "Video with Translated Subtitles"), unsafe_allow_html=True)

                # Display video with subtitles
                st.subheader("Video Preview with Subtitles")
                st.video(output_video_file)

                # Instructions for offline viewing
                st.markdown("""
                ### Instructions for Offline Viewing:
                1. Create a new folder on your computer (e.g., "Subtitled_Videos").
                2. Download both the original video and the subtitle file you want to use.
                3. Place both files in the folder you created. Make sure they have the same name (except for the file extension).
                4. To watch with subtitles:
                   - Use VLC Media Player: It should automatically detect the subtitle file if it's in the same folder and has the same name as the video.
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

