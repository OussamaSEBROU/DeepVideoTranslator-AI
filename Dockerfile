# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and Tesseract OCR languages
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    ffmpeg \
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
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Run demo.py when the container launches
CMD ["streamlit", "run", "demo.py"]
