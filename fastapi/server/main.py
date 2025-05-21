from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from typing import Annotated
from tr_dbt_to_english import DbtToEnglish
from fastapi.responses import StreamingResponse
import json
import io
import docx
import PyPDF2


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


@app.post("/get_node_in_english")
async def get_node_in_english(catalog_file: Annotated[UploadFile, File()],
                              manifest_file: Annotated[UploadFile, File()],
                              node_to_parse: Annotated[str, Form()],
                              prompt: Annotated[str, Form()],
                              additional_context_file: Annotated[
                                  UploadFile, File()] = None):
    manifest_str = await manifest_file.read()
    catalog_str = await catalog_file.read()
    additional_context = ''
    if additional_context_file:
        content = await additional_context_file.read()
        file_extension = additional_context_file.filename.rsplit('.', 1)[
            1].lower()
        if file_extension in ("txt", "md"):
            # For text files
            additional_context = content.decode("utf-8")
        elif file_extension == "docx":
            # For Word documents
            doc_stream = io.BytesIO(content)
            doc = docx.Document(doc_stream)
            additional_context = "\n".join(
                [para.text for para in doc.paragraphs])
        elif file_extension == "pdf":
            # For PDF files
            pdf_stream = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                additional_context += page.extract_text() + "\n"
        else:
            return HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}")
    manifest = json.loads(manifest_str)
    catalog = json.loads(catalog_str)
    return StreamingResponse(DbtToEnglish.upload_dbt_node(
        node_to_parse,
        manifest,
        catalog,
        prompt,
        additional_context
    ), media_type='text/plain')
