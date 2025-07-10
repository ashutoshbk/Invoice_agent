import os
import io
import json
from dotenv import load_dotenv
from openai import OpenAI
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import fitz  
import streamlit as st

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_from_pdf(bytes_data: bytes) -> str:
    """
    Extract text directly from a native PDF using PyMuPDF.
    """
    text = ""
    with fitz.open(stream=bytes_data, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text


def preprocess_image(img: Image.Image) -> Image.Image:
    # ensure full color + alpha
    if img.mode == "P":
        img = img.convert("RGBA")
    # now grayscale (or keep RGB if you prefer)
    gray = img.convert("L")
    # …do threshold, denoise, etc.
    return gray

def perform_ocr_on_images(images: list) -> str:
    """
    OCR each image and return concatenated text.
    """
    texts = []
    for img in images:
        proc = preprocess_image(img)
        text = pytesseract.image_to_string(proc)
        texts.append(text)
    return "\n".join(texts)


def load_and_extract_text(uploaded_file) -> str:
    """
    Determine file type: if PDF, try direct extract, else fallback to OCR; if image, run OCR.
    """
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        # Try direct extraction
        extracted = extract_text_from_pdf(file_bytes)
        if extracted.strip():
            return extracted
        # Fallback to OCR on PDF pages
        images = convert_from_bytes(file_bytes)
        return perform_ocr_on_images(images)
    else:
        # Image file
        img = Image.open(io.BytesIO(file_bytes))
        return perform_ocr_on_images([img])


def extract_fields_with_llm(text: str) -> dict:
    """
    Use GPT-4 via the OpenAI client to extract invoice metadata and line-item/product info.
    """
    prompt = (
        "You are an invoice-processing assistant.\n"
        "Extract exactly the following into a JSON object:\n"
        "  • invoice_number (string)\n"
        "  • invoice_date (YYYY-MM-DD)\n"
        "  • vendor_name (string)\n"
        "  • total_amount (numeric with currency)\n"
        "  • products (array of objects, each with description, quantity, unit_price, line_total)\n"
        "If any field is missing, use an empty string or empty array. Do not return any extra keys.\n\n"
        "Here is the raw invoice text:\n```\n"
        + text +
        "\n```\n\n"
        "Respond *only* with the JSON."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return json.loads(response.choices[0].message.content)


def run_pipeline(uploaded_file) -> dict:
    """
    Full pipeline: load or OCR text, LLM extraction, and validation.
    """
    text = load_and_extract_text(uploaded_file)
    fields = extract_fields_with_llm(text)
    return fields

def run_pipeline_with_bytes(name: str, file_bytes: bytes) -> dict:
    """
    Wrap bytes in a file‐like object so run_pipeline can consume it
    exactly as if it came from st.file_uploader.
    """
    fake_file = io.BytesIO(file_bytes)
    fake_file.name = name
    return run_pipeline(fake_file)

# Streamlit UI layout
# st.set_page_config(
#     page_title="Invoice Extraction PoC",
#     page_icon="📄",
#     layout="centered",
#     initial_sidebar_state="expanded"
# )

# st.title("📄 Invoice Extraction PoC")
# st.write(
#     "Upload a PDF or image invoice, and the app will extract key fields "
#     "(invoice number, date, vendor name, total amount) using GPT-4."
# )

# uploaded = st.file_uploader(
#     "Choose an invoice file", type=["pdf", "png", "jpg", "jpeg"]
# )

# if uploaded:
#     with st.spinner("Extracting data..."):
#         try:
#             result = run_pipeline(uploaded)
#             st.subheader("Extracted Fields")
#             st.json(result)
#             st.download_button(
#                 "Download JSON", 
#                 json.dumps(result, indent=2),
#                 file_name="invoice_fields.json",
#                 mime="application/json"
#             )
#         except Exception as e:
#             st.error(f"Error during processing: {e}")

# st.sidebar.header("Instructions")
# st.sidebar.markdown(
#     "1. Upload a native PDF (digital) or scanned PDF/image.\n"
#     "2. The app tries direct text extraction for digital PDFs, else uses OCR.\n"
#     "3. Fields are parsed via GPT-4 with a strict JSON schema.\n"
#     "4. Download the JSON output using the button above."
# )


# ───── Streamlit UI ────────────────────────────────────────────

st.set_page_config(
    page_title="Invoice Extraction PoC",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📄 Invoice Extraction PoC")
st.write(
    "Upload a PDF or image invoice, see a preview on the left, "
    "and get your extracted JSON on the right."
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload & Preview")
    uploaded = st.file_uploader(
        "Choose an invoice file", type=["pdf", "png", "jpg", "jpeg"]
    )
    if uploaded:
        file_bytes = uploaded.read()
        st.markdown(f"**Selected file:** {uploaded.name}")

        if uploaded.name.lower().endswith((".png", ".jpg", ".jpeg")):
            st.image(file_bytes, use_container_width=True)

        elif uploaded.name.lower().endswith(".pdf"):
            try:
                # open PDF from bytes
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for i, page in enumerate(doc, start=1):
                    # render at 150 DPI (1.5 zoom)
                    zoom = 1.5
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    # convert to PIL Image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.markdown(f"**Page {i}**")
                    st.image(img, use_container_width=True)
            except Exception as e:
                st.error(f"Could not preview PDF: {e}")

with col2:
    if uploaded:
        st.markdown("<br/>" * 9, unsafe_allow_html=True)
        st.subheader("JSON Output")
        with st.spinner("Extracting data…"):
            try:
                result = run_pipeline_with_bytes(uploaded.name, file_bytes)
                st.json(result)
                st.download_button(
                    "Download JSON",
                    data=json.dumps(result, indent=2),
                    file_name="invoice_fields.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Error during processing: {e}")
    else:
        st.info("Upload a file on the left to see the JSON here.")

# Optional: keep your instructions in the sidebar
st.sidebar.header("Instructions")
st.sidebar.markdown(
    "1. Upload a native PDF (digital) or scanned PDF/image.\n\n"
    "2. It previews the file on the left.\n\n"
    "3. Fields are parsed via GPT-4 with a strict JSON schema.\n\n"
    "4. Download the JSON using the button on the right."
)