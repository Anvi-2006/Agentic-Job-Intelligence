from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.core.database import SessionLocal
from backend.app.services.resume_processing_service import process_resume

router = APIRouter(
    prefix="/api/resumes",
    tags=["Resume Upload"],
)

UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/{candidate_id}/upload")
async def upload_resume(
    candidate_id: UUID,
    file: UploadFile = File(...),
):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF resumes are supported.",
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Resume file must be smaller than 5 MB.",
        )

    safe_filename = f"{candidate_id}_resume.pdf"
    file_path = UPLOAD_DIR / safe_filename

    file_path.write_bytes(contents)

    db = SessionLocal()

    try:
        result = process_resume(
            db=db,
            candidate_id=candidate_id,
            file_name=file.filename or safe_filename,
            file_path=str(file_path),
        )

        return {
            "message": "Resume uploaded and processed successfully.",
            "candidate_id": str(candidate_id),
            "filename": safe_filename,
            "file_size": len(contents),
            "file_path": str(file_path),
            "processing": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Resume processing failed: {str(exc)}",
        )

    finally:
        db.close()