
from pypdf import PdfReader
from docx import Document
from io import BytesIO


def extract_resume_text(uploaded_file):

    file_name = uploaded_file.name.lower()

    try:

        if file_name.endswith(".pdf"):

            pdf = PdfReader(BytesIO(uploaded_file.getvalue()))

            text = ""

            for page in pdf.pages:
                text += page.extract_text() or ""

            return text.strip()

        elif file_name.endswith(".docx"):

            document = Document(
                BytesIO(uploaded_file.getvalue())
            )

            text = "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
            )

            return text.strip()

        else:
            return "Unsupported file format."

    except Exception as error:

        return f"Error reading resume: {error}"
