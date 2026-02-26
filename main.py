import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Bibliothèques pour PDF -> Word
from pdf2docx import Converter

# Bibliothèques pour Word -> PDF (Solution 100% Python)
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

app = FastAPI(title="Lowaconvert Premium API")

# Configuration CORS pour ton interface Light Mode
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "online", "mode": "Python Native (No LibreOffice)"}

# --- ROUTE : PDF VERS WORD ---
@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Fichier PDF requis")
        
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

# --- ROUTE : WORD VERS PDF (Méthode de rendu par texte) ---
@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="Fichier Word (.docx) requis")
        
    input_path = f"temp_{file.filename}"
    output_path = input_path.replace(".docx", ".pdf")
    
    try:
        # 1. Sauvegarde temporaire du Word
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Lecture et conversion en PDF
        doc = Document(input_path)
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        y_position = height - 50 # Marge du haut
        
        c.setFont("Helvetica", 12)
        
        for para in doc.paragraphs:
            # Gestion du saut de page
            if y_position < 50:
                c.showPage()
                y_position = height - 50
                c.setFont("Helvetica", 12)
            
            # Dessine le texte du paragraphe
            # On limite à 90 caractères pour éviter que le texte sorte de la page
            text = para.text.strip()
            if text:
                c.drawString(50, y_position, text[:90])
                y_position -= 20 # Espacement entre lignes
            else:
                y_position -= 10 # Petit espace pour les lignes vides
                
        c.save()
        
        if os.path.exists(output_path):
            return FileResponse(output_path, filename=f"lowaconvert_{file.filename.replace('.docx', '.pdf')}")
        else:
            return {"error": "Échec de la génération du PDF."}
            
    except Exception as e:
        return {"error": f"Erreur de conversion : {str(e)}"}

if __name__ == "__main__":
    # Port dynamique pour Railway
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
        
