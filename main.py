# uvicorn main:app --reload for running
# after running add /docs after link
# /docs
# /generate-core-timetable/
# /generate-elective-timetable/

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from Core import TimetableGenerator as CoreTimetable
from Electives import ElectivesManager as ElectiveGenerator
import os
import shutil
from typing import List

app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/download-timetable/")
async def download_timetable():
    file_path = os.path.join("Ultimate_12File_Timetable.xlsx")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename="Ultimate_12File_Timetable.xlsx", 
                          media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        return JSONResponse(status_code=404, content={"error": "File not found."})

# ---------------------------------------
# ---------- CORE TIMETABLE -------------
# ---------------------------------------
@app.post("/generate-timetable/")
async def generate_timetable(files: List[UploadFile] = File(...)):
    """
    Generate timetable from multiple Excel files
    """
    try:
        # Clear upload directory first
        for existing_file in os.listdir(UPLOAD_DIR):
            if existing_file.startswith("core_"):
                os.remove(os.path.join(UPLOAD_DIR, existing_file))
        
        uploaded_file_paths = []
        
        # Save all uploaded files
        for i, file in enumerate(files):
            # Validate file extension
            if not file.filename.endswith(('.xlsx', '.xls')):
                return JSONResponse(status_code=400, 
                                  content={"error": f"Invalid file type: {file.filename}. Only Excel files are allowed."})
            
            temp_path = os.path.join(UPLOAD_DIR, f"core_{i}_{file.filename}")
            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            uploaded_file_paths.append(temp_path)
            print(f"📂 Uploaded file {i+1} saved at: {temp_path}")

        print(f"📊 Total files uploaded: {len(uploaded_file_paths)}")

        # Initialize the generator
        generator = CoreTimetable()
        
        # Load all uploaded files into the generator
        print("🚀 Running timetable generation with multiple files...")
        generator.run(uploaded_file_paths)

        # Check for output file
        output_file = os.path.join(OUTPUT_DIR, "Ultimate_12File_Timetable.xlsx")
        
        # Also check in current directory (as per your original code)
        if not os.path.exists(output_file):
            output_file = "Ultimate_12File_Timetable.xlsx"
        
        print(f"📂 Checking for output file at: {output_file}")

        if os.path.exists(output_file):
            print("✅ Output file found!")
            return FileResponse(output_file, filename="Ultimate_12File_Timetable.xlsx", 
                              media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            print("❌ Output file not found!")
            return JSONResponse(status_code=500, 
                              content={"error": "Output file not found after generation."})
            
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# Alternative endpoint for single file (backward compatibility)
@app.post("/generate-timetable-single/")
async def generate_timetable_single(file: UploadFile = File(...)):
    """
    Generate timetable from a single Excel file (backward compatibility)
    """
    return await generate_timetable([file])

# ---------------------------------------
# -------- ELECTIVE GENERATION ---------
# ---------------------------------------
@app.post("/generate-electives/")
async def generate_electives(files: List[UploadFile] = File(None)):
    """
    Generate electives from multiple files (optional)
    """
    try:
        if files and files[0].filename:  # Check if files were uploaded
            # Save uploaded files for electives
            uploaded_file_paths = []
            for i, file in enumerate(files):
                if not file.filename.endswith(('.xlsx', '.xls')):
                    return JSONResponse(status_code=400, 
                                      content={"error": f"Invalid file type: {file.filename}"})
                
                temp_path = os.path.join(UPLOAD_DIR, f"elective_{i}_{file.filename}")
                with open(temp_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                uploaded_file_paths.append(temp_path)
            
            # Pass files to generator if your ElectiveGenerator supports it
            generator = ElectiveGenerator()
            # Assuming your generator can accept file paths
            if hasattr(generator, 'load_files'):
                generator.load_files(uploaded_file_paths)
            generator.generate_electives()
        else:
            # Use default files
            generator = ElectiveGenerator()
            generator.generate_electives()
            
        return {"message": "Electives generated successfully."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/generate-elective-timetable/")
async def generate_elective_timetable(files: List[UploadFile] = File(None)):
    """
    Generate elective timetable from multiple files (optional)
    """
    try:
        if files and files[0].filename:  # Check if files were uploaded
            uploaded_file_paths = []
            for i, file in enumerate(files):
                if not file.filename.endswith(('.xlsx', '.xls')):
                    return JSONResponse(status_code=400, 
                                      content={"error": f"Invalid file type: {file.filename}"})
                
                temp_path = os.path.join(UPLOAD_DIR, f"elective_tt_{i}_{file.filename}")
                with open(temp_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                uploaded_file_paths.append(temp_path)
            
            generator = ElectiveGenerator()
            if hasattr(generator, 'load_files'):
                generator.load_files(uploaded_file_paths)
            generator.generate_timetable()
        else:
            generator = ElectiveGenerator()
            generator.generate_timetable()
            
        return {"message": "Elective timetable generated successfully."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------------------------------------
# -------- UTILITY ENDPOINTS -----------
# ---------------------------------------
@app.get("/")
async def root():
    return {"message": "Timetable Generator API", 
            "docs": "/docs",
            "endpoints": {
                "generate_timetable": "/generate-timetable/ (multiple files)",
                "generate_timetable_single": "/generate-timetable-single/ (single file)",
                "generate_electives": "/generate-electives/",
                "generate_elective_timetable": "/generate-elective-timetable/",
                "download": "/download-timetable/"
            }}

@app.delete("/clear-uploads/")
async def clear_uploads():
    """Clear all uploaded files"""
    try:
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            os.remove(file_path)
        return {"message": "Upload directory cleared successfully."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})