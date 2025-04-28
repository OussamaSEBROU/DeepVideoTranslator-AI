# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and Tesseract OCR languages
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-eng \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-chi-sim \
    tesseract-ocr-deu \
    tesseract-ocr-spa \
    tesseract-ocr-jpn \
    tesseract-ocr-hin \
    tesseract-ocr-ita \
    tesseract-ocr-kor \
    tesseract-ocr-por \
    tesseract-ocr-rus \
    tesseract-ocr-swe \
    tesseract-ocr-tur \
    tesseract-ocr-vie \
    ffmpeg \
    libsm6 \
    libxext6 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Run demo.py when the container launches
CMD ["streamlit", "run", "demo.py"]