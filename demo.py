import streamlit as st
import requests
import json
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import base64
from io import BytesIO
from datetime import timedelta
import re

# Set the page configuration for a wider layout
st.set_page_config(layout="wide")

st.title("YouTube Video Translator")
st.markdown("Enter a YouTube video URL to translate its subtitles and audio.")

# User inputs
youtube_url = st.text_input("YouTube Video URL", placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ")
api_key = st.text_input("Gemini API Key", type="password")
target_language = st.selectbox(
    "Select Target Language",
    [
        "English", "Spanish", "French", "German", "Italian", "Portuguese",
        "Japanese", "Korean", "Chinese (Simplified)", "Russian", "Arabic"
    ]
)

# A mapping from language names to their common language codes for Gemini API and SRT files
LANGUAGE_CODES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese (Simplified)": "zh-CN",
    "Russian": "ru",
    "Arabic": "ar"
}

# Mapping for Gemini TTS voices
TTS_VOICES = {
    "en": "Kore",
    "es": "Puck",
    "fr": "Charon",
    "de": "Fenrir",
    "it": "Leda",
    "pt": "Orus",
    "ja": "Aoede",
    "ko": "Callirrhoe",
    "zh-CN": "Autonoe",
    "ru": "Iapetus",
    "ar": "Umbriel"
}

def get_video_id(url):
    """Extracts the video ID from a YouTube URL."""
    if "youtube.com/watch?v=" in url:
        return url.split("v=")[-1]
    return None

def format_time(seconds):
    """Formats seconds into SRT time format (HH:MM:SS,mmm)."""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def generate_translation(text, source_lang, target_lang, api_key):
    """Generates translated text using the Gemini API."""
    if not api_key:
        st.error("Please enter your Gemini API key.")
        return None

    # Construct the API request payload
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Translate the following text from {source_lang} to {target_lang}: {text}"
            }]
        }]
    }
    headers = {'Content-Type': 'application/json'}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        
        result = response.json()
        translated_text = result['candidates'][0]['content']['parts'][0]['text']
        return translated_text
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling Gemini API for translation: {e}")
        return None
    except (KeyError, IndexError) as e:
        st.error(f"Invalid response from Gemini API for translation: {e}")
        st.json(response.json()) # show response for debugging
        return None

def generate_tts(text, language_code, voice_name, api_key):
    """Generates audio from text using Gemini TTS API."""
    if not api_key:
        st.error("Please enter your Gemini API key.")
        return None

    payload = {
        "contents": [{
            "parts": [{ "text": text }]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name
                    }
                }
            }
        },
        "model": "gemini-2.5-flash-preview-tts"
    }

    headers = {'Content-Type': 'application/json'}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={api_key}"

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        result = response.json()
        audio_data_b64 = result['candidates'][0]['content']['parts'][0]['inlineData']['data']
        return base64.b64decode(audio_data_b64)
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling Gemini TTS API: {e}")
        return None
    except (KeyError, IndexError) as e:
        st.error(f"Invalid response from Gemini TTS API: {e}")
        st.json(response.json()) # show response for debugging
        return None

if st.button("Translate Video"):
    if not youtube_url:
        st.warning("Please enter a YouTube video URL.")
    elif not api_key:
        st.warning("Please enter your Gemini API key.")
    else:
        video_id = get_video_id(youtube_url)
        if not video_id:
            st.error("Invalid YouTube URL. Please provide a valid URL.")
        else:
            with st.spinner("Processing video and generating translations..."):
                try:
                    # Get the transcript
                    st.write("Fetching video transcript...")
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    
                    # Try to find a human-generated or auto-generated English transcript
                    try:
                        transcript = transcript_list.find_transcript(['en']).fetch()
                    except NoTranscriptFound:
                        # If no English transcript is found, try to find one in any available language and translate from there
                        st.warning("No English transcript found. Attempting to translate from a different language.")
                        # Find the first available transcript
                        transcript = transcript_list.find_transcript(transcript_list.find_transcript().language_code).fetch()

                    # Concatenate the transcript text
                    full_transcript = " ".join([entry['text'] for entry in transcript])

                    # Get the target language code
                    target_lang_code = LANGUAGE_CODES.get(target_language)
                    
                    # Translate the entire transcript (or a large chunk)
                    st.write("Translating transcript using Gemini...")
                    translated_text = generate_translation(
                        full_transcript,
                        "English",  # Assuming original is English, or we use the source lang code if we can detect it
                        target_language,
                        api_key
                    )
                    
                    if translated_text:
                        # Generate the translated audio
                        st.write("Generating translated audio...")
                        translated_audio = generate_tts(
                            translated_text,
                            target_lang_code,
                            TTS_VOICES.get(target_lang_code, "Kore"), # Fallback to a default voice
                            api_key
                        )

                        # Create the SRT subtitle file content
                        st.write("Generating translated subtitles (SRT file)...")
                        srt_content = ""
                        for i, entry in enumerate(transcript):
                            start_time_sec = entry['start']
                            end_time_sec = entry['start'] + entry['duration']
                            
                            # Translate the segment's text for the subtitle file
                            segment_text = entry['text']
                            translated_segment = generate_translation(
                                segment_text,
                                "English",
                                target_language,
                                api_key
                            )
                            
                            srt_content += f"{i + 1}\n"
                            srt_content += f"{format_time(start_time_sec)} --> {format_time(end_time_sec)}\n"
                            srt_content += f"{translated_segment}\n\n"

                        # Display results
                        st.success("Translation complete!")
                        st.subheader("Original Video")
                        st.video(youtube_url)

                        st.subheader("Translated Content")
                        st.write("Download the translated audio and subtitle files below. You can use these with a video player like VLC to watch the video with the new audio and subtitles.")

                        # Provide download button for the SRT file
                        srt_bytes = srt_content.encode('utf-8')
                        st.download_button(
                            label="Download Subtitle File (SRT)",
                            data=srt_bytes,
                            file_name=f"translated_subtitles_{target_lang_code}.srt",
                            mime="text/plain"
                        )

                        # Provide a download button for the audio file
                        if translated_audio:
                            st.download_button(
                                label="Download Translated Audio (PCM)",
                                data=translated_audio,
                                file_name=f"translated_audio_{target_lang_code}.pcm",
                                mime="audio/L16"
                            )

                except TranscriptsDisabled:
                    st.error("Transcripts are disabled for this video.")
                except NoTranscriptFound:
                    st.error("No transcript found for this video in any language.")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
                    st.stop()

# Instructions for running the app
st.markdown("""
---
### How to Run this Application:

1.  **Install Libraries:** Make sure you have Python installed. Then, open your terminal or command prompt and run:
    ```
    pip install streamlit youtube-transcript-api requests
    ```
2.  **Save the Code:** Save the code above as `app.py`.
3.  **Run the App:** In your terminal, navigate to the directory where you saved the file and run:
    ```
    streamlit run app.py
    ```
4.  **Open in Browser:** Your web browser will open and display the application.
""")

