import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Conversion PDF -> Word
from pdf2docx import Converter

# Conversion Word -> PDF (Méthode Image/Canvas)
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="Format .docx requis")
    
    input_path = f"temp_{file.filename}"
    output_path = input_path.replace(".docx", ".pdf")
    
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Création du PDF avec une meilleure gestion graphique
        doc = Document(input_path)
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # On simule un rendu de page
        y_position = height - 1*inch
        
        for para in doc.paragraphs:
            # Gestion du style de base
            if para.style.name.startswith('Heading'):
                c.setFont("Helvetica-Bold", 16)
            else:
                c.setFont("Helvetica", 11)
                
            # Découpage du texte pour qu'il ne dépasse pas l'image de la page
            lines = [para.text[i:i+85] for i in range(0, len(para.text), 85)]
            
            for line in lines:
                if y_position < 1*inch:
                    c.showPage()
                    y_position = height - 1*inch
                    c.setFont("Helvetica", 11)
                
                c.drawString(1*inch, y_position, line)
                y_position -= 15
            
            y_position -= 10 # Espace entre paragraphes
            
        c.save()
        return FileResponse(output_path, filename=f"lowaconvert_{file.filename.replace('.docx', '.pdf')}")
        
    except Exception as e:
        return {"error": f"Erreur de rendu visuel : {str(e)}"}

# Garde ta route pdf-to-word actuelle ici...
