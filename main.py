import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Bibliothèques pour PDF -> Word
from pdf2docx import Converter

# Bibliothèques pour Word -> PDF (Solution 100% Python Native)
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

app = FastAPI(title="Lowaconvert API")

# CONFIGURATION CORS : C'est ce qui règle le "Failed to fetch"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Autorise ton site à parler au serveur
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health():
    return {"status": "online", "message": "Lowaconvert est prêt !"}

# --- ROUTE : PDF VERS WORD ---
@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    input_path = f"temp_{file.filename}"
    output_path = input_path.replace(".pdf", ".docx")
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        cv = Converter(input_path)
        cv.convert(output_path)
        cv.close()
        return FileResponse(output_path, filename=f"lowaconvert_{file.filename.replace('.pdf', '.docx')}")
    except Exception as e:
        return {"error": str(e)}

# --- ROUTE : WORD VERS PDF (Méthode Python Native) ---
@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="Fichier .docx requis")
    
    input_path = f"temp_{file.filename}"
    output_path = input_path.replace(".docx", ".pdf")
    
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        doc = Document(input_path)
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        y = height - 50
        
        c.setFont("Helvetica", 12)
        for para in doc.paragraphs:
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 12)
            
            text = para.text.strip()
            if text:
                c.drawString(50, y, text[:90])
                y -= 20
        c.save()
        
        return FileResponse(output_path, filename=f"lowaconvert_{file.filename.replace('.docx', '.pdf')}")
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
