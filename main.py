import os
import shutil
import subprocess
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        return FileResponse(output_path, filename=os.path.basename(output_path))
    except Exception as e:
        return {"error": str(e)}

@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    input_path = f"temp_{file.filename}"
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # On essaie 'libreoffice', et si ça rate, on essaie 'soffice'
        cmd = "libreoffice"
        if shutil.which("soffice"):
            cmd = "soffice"
            
        subprocess.run([
            cmd, "--headless", "--convert-to", "pdf", 
            input_path, "--outdir", "."
        ], check=True)
        
        output_path = input_path.rsplit('.', 1)[0] + ".pdf"
        return FileResponse(output_path, filename=os.path.basename(output_path))
    except Exception as e:
        # On renvoie l'erreur détaillée pour comprendre le problème
        return {"error": f"Erreur système : {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
