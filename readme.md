# Documentor

- Documentor is a simple Streamlit app that analyzes PDF files and answers your questions.
- Documentor, PDF dosyalarını analiz edip sorularınıza cevap veren basit bir Streamlit uygulamasıdır.

## What Does It Do?

- Reads PDF files
- Extracts text and basic table data
- Supports question-answering based on file content

## Requirements

- Python 3.10+
- Google Gemini API key

## Installation

1. Open the project.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

Start the app:

```bash
streamlit run app.py
```

In the browser:

1. Enter your Google API key
2. Upload a PDF file
3. Ask your question

## API Key

- The API key can be saved from inside the app.
- It is written to the `.env` file in the project root as `GOOGLE_API_KEY`.

You can also add it manually:

```env
GOOGLE_API_KEY=your_api_key_here
```

## Tech Stack

- Streamlit
- LangChain
- Google Generative AI
- pdfplumber
- python-dotenv