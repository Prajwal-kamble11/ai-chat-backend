import io
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from a PDF file.
    """
    reader = PdfReader(io.BytesIO(file_content))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_txt(file_content: bytes) -> str:
    """
    Extract text from a plain text file.
    """
    return file_content.decode("utf-8")

def chunk_text(text: str, chunk_size: int = 600, chunk_overlap: int = 60) -> list[str]:
    """
    Split text into smaller chunks for vector search.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_text(text)
