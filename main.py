import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import JobApplication

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Job Tracker Backend is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# -----------------------------
# Schemas Introspection
# -----------------------------
class SchemaResponse(BaseModel):
    name: str
    collection: str
    schema: Dict[str, Any]
    description: Optional[str] = None


@app.get("/schema", response_model=List[SchemaResponse])
def get_schema():
    """Expose Pydantic model schemas for the database viewer"""
    models = [
        ("JobApplication", JobApplication),
    ]
    out: List[SchemaResponse] = []
    for name, model in models:
        try:
            schema = model.model_json_schema()
        except Exception:
            schema = {}
        out.append(
            SchemaResponse(
                name=name,
                collection=name.lower(),
                schema=schema,
                description=(model.__doc__ or "").strip() if hasattr(model, "__doc__") else None,
            )
        )
    return out


# -----------------------------
# Job Applications CRUD
# -----------------------------

class CreateJobApplication(JobApplication):
    pass


class UpdateJobApplication(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    job_link: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    applied_date: Optional[str] = None
    follow_up_date: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    resume_version: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


# helpers
from bson import ObjectId


def to_public(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    d["id"] = str(d.pop("_id")) if d.get("_id") else None
    # convert datetimes to isoformat
    for k, v in list(d.items()):
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


@app.get("/api/applications")
def list_applications(status: Optional[str] = None, q: Optional[str] = None, limit: int = 100):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt: Dict[str, Any] = {}
    if status:
        filt["status"] = status
    if q:
        # simple $or text search over a few fields
        filt["$or"] = [
            {"company": {"$regex": q, "$options": "i"}},
            {"position": {"$regex": q, "$options": "i"}},
            {"notes": {"$regex": q, "$options": "i"}},
            {"tags": {"$elemMatch": {"$regex": q, "$options": "i"}}},
        ]
    docs = get_documents("jobapplication", filt, limit)
    return [to_public(d) for d in docs]


@app.post("/api/applications", status_code=201)
def create_application(payload: CreateJobApplication):
    collection = "jobapplication"
    try:
        inserted_id = create_document(collection, payload)
        # fetch the created document to return
        doc = db[collection].find_one({"_id": ObjectId(inserted_id)})
        return to_public(doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/api/applications/{app_id}")
def update_application(app_id: str, payload: UpdateJobApplication):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        update_dict = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        update_dict["updated_at"] = datetime.utcnow()
        res = db.jobapplication.update_one({"_id": ObjectId(app_id)}, {"$set": update_dict})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Application not found")
        doc = db.jobapplication.find_one({"_id": ObjectId(app_id)})
        return to_public(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/applications/{app_id}", status_code=204)
def delete_application(app_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        res = db.jobapplication.delete_one({"_id": ObjectId(app_id)})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Application not found")
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
