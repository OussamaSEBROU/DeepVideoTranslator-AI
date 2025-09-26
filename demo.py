import streamlit as st
import os
import tempfile
import requests
import json
from pathlib import Path
import re
from typing import Optional
import google.generativeai as genai
from datetime import timedelta

# Configure page layout
st.set_page_config(
    page_title="YouTube URL Translator",
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

def extract_video_id_from_url(url: str) -> str:
    """Extract video ID from YouTube URL."""
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None

def extract_video_info_with_api(video_id: str, api_key: str) -> dict:
    """Use YouTube Data API to get video info."""
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={video_id}&key={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            item = data['items'][0]
            duration_seconds = parse_duration(item['contentDetails']['duration'])
            return {
                'title': item['snippet']['title'],
                'duration': duration_seconds,
                'thumbnail': item['snippet']['thumbnails']['high']['url'],
                'uploader': item['snippet']['channelTitle']
            }
        else:
            return {}
    except Exception as e:
        st.error(f"YouTube API Error: {str(e)}")
        return {}

def parse_duration(duration_str: str) -> int:
    """Convert ISO 8601 duration to seconds."""
    import re
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)
    if not match:
        return 0
    
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    
    return hours * 3600 + minutes * 60 + seconds

def process_youtube_url_with_gemini(youtube_url: str, target_language: str, gemini_api_key: str) -> str:
    """
    Pass YouTube URL directly to Gemini API as part of the request.
    Note: Gemini will treat this as text input, not actual video processing.
    """
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are given a YouTube video URL: {youtube_url}
        
        Please analyze this URL and provide a translation to {target_language} language.
        Since you cannot access the actual video content directly, 
        provide a general translation service description in {target_language}.
        
        If you had access to the video content, you would:
        1. Extract and transcribe the audio content
        2. Translate the transcription to {target_language} with high accuracy and contextual understanding
        3. Generate properly formatted subtitles
        
        For now, demonstrate your translation capability by providing a sample translation 
        in {target_language} that shows what the output would look like.
        
        Return only the translated content without any additional commentary.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        st.error(f"Error processing with Gemini: {str(e)}")
        return ""

def generate_srt_subtitles(text: str, duration: int) -> str:
    """Generate basic SRT subtitle file from text."""
    import re
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        sentences = [text]
    
    srt_content = []
    segment_duration = duration / len(sentences) if len(sentences) > 0 else duration
    
    for i, sentence in enumerate(sentences):
        if not sentence:
            continue
            
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, duration)
        
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
        
        ### Important Note:
        This app passes YouTube URLs directly to Gemini API.
        Gemini will process the URL as text input and provide 
        translated content based on its understanding.
        
        For actual video/audio processing, consider uploading 
        audio files directly.
        """)
        
        st.markdown("---")
        st.markdown("⚠️ **Limitation**: Gemini API cannot directly access YouTube video content from URLs.")

    # Main content
    st.title("🎥 YouTube URL Translator")
    st.markdown("Pass YouTube URLs directly to Gemini API for translation")
    
    # Get API keys from environment variables
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not gemini_api_key:
        st.error("❌ Gemini API key not found. Please configure GEMINI_API_KEY in Render environment variables.")
        st.stop()
    
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
        
        try:
            with st.spinner("Processing YouTube URL with Gemini API..."):
                # Extract video info if YouTube API key is available
                video_info = {}
                if youtube_api_key:
                    video_id = extract_video_id_from_url(youtube_url)
                    if video_id:
                        video_info = extract_video_info_with_api(video_id, youtube_api_key)
                        st.session_state.video_info = video_info
                
                # Pass YouTube URL directly to Gemini (as requested)
                st.info("Passing YouTube URL directly to Gemini API...")
                translated_text = process_youtube_url_with_gemini(youtube_url, target_language, gemini_api_key)
                
                if not translated_text:
                    st.error("Failed to get translation from Gemini")
                    return
                
                # Generate subtitles
                duration = video_info.get('duration', 300) if video_info else 300
                subtitle_content = generate_srt_subtitles(translated_text, duration)
                
                st.session_state.translated_text = translated_text
                st.session_state.subtitle_content = subtitle_content
                st.session_state.processed = True
                
                st.success("✅ Processing completed!")
                
        except Exception as e:
            st.error(f"An error occurred during processing: {str(e)}")
            return
    
    # Display results
    if st.session_state.processed:
        st.markdown("---")
        
        # Display video info if available
        if st.session_state.video_info:
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
        
        srt_filename = f"translated_subtitles_{target_language.lower()[:3]}.srt"
        st.download_button(
            label="⬇️ Download SRT Subtitles",
            data=st.session_state.subtitle_content,
            file_name=srt_filename,
            mime="text/plain",
            type="primary"
        )

if __name__ == "__main__":
    main()