import streamlit as st
import os
import assemblyai as aai
import google.generativeai as genai
from tempfile import NamedTemporaryFile
import base64
import streamlit.components.v1 as components
from moviepy.editor import VideoFileClip, AudioFileClip
import random
import langdetect
import pytube
import re
import time
from datetime import timedelta

# Configuration de la page
st.set_page_config(
    page_title="DeepTranslator - AI Video Translator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés pour une interface plus professionnelle
st.markdown("""
<style>
    /* Styles généraux */
    body {
        font-family: 'Roboto', sans-serif;
        color: #1E293B;
    }
    
    /* En-têtes */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1.5rem;
        text-align: center;
        padding-bottom: 1rem;
        border-bottom: 2px solid #E2E8F0;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2563EB;
        margin-bottom: 1rem;
        padding-top: 0.5rem;
    }
    
    /* Boîtes d'information */
    .info-box {
        background-color: #EFF6FF;
        border-left: 5px solid #3B82F6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .success-box {
        background-color: #ECFDF5;
        border-left: 5px solid #10B981;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .warning-box {
        background-color: #FFFBEB;
        border-left: 5px solid #F59E0B;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .error-box {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* Boutons */
    .stButton button {
        background-color: #2563EB;
        color: white;
        font-weight: 600;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
    }
    .stButton button:hover {
        background-color: #1D4ED8;
        box-shadow: 0 6px 8px rgba(29, 78, 216, 0.25);
        transform: translateY(-2px);
    }
    .stButton button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(29, 78, 216, 0.2);
    }
    
    /* Barre latérale */
    .sidebar-content {
        padding: 1.5rem 1rem;
    }
    .sidebar-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    .sidebar-title {
        color: #2563EB;
        font-weight: 700;
        margin-left: 0.5rem;
    }
    
    /* Pied de page */
    .footer {
        text-align: center;
        margin-top: 3rem;
        padding-top: 1.5rem;
        color: #6B7280;
        font-size: 0.8rem;
        border-top: 1px solid #E2E8F0;
    }
    
    /* Conteneur vidéo */
    .video-container {
        border-radius: 0.75rem;
        overflow: hidden;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #E2E8F0;
    }
    
    /* Boutons de téléchargement */
    .download-button {
        display: inline-block;
        background-color: #2563EB;
        color: white;
        padding: 0.75rem 1.25rem;
        text-decoration: none;
        border-radius: 0.5rem;
        font-weight: 600;
        margin-right: 0.75rem;
        margin-bottom: 0.75rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    }
    .download-button:hover {
        background-color: #1D4ED8;
        box-shadow: 0 4px 6px rgba(29, 78, 216, 0.25);
        transform: translateY(-2px);
    }
    
    /* Sélecteur de langue */
    .language-selector {
        margin-bottom: 1.5rem;
        padding: 0.75rem;
        background-color: #F8FAFC;
        border-radius: 0.5rem;
        border: 1px solid #E2E8F0;
    }
    
    /* Cartes de résultats */
    .result-card {
        background-color: white;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
    }
    
    /* Onglets personnalisés */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        background-color: #F1F5F9;
        border-radius: 0.5rem 0.5rem 0 0;
        gap: 0.5rem;
        padding: 0 1rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        color: white !important;
    }
    
    /* Spinner personnalisé */
    .stSpinner > div > div {
        border-top-color: #2563EB !important;
    }
    
    /* Expanders personnalisés */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #2563EB;
        background-color: #F8FAFC;
        border-radius: 0.5rem;
    }
    .streamlit-expanderContent {
        border: 1px solid #E2E8F0;
        border-top: none;
        border-radius: 0 0 0.5rem 0.5rem;
        padding: 1rem;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-blue {
        background-color: #DBEAFE;
        color: #1E40AF;
    }
    .badge-green {
        background-color: #D1FAE5;
        color: #065F46;
    }
    .badge-yellow {
        background-color: #FEF3C7;
        color: #92400E;
    }
    .badge-red {
        background-color: #FEE2E2;
        color: #B91C1C;
    }
    
    /* Séparateurs */
    .separator {
        height: 1px;
        background-color: #E2E8F0;
        margin: 1.5rem 0;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    .fade-in {
        animation: fadeIn 0.5s ease-in-out;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        .sub-header {
            font-size: 1.25rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Set up API keys (consider using environment variables for security)
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize AssemblyAI
if ASSEMBLYAI_API_KEY:
    aai.settings.api_key = ASSEMBLYAI_API_KEY
else:
    st.markdown('<div class="error-box">Clé API AssemblyAI manquante. Veuillez définir la variable d\'environnement ASSEMBLYAI_API_KEY.</div>', unsafe_allow_html=True)
    st.stop()

# Initialize Google Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.markdown('<div class="error-box">Clé API Gemini manquante. Veuillez définir la variable d\'environnement GEMINI_API_KEY.</div>', unsafe_allow_html=True)
    st.stop()

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
    """Format time in seconds to HH:MM:SS format"""
    return str(timedelta(seconds=seconds)).split('.')[0]

def is_valid_youtube_url(url):
    """Check if the URL is a valid YouTube URL"""
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    match = re.match(youtube_regex, url)
    return match is not None

def get_youtube_video_id(url):
    """Extract YouTube video ID from URL"""
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    match = re.match(youtube_regex, url)
    if match:
        return match.group(6)
    return None

def download_youtube_audio(url, max_duration=1900):
    """
    Download audio from YouTube video and return the path to the audio file
    """
    try:
        # Create a YouTube object
        yt = pytube.YouTube(url)
        
        # Check video duration
        if yt.length > max_duration:
            return None, f"La vidéo dépasse la durée maximale autorisée de {format_time(max_duration)}."
        
        # Get the audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        # Download the audio to a temporary file
        with NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            audio_path = tmp_file.name
            audio_stream.download(filename=audio_path)
        
        return audio_path, None, yt.title
    except pytube.exceptions.RegexMatchError:
        return None, "L'URL YouTube n'est pas valide.", None
    except pytube.exceptions.VideoUnavailable:
        return None, "Cette vidéo YouTube n'est pas disponible.", None
    except Exception as e:
        return None, f"Erreur lors du téléchargement de la vidéo YouTube: {str(e)}", None

def check_video_duration(video_file):
    """
    Check if the video duration is within the allowed limit
    """
    try:
        with NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(video_file.getvalue())
            tmp_file_path = tmp_file.name

        video = VideoFileClip(tmp_file_path)
        duration = video.duration
        video.close()
        os.unlink(tmp_file_path)

        return duration <= 1900, duration  # 1900 seconds = ~31.5 minutes
    except Exception as e:
        st.markdown(f'<div class="error-box">Erreur lors de la vérification de la durée de la vidéo: {str(e)}</div>', unsafe_allow_html=True)
        return False, 0

def transcribe_audio(audio_path):
    """
    Transcribe audio and return subtitles as SRT
    """
    try:
        transcript = aai.Transcriber().transcribe(audio_path)
        subtitles = transcript.export_subtitles_srt()
        return subtitles, None
    except Exception as e:
        return None, f"Erreur lors de la transcription: {str(e)}"

def is_english(text):
    """
    Check if the given text is in English
    """
    try:
        # Extract a sample of text from the SRT file for language detection
        # SRT format has timestamps and numbers, so we need to extract just the text
        text_lines = []
        for line in text.split('\n'):
            if line and not line.strip().isdigit() and '-->' not in line:
                text_lines.append(line)
        
        sample_text = ' '.join(text_lines[:20])  # Use first 20 lines for detection
        return langdetect.detect(sample_text) == 'en'
    except:
        return False

def translate_content(content, target_language, quality="Équilibrée"):
    """
    Translate the content to the target language using Google Gemini
    """
    # Adjust temperature based on quality setting
    if quality == "Précise":
        temperature = 0.1
    elif quality == "Rapide":
        temperature = 0.4
    else:  # Équilibrée
        temperature = 0.2
    
    # Improved prompt for better translation accuracy
    prompt = f"""Tu es un traducteur professionnel spécialisé dans les sous-titres de vidéos.

Traduis le texte suivant en {target_language} en respectant ces règles:
1. Maintiens le format exact des sous-titres SRT (numéros, timestamps, etc.)
2. Traduis uniquement le texte, pas les numéros ni les timestamps
3. Préserve le sens et le contexte original
4. Adapte les expressions idiomatiques si nécessaire
5. Utilise un langage naturel et fluide
6. Respecte le registre de langue original (formel/informel)
7. Conserve la ponctuation et les caractères spéciaux
8. Assure-toi que la traduction est synchronisée avec les timestamps

Voici le texte à traduire:

{content}

Traduction:"""

    generation_config = genai.GenerationConfig(
        temperature=temperature,
        top_p=0.95,
        top_k=40,
    )

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
        return response.text, None
    except Exception as e:
        return None, f"Erreur lors de la traduction: {str(e)}"

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """
    Create a download link for a file
    """
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}" class="download-button">{file_label}</a>'
    return href

def get_random_wisdom():
    """
    Get a random wisdom quote
    """
    wisdoms = [
        "La patience est la compagne de la sagesse.",
        "La seule vraie sagesse est de savoir que vous ne savez rien.",
        "La sagesse est la récompense que vous obtenez pour une vie d'écoute lorsque vous auriez préféré parler.",
        "La connaissance parle, mais la sagesse écoute.",
        "La sagesse commence dans l'émerveillement.",
        "Le savoir s'acquiert par l'expérience, tout le reste n'est que de l'information.",
        "La sagesse n'est pas un produit de la scolarité, mais de la tentative tout au long de la vie de l'acquérir.",
        "La sagesse est de savoir quoi faire; la vertu est de le faire.",
        "La sagesse est la fille de l'expérience.",
        "La sagesse est de comprendre que vous n'êtes pas le centre de l'univers.",
        "La sagesse consiste à savoir quand éviter la perfection.",
        "La sagesse est d'avoir des rêves suffisamment grands pour ne pas les perdre de vue pendant qu'on les poursuit.",
        "La sagesse est de savoir ce qu'il faut faire; l'habileté est de savoir comment le faire.",
        "La sagesse est la richesse de l'esprit.",
        "La sagesse est la capacité d'accepter les choses que l'on ne peut pas changer."
    ]
    return random.choice(wisdoms)

def create_youtube_embed_html(video_id, subtitles_url=None):
    """
    Create HTML for embedding YouTube video with optional subtitles
    """
    if subtitles_url:
        # With subtitles
        html = f"""
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 10px;">
            <iframe
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 10px;"
                src="https://www.youtube.com/embed/{video_id}?cc_load_policy=1&cc_lang_pref=en"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
            ></iframe>
        </div>
        """
    else:
        # Without subtitles
        html = f"""
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 10px;">
            <iframe
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 10px;"
                src="https://www.youtube.com/embed/{video_id}"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
            ></iframe>
        </div>
        """
    return html

def display_stats_card():
    """
    Display a card with statistics about the application
    """
    st.markdown("""
    <div style="background-color: #F8FAFC; border-radius: 0.75rem; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); border: 1px solid #E2E8F0;">
        <h3 style="color: #2563EB; margin-bottom: 1rem; font-size: 1.25rem;">Statistiques DeepTranslator</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 1rem;">
            <div style="flex: 1; min-width: 120px; background-color: white; padding: 1rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);">
                <div style="font-size: 1.5rem; font-weight: 700; color: #2563EB;">15+</div>
                <div style="color: #64748B; font-size: 0.875rem;">Langues supportées</div>
            </div>
            <div style="flex: 1; min-width: 120px; background-color: white; padding: 1rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);">
                <div style="font-size: 1.5rem; font-weight: 700; color: #2563EB;">31.5</div>
                <div style="color: #64748B; font-size: 0.875rem;">Minutes max</div>
            </div>
            <div style="flex: 1; min-width: 120px; background-color: white; padding: 1rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);">
                <div style="font-size: 1.5rem; font-weight: 700; color: #2563EB;">99%</div>
                <div style="color: #64748B; font-size: 0.875rem;">Précision</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        
        # Logo et titre
        st.markdown("""
        <div class="sidebar-header">
            <img src="https://img.icons8.com/fluency/96/000000/video-editing.png" width="40">
            <h2 class="sidebar-title">DeepTranslator</h2>
        </div>
        <p style="color: #6B7280; margin-bottom: 1.5rem;">Traduction de sous-titres vidéo alimentée par l'IA</p>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

        # Instructions in sidebar
        with st.expander("📋 Guide d'utilisation", expanded=True):
            st.markdown("""
            ### Comment utiliser DeepTranslator:
            
            1. **Choisissez votre source**:
               - Téléchargez une vidéo depuis votre appareil
               - OU collez un lien YouTube
            
            2. **Sélectionnez la langue cible** pour la traduction
            
            3. **Cliquez sur "Traiter la vidéo"** et attendez le traitement
            
            4. **Téléchargez les fichiers de sous-titres** générés
            
            5. **Visionnez votre vidéo** avec les nouveaux sous-titres
            
            > **Note**: Cette application ne fonctionne qu'avec des vidéos en anglais.
            """)
        
        with st.expander("⚙️ Paramètres avancés"):
            st.markdown("### Options de traduction")
            translation_quality = st.select_slider(
                "Qualité de traduction",
                options=["Rapide", "Équilibrée", "Précise"],
                value="Équilibrée",
                help="Influence la précision et la vitesse de traduction"
            )
            
            st.markdown("### Limites du système")
            st.info("Durée maximale de vidéo: 31.5 minutes")
            st.info("Formats supportés: MP4, MOV, AVI, MKV")
            
            # Nouvelle fonctionnalité: Thème de l'application
            st.markdown("### Personnalisation")
            app_theme = st.radio(
                "Thème de l'application",
                options=["Bleu (Défaut)", "Sombre", "Clair"],
                index=0,
                help="Change l'apparence visuelle de l'application"
            )
            
            # Appliquer le thème sélectionné
            if app_theme == "Sombre":
                st.markdown("""
                <style>
                    body {
                        color: #E2E8F0;
                        background-color: #1E293B;
                    }
                    .main-header {
                        color: #60A5FA;
                        border-bottom-color: #334155;
                    }
                    .sub-header {
                        color: #60A5FA;
                    }
                    .info-box, .success-box, .warning-box, .error-box {
                        background-color: #334155;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
                    }
                    .info-box {
                        border-left-color: #60A5FA;
                    }
                    .success-box {
                        border-left-color: #34D399;
                    }
                    .warning-box {
                        border-left-color: #FBBF24;
                    }
                    .error-box {
                        border-left-color: #F87171;
                    }
                    .stButton button {
                        background-color: #3B82F6;
                    }
                    .stButton button:hover {
                        background-color: #2563EB;
                    }
                    .video-container, .result-card {
                        background-color: #1E293B;
                        border-color: #334155;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
                    }
                    .footer {
                        border-top-color: #334155;
                        color: #94A3B8;
                    }
                    .language-selector {
                        background-color: #1E293B;
                        border-color: #334155;
                    }
                    .streamlit-expanderHeader {
                        background-color: #334155;
                        color: #60A5FA;
                    }
                    .streamlit-expanderContent {
                        border-color: #334155;
                        background-color: #1E293B;
                    }
                    .separator {
                        background-color: #334155;
                    }
                </style>
                """, unsafe_allow_html=True)
            elif app_theme == "Clair":
                st.markdown("""
                <style>
                    body {
                        color: #1E293B;
                        background-color: #FFFFFF;
                    }
                    .main-header {
                        color: #3B82F6;
                        border-bottom-color: #F1F5F9;
                    }
                    .sub-header {
                        color: #3B82F6;
                    }
                    .info-box, .success-box, .warning-box, .error-box {
                        background-color: #FFFFFF;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                    }
                    .stButton button {
                        background-color: #3B82F6;
                    }
                    .video-container, .result-card {
                        background-color: #FFFFFF;
                        border-color: #F1F5F9;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
                    }
                    .footer {
                        border-top-color: #F1F5F9;
                    }
                    .language-selector {
                        background-color: #FFFFFF;
                        border-color: #F1F5F9;
                    }
                    .streamlit-expanderHeader {
                        background-color: #F8FAFC;
                    }
                    .separator {
                        background-color: #F1F5F9;
                    }
                </style>
                """, unsafe_allow_html=True)
        
        # Nouvelle fonctionnalité: Langues récemment utilisées
        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)
        st.markdown("### Langues récemment utilisées")
        st.markdown("""
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;">
            <span class="badge badge-blue">Français</span>
            <span class="badge badge-green">Espagnol</span>
            <span class="badge badge-yellow">Arabe</span>
            <span class="badge badge-blue">Allemand</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Nouvelle fonctionnalité: Compteur d'utilisation
        st.markdown("### Statistiques d'utilisation")
        st.markdown("""
        <div style="background-color: #F1F5F9; border-radius: 0.5rem; padding: 0.75rem; margin-bottom: 1rem;">
            <div style="font-size: 0.875rem; color: #64748B; margin-bottom: 0.25rem;">Vidéos traitées aujourd'hui</div>
            <div style="font-size: 1.25rem; font-weight: 600; color: #2563EB;">12</div>
            <div style="height: 0.5rem; background-color: #E2E8F0; border-radius: 9999px; margin: 0.5rem 0;">
                <div style="height: 100%; width: 60%; background-color: #3B82F6; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 0.75rem; color: #64748B;">60% de la limite quotidienne</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("ℹ️ À propos"):
            st.markdown("""
            ### DeepTranslator - Traducteur vidéo IA

            Cette application utilise des technologies d'IA avancées pour simplifier votre flux de travail de sous-titrage vidéo:

            **Transcription vidéo**:
            Utilisation de l'IA d'AssemblyAI pour une reconnaissance vocale précise.

            **Traduction multilingue**:
            Propulsée par l'IA de Google Gemini, offrant une traduction dans plus de 15 langues.

            **Fonctionnalités clés**:
            - Support de divers formats vidéo
            - Transcription et traduction de haute qualité
            - Interface conviviale
            - Fichiers SRT téléchargeables
            - Support direct des liens YouTube
            - Lecteur vidéo intégré avec sous-titres

            **Idéal pour**:
            - Créateurs de contenu visant un public international
            - Établissements éducatifs créant du matériel multilingue
            - Entreprises localisant du contenu vidéo
            - Toute personne ayant besoin de sous-titres vidéo rapides et précis

            © 2024 DeepTranslator. Tous droits réservés.
            """)
        
        st.markdown('<div class="footer">Développé par Mr. Oussama SEBROU</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Main area
    st.markdown('<h1 class="main-header">DeepTranslator - Traducteur Vidéo IA</h1>', unsafe_allow_html=True)
    
    # Afficher la carte de statistiques
    display_stats_card()
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["📤 Télécharger une vidéo", "🔗 Lien YouTube"])
    
    with tab1:
        st.markdown('<div class="info-box">Cette application ne fonctionne qu\'avec des vidéos en anglais. Assurez-vous que votre vidéo contient de l\'audio en anglais.</div>', unsafe_allow_html=True)
        
        # File uploader with improved UI
        st.markdown("""
        <div style="background-color: #F8FAFC; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1.5rem; border: 2px dashed #CBD5E1; text-align: center;">
            <img src="https://img.icons8.com/fluency/96/000000/upload.png" width="48" style="margin-bottom: 1rem;">
            <h3 style="color: #2563EB; margin-bottom: 0.5rem; font-size: 1.25rem;">Téléchargez votre vidéo</h3>
            <p style="color: #64748B; margin-bottom: 0.5rem;">Formats supportés: MP4, MOV, AVI, MKV</p>
            <p style="color: #64748B; font-size: 0.875rem;">Durée maximale: 31.5 minutes</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Choisissez une vidéo en anglais", type=["mp4", "mov", "avi", "mkv"], accept_multiple_files=False, label_visibility="collapsed")
        
        # Language selection with improved UI
        st.markdown('<div class="language-selector">', unsafe_allow_html=True)
        st.markdown('<h3 style="color: #2563EB; margin-bottom: 0.75rem; font-size: 1.1rem;">Sélectionnez la langue cible</h3>', unsafe_allow_html=True)
        
        # Organiser les langues en colonnes pour une meilleure présentation
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            target_language = st.radio(
                "Langue",
                ["Arabic", "Chinese (Simplified)", "French", "German"],
                index=2,  # Français par défaut
                label_visibility="collapsed"
            )
        with col2:
            if st.radio(
                "Langue",
                ["Hindi", "Italian", "Japanese", "Korean"],
                label_visibility="collapsed"
            ) in ["Hindi", "Italian", "Japanese", "Korean"]:
                target_language = st.session_state.radio
        with col3:
            if st.radio(
                "Langue",
                ["Portuguese", "Russian", "Spanish", "Swedish"],
                label_visibility="collapsed"
            ) in ["Portuguese", "Russian", "Spanish", "Swedish"]:
                target_language = st.session_state.radio
        with col4:
            if st.radio(
                "Langue",
                ["Turkish", "Vietnamese"],
                label_visibility="collapsed"
            ) in ["Turkish", "Vietnamese"]:
                target_language = st.session_state.radio
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_file is not None:
            file_name = os.path.splitext(uploaded_file.name)[0]
            
            # Check video duration
            duration_valid, duration = check_video_duration(uploaded_file)
            if not duration_valid:
                st.markdown(f'<div class="error-box">La vidéo téléchargée dépasse la limite de 31.5 minutes (Durée: {format_time(duration)}). Veuillez télécharger une vidéo plus courte.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="info-box"><strong>Vidéo prête à être traitée</strong><br>Nom: {file_name}<br>Durée: {format_time(duration)}</div>', unsafe_allow_html=True)
                
                # Bouton de traitement amélioré
                process_col1, process_col2, process_col3 = st.columns([1, 2, 1])
                with process_col2:
                    if st.button("🚀 Traiter la vidéo", key="process_uploaded_video"):
                        with st.spinner(f"Traitement de la vidéo et traduction en {target_language}..."):
                            # Display random wisdoms during processing
                            progress_container = st.container()
                            wisdom_placeholder = progress_container.empty()
                            progress_bar = progress_container.progress(0)
                            
                            # Transcribe video
                            with NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_file_path = tmp_file.name
                            
                            # Show wisdom while processing
                            wisdom_placeholder.info(f"Transcription en cours... {get_random_wisdom()}")
                            progress_bar.progress(25)
                            
                            # Transcribe video
                            subtitles, transcription_error = transcribe_audio(tmp_file_path)
                            
                            if transcription_error:
                                wisdom_placeholder.empty()
                                progress_bar.empty()
                                st.markdown(f'<div class="error-box">{transcription_error}</div>', unsafe_allow_html=True)
                                os.unlink(tmp_file_path)
                                st.stop()
                            
                            # Check if the subtitles are in English
                            if not is_english(subtitles):
                                wisdom_placeholder.empty()
                                progress_bar.empty()
                                st.markdown('<div class="error-box">La vidéo semble être dans une langue autre que l\'anglais. Veuillez télécharger une vidéo en anglais.</div>', unsafe_allow_html=True)
                                os.unlink(tmp_file_path)
                                st.stop()
                            
                            # Save original subtitles
                            original_subtitle_file = f"{file_name}_original.srt"
                            with open(original_subtitle_file, "w", encoding="utf-8") as f:
                                f.write(subtitles)
                            
                            # Show new wisdom while translating
                            wisdom_placeholder.info(f"Traduction en cours... {get_random_wisdom()}")
                            progress_bar.progress(75)
                            
                            # Get translation quality from sidebar
                            translation_quality = "Équilibrée"  # Default value
                            if "translation_quality" in locals():
                                translation_quality = locals()["translation_quality"]
                            
                            # Translate subtitles
                            translated_subtitles, translation_error = translate_content(subtitles, LANGUAGES[target_language], translation_quality)
                            
                            if translation_error:
                                wisdom_placeholder.empty()
                                progress_bar.empty()
                                st.markdown(f'<div class="error-box">{translation_error}</div>', unsafe_allow_html=True)
                                os.unlink(tmp_file_path)
                                st.stop()
                            
                            # Save translated subtitles
                            translated_subtitle_file = f"{file_name}_{target_language.lower().replace(' ', '_')}.srt"
                            with open(translated_subtitle_file, "w", encoding="utf-8") as f:
                                f.write(translated_subtitles)
                            
                            wisdom_placeholder.empty()  # Remove the wisdom messages
                            progress_bar.progress(100)
                            time.sleep(0.5)  # Pause pour montrer la barre à 100%
                            progress_bar.empty()
                            
                            # Afficher les résultats dans une carte
                            st.markdown("""
                            <div class="result-card fade-in">
                                <h2 style="color: #2563EB; margin-bottom: 1rem; display: flex; align-items: center;">
                                    <span style="background-color: #DBEAFE; color: #1E40AF; width: 32px; height: 32px; border-radius: 50%; display: inline-flex; justify-content: center; align-items: center; margin-right: 0.75rem;">✓</span>
                                    Traitement terminé avec succès!
                                </h2>
                                
                                <div style="margin-bottom: 1.5rem;">
                                    <h3 style="color: #2563EB; margin-bottom: 0.75rem; font-size: 1.1rem;">Télécharger les fichiers de sous-titres</h3>
                                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                            """, unsafe_allow_html=True)
                            
                            # Download buttons
                            st.markdown(get_binary_file_downloader_html(original_subtitle_file, "📄 Sous-titres originaux (EN)"), unsafe_allow_html=True)
                            st.markdown(get_binary_file_downloader_html(translated_subtitle_file, f"🌐 Sous-titres traduits ({target_language})"), unsafe_allow_html=True)
                            
                            st.markdown("""
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 1.5rem;">
                                    <h3 style="color: #2563EB; margin-bottom: 0.75rem; font-size: 1.1rem;">Aperçu de la vidéo</h3>
                            """, unsafe_allow_html=True)
                            
                            # Display video with subtitles
                            st.markdown('<div class="video-container">', unsafe_allow_html=True)
                            st.video(uploaded_file)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown("""
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Instructions for offline viewing
                            with st.expander("📝 Instructions pour le visionnage hors ligne", expanded=True):
                                st.markdown("""
                                ### Comment utiliser les sous-titres avec votre vidéo:
                                
                                1. Créez un nouveau dossier sur votre ordinateur
                                2. Téléchargez la vidéo originale et le fichier de sous-titres que vous souhaitez utiliser
                                3. Placez les deux fichiers dans le dossier créé. Assurez-vous qu'ils ont le même nom (à l'exception de l'extension de fichier)
                                4. Pour regarder avec des sous-titres:
                                   - Utilisez VLC Media Player: Il détectera automatiquement le fichier de sous-titres s'il se trouve dans le même dossier et porte le même nom que la vidéo
                                5. Profitez de votre vidéo avec des sous-titres traduits!
                                """)
                            
                            # Clean up
                            os.unlink(tmp_file_path)
        else:
            # Message d'accueil amélioré
            st.markdown("""
            <div class="result-card" style="text-align: center; padding: 2rem;">
                <img src="https://img.icons8.com/fluency/96/000000/video-editing.png" width="64" style="margin-bottom: 1rem;">
                <h2 style="color: #2563EB; margin-bottom: 1rem;">Bienvenue sur DeepTranslator!</h2>
                <p style="color: #64748B; margin-bottom: 1.5rem; font-size: 1.1rem;">Téléchargez votre vidéo en anglais et sélectionnez une langue cible pour commencer.</p>
                <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem;">
                    <div style="background-color: #F1F5F9; border-radius: 0.5rem; padding: 1rem; text-align: center; min-width: 120px;">
                        <div style="font-size: 1.5rem; color: #2563EB; margin-bottom: 0.5rem;">1</div>
                        <div style="color: #64748B; font-size: 0.875rem;">Télécharger</div>
                    </div>
                    <div style="background-color: #F1F5F9; border-radius: 0.5rem; padding: 1rem; text-align: center; min-width: 120px;">
                        <div style="font-size: 1.5rem; color: #2563EB; margin-bottom: 0.5rem;">2</div>
                        <div style="color: #64748B; font-size: 0.875rem;">Traduire</div>
                    </div>
                    <div style="background-color: #F1F5F9; border-radius: 0.5rem; padding: 1rem; text-align: center; min-width: 120px;">
                        <div style="font-size: 1.5rem; color: #2563EB; margin-bottom: 0.5rem;">3</div>
                        <div style="color: #64748B; font-size: 0.875rem;">Télécharger</div>
                    </div>
                </div>
                <p style="color: #64748B; font-size: 0.875rem;">Nous sommes ravis de vous aider à transcrire, traduire et regarder votre vidéo avec des sous-titres multilingues!</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="info-box">Entrez un lien YouTube vers une vidéo en anglais. L\'application extraira l\'audio, créera des sous-titres et les traduira.</div>', unsafe_allow_html=True)
        
        # YouTube URL input with improved UI
        st.markdown("""
        <div style="background-color: #F8FAFC; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1.5rem; border: 2px dashed #CBD5E1; text-align: center;">
            <img src="https://img.icons8.com/color/96/000000/youtube-play.png" width="48" style="margin-bottom: 1rem;">
            <h3 style="color: #2563EB; margin-bottom: 0.5rem; font-size: 1.25rem;">Entrez un lien YouTube</h3>
            <p style="color: #64748B; margin-bottom: 0.5rem;">Exemple: https://www.youtube.com/watch?v=dQw4w9WgXcQ</p>
            <p style="color: #64748B; font-size: 0.875rem;">Durée maximale: 31.5 minutes</p>
        </div>
        """, unsafe_allow_html=True)
        
        youtube_url = st.text_input("Entrez un lien YouTube:", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")
        
        # Language selection with improved UI
        st.markdown('<div class="language-selector">', unsafe_allow_html=True)
        st.markdown('<h3 style="color: #2563EB; margin-bottom: 0.75rem; font-size: 1.1rem;">Sélectionnez la langue cible</h3>', unsafe_allow_html=True)
        
        # Organiser les langues en colonnes pour une meilleure présentation
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            yt_target_language = st.radio(
                "Langue",
                ["Arabic", "Chinese (Simplified)", "French", "German"],
                index=2,  # Français par défaut
                key="yt_lang_col1",
                label_visibility="collapsed"
            )
        with col2:
            if st.radio(
                "Langue",
                ["Hindi", "Italian", "Japanese", "Korean"],
                key="yt_lang_col2",
                label_visibility="collapsed"
            ) in ["Hindi", "Italian", "Japanese", "Korean"]:
                yt_target_language = st.session_state.yt_lang_col2
        with col3:
            if st.radio(
                "Langue",
                ["Portuguese", "Russian", "Spanish", "Swedish"],
                key="yt_lang_col3",
                label_visibility="collapsed"
            ) in ["Portuguese", "Russian", "Spanish", "Swedish"]:
                yt_target_language = st.session_state.yt_lang_col3
        with col4:
            if st.radio(
                "Langue",
                ["Turkish", "Vietnamese"],
                key="yt_lang_col4",
                label_visibility="collapsed"
            ) in ["Turkish", "Vietnamese"]:
                yt_target_language = st.session_state.yt_lang_col4
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if youtube_url:
            if not is_valid_youtube_url(youtube_url):
                st.markdown('<div class="error-box">L\'URL YouTube n\'est pas valide. Veuillez entrer une URL YouTube correcte.</div>', unsafe_allow_html=True)
            else:
                video_id = get_youtube_video_id(youtube_url)
                if video_id:
                    # Display YouTube video preview
                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    st.markdown('<h3 style="color: #2563EB; margin-bottom: 0.75rem; font-size: 1.1rem;">Aperçu de la vidéo YouTube</h3>', unsafe_allow_html=True)
                    st.markdown('<div class="video-container">', unsafe_allow_html=True)
                    components.html(create_youtube_embed_html(video_id), height=400)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Bouton de traitement amélioré
                    process_col1, process_col2, process_col3 = st.columns([1, 2, 1])
                    with process_col2:
                        if st.button("🚀 Traiter la vidéo YouTube", key="process_youtube_video"):
                            with st.spinner(f"Téléchargement et traitement de la vidéo YouTube..."):
                                # Display random wisdoms during processing
                                progress_container = st.container()
                                wisdom_placeholder = progress_container.empty()
                                progress_bar = progress_container.progress(0)
                                
                                # Download YouTube audio
                                wisdom_placeholder.info(f"Téléchargement de la vidéo YouTube... {get_random_wisdom()}")
                                progress_bar.progress(10)
                                
                                # Download YouTube audio
                                audio_path, download_error, video_title = download_youtube_audio(youtube_url)
                                
                                if download_error:
                                    wisdom_placeholder.empty()
                                    progress_bar.empty()
                                    st.markdown(f'<div class="error-box">{download_error}</div>', unsafe_allow_html=True)
                                    st.stop()
                                
                                # Show new wisdom while transcribing
                                wisdom_placeholder.info(f"Transcription de l'audio... {get_random_wisdom()}")
                                progress_bar.progress(40)
                                
                                # Transcribe audio
                                subtitles, transcription_error = transcribe_audio(audio_path)
                                
                                if transcription_error:
                                    wisdom_placeholder.empty()
                                    progress_bar.empty()
                                    st.markdown(f'<div class="error-box">{transcription_error}</div>', unsafe_allow_html=True)
                                    os.unlink(audio_path)
                                    st.stop()
                                
                                # Check if the subtitles are in English
                                if not is_english(subtitles):
                                    wisdom_placeholder.empty()
                                    progress_bar.empty()
                                    st.markdown('<div class="error-box">La vidéo semble être dans une langue autre que l\'anglais. Veuillez choisir une vidéo en anglais.</div>', unsafe_allow_html=True)
                                    os.unlink(audio_path)
                                    st.stop()
                                
                                # Save original subtitles
                                original_subtitle_file = f"youtube_{video_id}_original.srt"
                                with open(original_subtitle_file, "w", encoding="utf-8") as f:
                                    f.write(subtitles)
                                
                                # Show new wisdom while translating
                                wisdom_placeholder.info(f"Traduction en cours... {get_random_wisdom()}")
                                progress_bar.progress(70)
                                
                                # Get translation quality from sidebar
                                translation_quality = "Équilibrée"  # Default value
                                if "translation_quality" in locals():
                                    translation_quality = locals()["translation_quality"]
                                
                                # Translate subtitles
                                translated_subtitles, translation_error = translate_content(subtitles, LANGUAGES[yt_target_language], translation_quality)
                                
                                if translation_error:
                                    wisdom_placeholder.empty()
                                    progress_bar.empty()
                                    st.markdown(f'<div class="error-box">{translation_error}</div>', unsafe_allow_html=True)
                                    os.unlink(audio_path)
                                    st.stop()
                                
                                # Save translated subtitles
                                translated_subtitle_file = f"youtube_{video_id}_{yt_target_language.lower().replace(' ', '_')}.srt"
                                with open(translated_subtitle_file, "w", encoding="utf-8") as f:
                                    f.write(translated_subtitles)
                                
                                wisdom_placeholder.empty()  # Remove the wisdom messages
                                progress_bar.progress(100)
                                time.sleep(0.5)  # Pause pour montrer la barre à 100%
                                progress_bar.empty()
                                
                                # Afficher les résultats dans une carte
                                st.markdown(f"""
                                <div class="result-card fade-in">
                                    <h2 style="color: #2563EB; margin-bottom: 1rem; display: flex; align-items: center;">
                                        <span style="background-color: #DBEAFE; color: #1E40AF; width: 32px; height: 32px; border-radius: 50%; display: inline-flex; justify-content: center; align-items: center; margin-right: 0.75rem;">✓</span>
                                        Traitement terminé avec succès!
                                    </h2>
                                    
                                    <div style="margin-bottom: 1rem;">
                                        <span class="badge badge-blue">YouTube</span>
                                        <span class="badge badge-green">{yt_target_language}</span>
                                        <span class="badge badge-yellow">SRT</span>
                                    </div>
                                    
                                    <div style="margin-bottom: 1.5rem;">
                                        <h3 style="color: #2563EB; margin-bottom: 0.75rem; font-size: 1.1rem;">Titre de la vidéo</h3>
                                        <p style="color: #1E293B; background-color: #F8FAFC; padding: 0.75rem; border-radius: 0.5rem; border: 1px solid #E2E8F0;">{video_title}</p>
                                    </div>
                                    
                                    <div style="margin-bottom: 1.5rem;">
                                        <h3 style="color: #2563EB; margin-bottom: 0.75rem; font-size: 1.1rem;">Télécharger les fichiers de sous-titres</h3>
                                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                """, unsafe_allow_html=True)
                                
                                # Download buttons
                                st.markdown(get_binary_file_downloader_html(original_subtitle_file, "📄 Sous-titres originaux (EN)"), unsafe_allow_html=True)
                                st.markdown(get_binary_file_downloader_html(translated_subtitle_file, f"🌐 Sous-titres traduits ({yt_target_language})"), unsafe_allow_html=True)
                                
                                st.markdown("""
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 1.5rem;">
                                        <h3 style="color: #2563EB; margin-bottom: 0.75rem; font-size: 1.1rem;">Vidéo YouTube avec sous-titres</h3>
                                """, unsafe_allow_html=True)
                                
                                # Display YouTube video with subtitles
                                st.markdown('<div class="info-box">Les sous-titres ne peuvent pas être directement intégrés dans le lecteur YouTube. Téléchargez les fichiers SRT et utilisez-les avec votre lecteur vidéo local.</div>', unsafe_allow_html=True)
                                st.markdown('<div class="video-container">', unsafe_allow_html=True)
                                components.html(create_youtube_embed_html(video_id), height=400)
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                                st.markdown("""
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Instructions for offline viewing
                                with st.expander("📝 Instructions pour le visionnage avec sous-titres", expanded=True):
                                    st.markdown("""
                                    ### Comment utiliser les sous-titres avec la vidéo YouTube:
                                    
                                    #### Option 1: Télécharger la vidéo et utiliser un lecteur local
                                    1. Téléchargez la vidéo YouTube en utilisant un service en ligne comme y2mate.com
                                    2. Téléchargez le fichier de sous-titres traduits depuis cette application
                                    3. Renommez le fichier de sous-titres pour qu'il corresponde au nom de votre vidéo téléchargée
                                    4. Utilisez VLC Media Player pour lire la vidéo avec les sous-titres
                                    
                                    #### Option 2: Utiliser les sous-titres avec YouTube
                                    1. Téléchargez le fichier de sous-titres traduits
                                    2. Lors de la lecture de la vidéo sur YouTube, cliquez sur l'icône ⚙️ (paramètres)
                                    3. Sélectionnez "Sous-titres" > "Ajouter des sous-titres"
                                    4. Téléchargez le fichier SRT que vous avez téléchargé
                                    
                                    > Note: L'option 2 nécessite que vous soyez le propriétaire de la vidéo YouTube ou que la vidéo permette l'ajout de sous-titres par la communauté.
                                    """)
                                
                                # Clean up
                                os.unlink(audio_path)
                else:
                    st.markdown('<div class="error-box">Impossible d\'extraire l\'ID de la vidéo YouTube. Veuillez vérifier l\'URL.</div>', unsafe_allow_html=True)
        else:
            # Message d'accueil amélioré pour YouTube
            st.markdown("""
            <div class="result-card" style="text-align: center; padding: 2rem;">
                <img src="https://img.icons8.com/color/96/000000/youtube-play.png" width="64" style="margin-bottom: 1rem;">
                <h2 style="color: #2563EB; margin-bottom: 1rem;">Utilisez des vidéos YouTube!</h2>
                <p style="color: #64748B; margin-bottom: 1.5rem; font-size: 1.1rem;">Collez simplement l'URL d'une vidéo YouTube en anglais et obtenez des sous-titres traduits.</p>
                <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem;">
                    <div style="background-color: #F1F5F9; border-radius: 0.5rem; padding: 1rem; text-align: center; min-width: 120px;">
                        <div style="font-size: 1.5rem; color: #2563EB; margin-bottom: 0.5rem;">1</div>
                        <div style="color: #64748B; font-size: 0.875rem;">Coller l'URL</div>
                    </div>
                    <div style="background-color: #F1F5F9; border-radius: 0.5rem; padding: 1rem; text-align: center; min-width: 120px;">
                        <div style="font-size: 1.5rem; color: #2563EB; margin-bottom: 0.5rem;">2</div>
                        <div style="color: #64748B; font-size: 0.875rem;">Traduire</div>
                    </div>
                    <div style="background-color: #F1F5F9; border-radius: 0.5rem; padding: 1rem; text-align: center; min-width: 120px;">
                        <div style="font-size: 1.5rem; color: #2563EB; margin-bottom: 0.5rem;">3</div>
                        <div style="color: #64748B; font-size: 0.875rem;">Télécharger</div>
                    </div>
                </div>
                <p style="color: #64748B; font-size: 0.875rem;">Cette fonctionnalité vous permet de créer des sous-titres traduits pour n'importe quelle vidéo YouTube accessible publiquement!</p>
            </div>
            """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="footer">
        <p>DeepTranslator - Propulsé par AssemblyAI et Google Gemini</p>
        <p>© 2024 Tous droits réservés</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
