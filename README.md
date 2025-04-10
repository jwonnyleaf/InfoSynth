# 📚 InfoSynth

---

## 🚀 Getting Started

Follow these steps to get up and running:

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows
```

### 2. Install dependencies

```python
pip install -r requirements.txt
```

#### Note: You will also need to install the Tesseract OCR engine on your local machine, which is needed for processing and extracting text from image files. The path to the installed binary is automatically configured in the code based on the architecture of your machine.

If you are on MacOS:
```sh
brew install tesseract
```

OR if you are on Linux (Debian based distro):
```sh
sudo apt install tesseract-ocr
```

### 3. Configure your environment

Copy the .env.example file to .env and add your Gemini API Key:

```python
cp .env.example .env
```

Inside .env:

```
GEMINI_API_KEY=your-gemini-api-key-here
```

[ 🔑 ] Get your Gemini API key from: https://makersuite.google.com/app/apikey

### 4. Run the application

```
streamlit run app/main.py
```

This will launch a browser tab with the full UI.

### 5. Project Structure
```
infosynth/
├── app/
│   └── main.py                # Main application entry-point
│
├── core/
│   ├── retriever.py           # Chunking + TF-IDF search
│   ├── query_classifier.py    # Query intent classification
│   └── llm.py                 # Gemini API integration
│
├── utils/
│   ├── file_utils.py          # File upload, metadata, JSON saving
│   └── logger.py              # Console log formatting
│
├── data/
│   ├── uploads/               # Uploaded files
│   └── library.json           # Document metadata + chunk cache
│
├── .env                       # Your Gemini API key lives here
├── .env.example               # Template for .env
├── requirements.txt           # Project Dependencies
└── README.md
```
