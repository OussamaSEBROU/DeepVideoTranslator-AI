import streamlit as st
import google.generativeai as genai
import pytube
import textwrap
import time

# --- Configuration and API Key Handling ---
st.set_page_config(
    page_title="Gemini-Powered YouTube Translator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Place the API key input at the top of the main page for clarity
api_key = st.text_input(
    "Gemini API Key",
    type="password",
    placeholder="Enter your Gemini API key here"
)

# Configure the API key only if it is provided
if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("Please enter your Gemini API key to proceed.")


# --- Sidebar UI ---
st.sidebar.header("About this App")
st.sidebar.markdown(
    """
This application demonstrates how to translate content from a YouTube video
into different languages using the Gemini API.

**How it works:**
1.  Enter your Gemini API key.
2.  Enter a YouTube video URL.
3.  Select a target language.
4.  The app processes the video's audio to generate a transcript (simplified for this demo).
5.  The transcript is sent to the Gemini API for translation.
6.  The translated text is then displayed on the screen.
"""
)

st.sidebar.markdown(
    """
**Important Notes:**
-   The Gemini API is used for text translation, not for audio transcription.
-   The transcription part is a simplified placeholder. For a real-world application,
    you would use a dedicated ASR (Automatic Speech Recognition) service.
"""
)

# --- Main App Title and Introduction ---
st.title("YouTube Video Translator")
st.markdown("Enter a YouTube video URL and select a language to translate its content.")


# --- Functions for Processing ---

@st.cache_data
def get_video_info(url):
    """
    Retrieves video information using pytube.
    This function is cached to prevent re-downloading on every interaction.
    """
    try:
        yt = pytube.YouTube(url)
        return yt.title, yt.video_id, yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().url
    except Exception as e:
        st.error(f"Could not retrieve video information. Please check the URL. Error: {e}")
        return None, None, None


def translate_text_with_gemini(text_to_translate, target_language):
    """
    Sends text to the Gemini API for translation.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        prompt = f"""
        Translate the following text into {target_language}.
        Keep the tone and context of the original text.
        Do not add any additional commentary or explanation, just the translated text.

        Original text:
        {text_to_translate}
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Translation failed. Please try again. Error: {e}")
        return None


# --- Input Fields for URL and Language ---
col1, col2 = st.columns([3, 1])

with col1:
    youtube_url = st.text_input(
        "YouTube Video URL",
        placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )

with col2:
    target_language = st.selectbox(
        "Target Language",
        options=["Spanish", "French", "German", "Japanese", "Chinese", "Hindi"],
        index=0
    )


# --- Main Action Button ---
if st.button("Translate & Generate"):
    if not api_key:
        st.error("Please enter your Gemini API key to run the translation.")
    elif not youtube_url:
        st.error("Please enter a valid YouTube video URL.")
    else:
        with st.spinner("Processing video and translating content..."):
            # Step 1: Get video information
            title, video_id, video_url = get_video_info(youtube_url)
            if not video_id:
                st.stop()

            # --- Mock Transcription (as Gemini doesn't do ASR) ---
            mock_transcript_raw = """
            Hello and welcome to the show. Today, we're going to talk about the latest trends in artificial intelligence.
            AI is transforming industries, from healthcare to finance.
            The future of AI is collaborative and exciting.
            We're seeing a boom in machine learning models and data science.
            Thank you for watching.
            """
            
            segments_to_translate = textwrap.wrap(mock_transcript_raw, 80)
            
            # Step 2: Translate the segments
            translated_text_list = []
            for segment in segments_to_translate:
                translated_segment = translate_text_with_gemini(segment, target_language)
                if translated_segment:
                    translated_text_list.append(translated_segment)

            if translated_text_list:
                translated_text = " ".join(translated_text_list)
                
                st.success("Translation complete!")
                
                # --- Output Section ---
                st.subheader("Original Video")
                st.video(youtube_url)
                
                st.subheader(f"Translated Content ({target_language})")
                
                # Display the translated text
                st.text_area(
                    "Translated Text",
                    value=translated_text,
                    height=200,
                    help="This is the translated text from the video.",
                    disabled=True
                )

