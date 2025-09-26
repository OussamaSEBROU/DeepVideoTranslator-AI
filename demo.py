import streamlit as st
import os
import tempfile
import requests
import json
from pathlib import Path
import re
from typing import List, Tuple, Optional
import yt_dlp
import subprocess
import google.generativeai as genai
from datetime import timedelta

# Configure page layout
st.set_page_config(
    page_title="YouTube Translator & Subtitle Generator",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = ""
if 'subtitle_content' not in st.session_state:
    st.session_state.subtitle_content = ""
if 'video_info' not in st.session_state:
    st.session_state.video_info = {}

def validate_youtube_url(url: str) -> bool:
    """Validate if the URL is a valid YouTube URL."""
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(re.match(youtube_regex, url))

def extract_video_info(url: str) -> dict:
    """Extract basic video information using yt-dlp."""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown Channel')
            }
    except Exception as e:
        st.error(f"Error extracting video info: {str(e)}")
        return {}

def download_audio_from_youtube(url: str, temp_dir: str) -> Optional[str]:
    """Download audio from YouTube video and save as MP3."""
    try:
        audio_path = os.path.join(temp_dir, "audio.mp3")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_path.replace('.mp3', ''),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return audio_path if os.path.exists(audio_path) else None
    except Exception as e:
        st.error(f"Error downloading audio: {str(e)}")
        return None

def transcribe_audio_with_gemini(audio_path: str, gemini_api_key: str) -> str:
    """Transcribe audio using Gemini API."""
    try:
        genai.configure(api_key=gemini_api_key)
        
        # Upload audio file to Gemini
        audio_file = genai.upload_file(path=audio_path)
        
        # Wait for processing
        while audio_file.state.name == "PROCESSING":
            audio_file = genai.get_file(audio_file.name)
        
        if audio_file.state.name == "FAILED":
            raise ValueError("Audio processing failed")
        
        # Generate transcription
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([
            "Transcribe this audio file accurately. Return only the transcribed text without any additional commentary.",
            audio_file
        ])
        
        return response.text.strip()
        
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return ""

def translate_text_with_gemini(text: str, target_language: str, gemini_api_key: str) -> str:
    """Translate text to target language using Gemini API."""
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Translate the following text to {target_language}. 
        Maintain the original meaning and context.
        Return only the translated text without any additional commentary or formatting.
        
        Text to translate:
        {text}
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        st.error(f"Error translating text: {str(e)}")
        return ""

