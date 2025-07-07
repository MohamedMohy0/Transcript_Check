import streamlit as st
import pikepdf
from datetime import datetime
import re
from PyPDF2 import PdfReader
import fitz  
import time
from io import BytesIO


st.set_page_config(page_title="كشف الوصولات", layout="centered")


st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer   {visibility: hidden;}
        header   {visibility: hidden;}
        body, .stApp {direction: rtl; text-align: right; font-family: 'Arial', sans-serif;}
        .css-1d391kg {text-align: right;}
    </style>
    """,
    unsafe_allow_html=True,
)

Creators = {"Chromium", "JasperReports Library"}

def is_STC(pdf_bytes: bytes) -> bool:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            if "stc Bank" in page.get_text():
                return True
    return False


def is_pdf_text_based(pdf_bytes: bytes) -> bool:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            if page.get_text().strip():
                return True
    return False


def count_pdf_pages(pdf_bytes: bytes) -> int:
   
    return len(PdfReader(BytesIO(pdf_bytes)).pages)


def parse_pdf_date(raw_date) -> datetime | str | None:

    if raw_date:
        raw_date = str(raw_date)
        if raw_date.startswith("D:"):
            try:
                return datetime.strptime(raw_date[2:16], "%Y%m%d%H%M%S")
            except ValueError:
                pass
    return raw_date


def classify_receipt(pdf_bytes: bytes) -> str:

   
    if count_pdf_pages(pdf_bytes) > 1:
        return "That is Not A Receipt"

    
    with pikepdf.open(BytesIO(pdf_bytes)) as pdf:
        info = pdf.docinfo
        creation_date = parse_pdf_date(info.get("/CreationDate"))
        mod_date      = parse_pdf_date(info.get("/ModDate"))
        creator  = str(info.get("/Creator")  or "")
        producer = str(info.get("/Producer") or "")

    
    if is_pdf_text_based(pdf_bytes):
        
        if "JasperReports Library" in creator or "JasperReports Library" in producer:
            creator = producer = "JasperReports Library"

        
        if is_STC(pdf_bytes):
            
            obj_matches = re.findall(rb"\n(\d+)\s+\d+\s+obj", pdf_bytes)
            return "Original" if len(obj_matches) == 11 else "Fake"


        if not creation_date or not mod_date or not creator or not producer or "PDFsharp" in producer:
            edited = (b"/AcroForm" in pdf_bytes) or (pdf_bytes.count(b"%%EOF") > 1)
            return "Fake" if edited else "Original"

        if creation_date == mod_date and (creator in Creators or producer in Creators):
            return "Original"

        return "Fake"

    return "Fake"



col1, col2, col3 = st.columns([2, 3, 2])
with col2:
    st.image("logo.jpg", width=120 )
    st.write("الموقع مدعوم بالكامل من قبل فريق UFRC")
st.info("الموقع لا يزال تحت التجربة")
st.title("التحقق من وصل التحويل")

uploaded_file = st.file_uploader(
    label=" قم برفع ملف PDF للتحقق منه",
    type="pdf",
    help="الرجاء رفع وصل  بصيغة PDF فقط",
    label_visibility="visible",
)

if uploaded_file is not None:
    with st.spinner("يرجى الانتظار، يتم التحقق من الوصل..."):
        time.sleep(3) 
        pdf_bytes = uploaded_file.read()
        result = classify_receipt(pdf_bytes)

    if result == "Original":
        st.success("الوصل سليم ")
    elif result == "That is Not A Receipt":
        st.warning("هذا الملف ليس وصل تحويل، الرجاء إدخال ملف آخر ")
    else:  
        st.error("هذا الوصل غير سليم ")
