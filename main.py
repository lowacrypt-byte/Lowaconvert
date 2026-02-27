import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Bibliothèque pour PDF -> Word
from pdf2docx import Converter

# Bibliothèque Premium pour Word -> PDF (Rendu fidèle)
from spire.doc import Document, FileFormat

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
async def status():
    return {"status": "online", "engine": "Spire.Doc Engine"}

# --- ROUTE 1 : PDF VERS WORD ---
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
        
        return FileResponse(output_path, filename=f"lowaconvert_{os.path.basename(output_path)}")
    except Exception as e:
        return {"error": f"Erreur PDF-to-Word: {str(e)}"}

# --- ROUTE 2 : WORD VERS PDF (Méthode de rendu visuel complet) ---
@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Format Word requis")
    
    input_path = f"temp_{file.filename}"
    output_path = input_path.rsplit('.', 1)[0] + ".pdf"
    
    try:
        # 1. Sauvegarde du fichier uploadé
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Utilisation du moteur de rendu Spire.Doc
        # Ce moteur convertit le document en respectant la mise en page (images, tableaux)
        doc = Document()
        doc.LoadFromFile(input_path)
        
        # Sauvegarde directe au format PDF
        doc.SaveToFile(output_path, FileFormat.PDF)
        doc.Close()
        
        if os.path.exists(output_path):
            return FileResponse(output_path, filename=f"lowaconvert_{os.path.basename(output_path)}")
        else:
            return {"error": "Le moteur n'a pas pu générer le fichier PDF."}
            
    except Exception as e:
        # Capture de l'erreur pour éviter le "Failed to fetch"
        return {"error": f"Erreur de rendu visuel : {str(e)}"}
    finally:
        # Nettoyage des fichiers temporaires pour économiser l'espace Railway
        if os.path.exists(input_path):
            os.remove(input_path)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
        
