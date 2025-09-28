from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import base64
from typing import List

app = FastAPI(title="Lovable PDF Parser")

# Enable CORS so frontend can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Lovable PDF parser is running!"}

@app.post("/parse-pdf/")
async def parse_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        text_content = ""
        metadata = {}
        num_pages = 0
        tables: List[List[List[str]]] = []  # List of tables per page
        images: List[str] = []  # Base64 encoded images

        with pdfplumber.open(file.file) as pdf:
            num_pages = len(pdf.pages)
            metadata = pdf.metadata or {}
            
            for page in pdf.pages:
                # Extract text
                text_content += page.extract_text() or ""
                
                # Extract tables
                page_tables = page.extract_tables()
                for table in page_tables:
                    tables.append(table)
                
                # Extract images
                for img in page.images:
                    # Crop the image from the page
                    cropped = page.within_bbox((img['x0'], img['top'], img['x1'], img['bottom']))
                    img_obj = cropped.to_image(resolution=150)
                    # Convert to base64 string
                    img_bytes = img_obj.original.save(None, format="PNG")
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    images.append(img_base64)
        
        return {
            "filename": file.filename,
            "num_pages": num_pages,
            "metadata": metadata,
            "text": text_content,
            "tables": tables,
            "images_base64": images  # You can decode this in frontend to display
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")