def generate_srt_subtitles(text: str, duration: int) -> str:
    """Generate basic SRT subtitle file from text."""
    # This is a simplified approach - in production, you'd want proper sentence segmentation
    # and timing based on actual speech patterns
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    if not sentences:
        sentences = [text]
    
    srt_content = []
    segment_duration = duration / len(sentences) if sentences else duration
    
    for i, sentence in enumerate(sentences):
        if not sentence:
            continue
            
        start_time = i * segment_duration
        end_time = (i + 1) * segment_duration
        
        # Format time as HH:MM:SS,mmm
        def format_time(seconds):
            td = timedelta(seconds=seconds)
            hours, remainder = divmod(td.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{int(td.microseconds/1000):03d}"
        
        srt_entry = f"{i+1}\n{format_time(start_time)} --> {format_time(end_time)}\n{sentence.strip()}\n"
        srt_content.append(srt_entry)
    
    return "\n".join(srt_content)

def main():
    """Main Streamlit application."""
    
    # Sidebar
    with st.sidebar:
        st.title("ℹ️ Instructions")
        st.markdown("""
        ### How to use this app:
        
        1. **Enter YouTube URL**: Paste a valid YouTube video URL
        2. **Select Language**: Choose your target translation language
        3. **Click Process**: Press "Translate & Generate" to start
        4. **Download**: Get your translated subtitles as .srt file
        
        ### Supported Languages:
        - Spanish
        - French  
        - German
        - Portuguese
        - Italian
        - Dutch
        - Russian
        - Chinese
        - Japanese
        - Korean
        - Arabic
        - Hindi
        
        ### About
        This app uses Google's Gemini API to transcribe and translate YouTube video content. 
        Audio extraction is handled by yt-dlp, and subtitles are generated in SRT format.
        """)
        
        st.markdown("---")
        st.markdown("⚠️ **Note**: Processing time depends on video length. Please be patient!")

    # Main content
    st.title("🎥 YouTube Translator & Subtitle Generator")
    st.markdown("Transform YouTube videos into multilingual content with AI-powered translation")
    
    # API Key input (hidden for security in production)
    gemini_api_key = st.text_input(
        "Enter your Gemini API Key", 
        type="password",
        help="Your Gemini API key is required for transcription and translation"
    )
    
    if not gemini_api_key:
        st.warning("Please enter your Gemini API key to proceed.")
        return
    
    # Input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        youtube_url = st.text_input(
            "YouTube Video URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste the full YouTube URL here"
        )
    
    with col2:
        languages = [
            "Spanish", "French", "German", "Portuguese", "Italian", 
            "Dutch", "Russian", "Chinese", "Japanese", "Korean", 
            "Arabic", "Hindi"
        ]
        target_language = st.selectbox(
            "Target Language",
            languages,
            help="Select the language for translation"
        )
    
    # Validation
    if youtube_url and not validate_youtube_url(youtube_url):
        st.error("❌ Please enter a valid YouTube URL")
        return
    
    # Process button
    if st.button("🚀 Translate & Generate", type="primary", use_container_width=True):
        if not youtube_url:
            st.error("Please enter a YouTube URL")
            return
        
        if not gemini_api_key:
            st.error("Please enter your Gemini API key")
            return
        
        try:
            with st.spinner("Processing... This may take several minutes"):
                # Create temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Extract video info
                    st.info("Extracting video information...")
                    video_info = extract_video_info(youtube_url)
                    st.session_state.video_info = video_info
                    
                    if not video_info:
                        st.error("Failed to extract video information")
                        return
                    
                    # Download audio
                    st.info("Downloading audio...")
                    audio_path = download_audio_from_youtube(youtube_url, temp_dir)
                    if not audio_path:
                        st.error("Failed to download audio")
                        return
                    
                    # Transcribe audio
                    st.info("Transcribing audio...")
                    original_text = transcribe_audio_with_gemini(audio_path, gemini_api_key)
                    if not original_text:
                        st.error("Failed to transcribe audio")
                        return
                    
                    # Translate text
                    st.info("Translating to selected language...")
                    translated_text = translate_text_with_gemini(
                        original_text, 
                        target_language, 
                        gemini_api_key
                    )
                    if not translated_text:
                        st.error("Failed to translate text")
                        return
                    
                    # Generate subtitles
                    st.info("Generating subtitles...")
                    duration = video_info.get('duration', 300)  # Default 5 minutes if not available
                    subtitle_content = generate_srt_subtitles(translated_text, duration)
                    
                    # Store in session state
                    st.session_state.translated_text = translated_text
                    st.session_state.subtitle_content = subtitle_content
                    st.session_state.processed = True
                    
                    st.success("✅ Processing completed successfully!")
                    
        except Exception as e:
            st.error(f"An error occurred during processing: {str(e)}")
            return
    
    # Display results
    if st.session_state.processed:
        st.markdown("---")
        st.subheader("🎬 Video Information")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.session_state.video_info.get('thumbnail'):
                st.image(st.session_state.video_info['thumbnail'], width=200)
        
        with col2:
            st.markdown(f"**Title:** {st.session_state.video_info.get('title', 'N/A')}")
            st.markdown(f"**Channel:** {st.session_state.video_info.get('uploader', 'N/A')}")
            duration = st.session_state.video_info.get('duration', 0)
            if duration > 0:
                minutes, seconds = divmod(duration, 60)
                st.markdown(f"**Duration:** {minutes}:{seconds:02d}")
        
        st.markdown("---")
        st.subheader(f"🌍 Translated Content ({target_language})")
        st.text_area(
            "Translated Text",
            st.session_state.translated_text,
            height=200,
            disabled=True
        )
        
        st.markdown("---")
        st.subheader("📥 Download Subtitles")
        
        # Download button for SRT file
        srt_filename = f"translated_subtitles_{target_language.lower()[:3]}.srt"
        st.download_button(
            label="⬇️ Download SRT Subtitles",
            data=st.session_state.subtitle_content,
            file_name=srt_filename,
            mime="text/plain",
            type="primary"
        )
        
        # Display sample of subtitles
        st.markdown("**Preview of generated subtitles:**")
        preview_lines = st.session_state.subtitle_content.split('\n')[:10]
        st.code('\n'.join(preview_lines), language='srt')

if __name__ == "__main__":
    main()