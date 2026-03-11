import os
import io
import PyPDF2
from PIL import Image
import numpy as np
import torch
try:
    import easyocr
    reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
except ImportError:
    reader = None
import PyPDF2
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from quiz_generation import QuizGenerator
from google import genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY environment variable not set. Voice agent features will fail.")
gemini_client = genai.Client(api_key=api_key) if api_key else None

app = FastAPI(title="Text Summarization & Quiz Generation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = "cuda" if torch.cuda.is_available() else "cpu"

model_path = "output/saved_summarization_model"
if not os.path.exists(model_path):
    model_path = "./saved_summarization_model"

try:
    sum_tokenizer = AutoTokenizer.from_pretrained(model_path)
    sum_model = AutoModelForSeq2SeqLM.from_pretrained(
        model_path,
        device_map="auto",
        dtype=torch.float32 # CPU optimized
    )
except Exception as e:
    sum_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
    sum_model = AutoModelForSeq2SeqLM.from_pretrained(
        "facebook/bart-large-cnn",
        device_map="auto",
        dtype=torch.float32 # CPU optimized
    )

quiz_gen = QuizGenerator()

class QuizRequest(BaseModel):
    text: str

class ChatRequest(BaseModel):
    message: str
    context: str = ""

def extract_text_from_pdf(pdf_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def generate_summary(text):
    inputs = sum_tokenizer(
        [text], 
        max_length=1024, 
        truncation=True, 
        return_tensors="pt"
    ).to(device)
    
    with torch.no_grad():
        summary_ids = sum_model.generate(
            inputs["input_ids"], 
            max_length=800, 
            min_length=250, 
            num_beams=6, 
            length_penalty=3.0,
            early_stopping=True,
            forced_bos_token_id=0
        )
        
    summary = sum_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

@app.post("/summarize")
async def summarize(text: str = Form(None), file: UploadFile = File(None)):
    if file and file.filename.endswith('.pdf'):
        content = await file.read()
        extracted_text = extract_text_from_pdf(content)
    elif text:
        extracted_text = text
    else:
        raise HTTPException(status_code=400, detail="Please provide either 'text' or a 'file' (PDF).")
        
    if not extracted_text:
        raise HTTPException(status_code=400, detail="No readable text found.")
        
    summary = generate_summary(extracted_text)
    return {"original_length": len(extracted_text), "summary_length": len(summary), "summary": summary}

@app.post("/generate-quizzes")
async def generate_quizzes(
    text: str = Form(None), 
    file: UploadFile = File(None),
    num_mcq: int = Form(7),
    num_tf: int = Form(5),
    num_fib: int = Form(5),
    num_flash: int = Form(15)
):
    if file and file.filename.endswith('.pdf'):
        content = await file.read()
        extracted_text = extract_text_from_pdf(content)
    elif text:
        extracted_text = text
    else:
        raise HTTPException(status_code=400, detail="Please provide either 'text' or a 'file' (PDF).")
        
    if not extracted_text:
        raise HTTPException(status_code=400, detail="No readable text found for quiz generation.")
        
    results = quiz_gen.process_text(extracted_text, num_mcq, num_tf, num_fib, num_flash)
    return results

from google.genai import types

@app.post("/api/voice-chat")
async def voice_chat(request: ChatRequest):
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini API Key missing")
    try:
        # Define strict system instructions forcing it to use context
        sys_instruct = f"You are a helpful AI tutor. You must answer the student's question strictly based on the following document context. Do not say you cannot read a PDF. If the answer is not in the context, say 'I cannot find that in the document.'\n\nHare is the document context:\n{request.context}"
        
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.3
            )
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API Error: {str(e)}")

@app.post("/extract-image")
async def extract_image(file: UploadFile = File(...), ocr_model: str = Form("gemini")):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image.")
    try:
        content = await file.read()
        
        if ocr_model == "easyocr":
            if not reader:
                raise HTTPException(status_code=500, detail="EasyOCR is not installed or initialized.")
            
            # EasyOCR expects numpy array or file path
            image_np = np.array(Image.open(io.BytesIO(content)).convert('RGB'))
            result = reader.readtext(image_np, detail=0) # detail=0 returns only a list of text strings
            text = " ".join(result)
            return {"text": text.strip()}
            
        else: # Default to Gemini
            if not gemini_client:
                raise HTTPException(status_code=500, detail="Gemini API Key missing")
            
            image = Image.open(io.BytesIO(content))
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[image, "Extract all the text from this image exactly as it appears. Ensure paragraphs and line breaks are maintained where logical. Do not add any extra commentary. Just return the extracted text."]
            )
            return {"text": response.text.strip()}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image Extraction Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
