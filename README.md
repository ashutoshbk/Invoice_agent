# 📄 Invoice Extraction PoC

A minimal proof-of-concept Streamlit app that extracts key fields (invoice number, date, vendor name, total amount) from PDF or image invoices using a combination of direct PDF text extraction, Tesseract OCR, and OpenAI GPT-4.

---

## 🔍 Features

- **Native PDF text extraction** via PyMuPDF for digitally generated PDFs
- **Scanned PDF / image OCR** using Tesseract for image-only documents
- **LLM-powered field parsing** with a strict JSON schema powered by GPT-4
- **Streamlit UI** for file upload, real-time JSON preview, and JSON download
- **Configuration** via a `.env` file for secure API key management

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-org/invoice_extraction_poc.git
cd invoice_extraction_poc
```

### 2. System dependencies

- **Tesseract-OCR**
  - Windows: install from https://github.com/tesseract-ocr/tesseract
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt-get install tesseract-ocr`

- **Poppler** (required by `pdf2image`)
  - macOS: `brew install poppler`
  - Ubuntu: `sudo apt-get install poppler-utils`
  - Windows: download from https://github.com/oschwartz10612/poppler-windows/releases

### 3. Create & activate your Conda environment

```bash
conda create --name invoice_agent python=3.10
conda activate invoice_agent
```

### 4. Install Python dependencies

All required Python packages are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root with your OpenAI API key:

```ini
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

> **Security:** Ensure `.env` is added to `.gitignore` to prevent leaking secrets.

### 6. Set Tesseract path (Windows only)

If running on Windows, add this to the top of `invoice_extraction_app.py`:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

## ▶️ Running the App

Start the Streamlit server with:

```bash
streamlit run invoice_extraction_app.py
```

Visit `http://localhost:8501` in your browser, upload a PDF or image invoice, and view or download the extracted JSON.

---

## 📁 Project Structure

```
.
├── .env                       # Environment variables (gitignored)
├── invoice_extraction_app.py  # Main Streamlit application
├── requirements.txt           # Python package dependencies
└── README.md                  # This documentation
```

---

## 🛠️ Troubleshooting

- **No text from a digital PDF?**
  - Ensure it isn’t image-only. The fallback OCR will handle scanned docs.

- **OCR quality issues?**
  - Verify Tesseract installation and path. Adjust `preprocess_image()` for thresholding and deskew.

- **OpenAI errors** (authentication, rate limits):
  - Double-check your API key in `.env`.
  - Confirm you have access to GPT-4.

---
