"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import date

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Add your own schemas here:
# --------------------------------------------------

class JobApplication(BaseModel):
    """
    Job applications you have applied to
    Collection name: "jobapplication"
    """
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Role or job title")
    location: Optional[str] = Field(None, description="Job location (City, Country or Remote)")
    job_link: Optional[str] = Field(None, description="URL to the job posting")
    source: Optional[str] = Field(None, description="Where you found it (LinkedIn, Referral, etc.)")
    status: str = Field(
        "applied",
        description="Application status",
    )  # applied, interviewing, offer, rejected, ghosted, saved
    applied_date: Optional[date] = Field(None, description="Date you applied")
    follow_up_date: Optional[date] = Field(None, description="Planned follow-up date")
    salary_min: Optional[float] = Field(None, ge=0, description="Min salary expectation")
    salary_max: Optional[float] = Field(None, ge=0, description="Max salary expectation")
    contact_name: Optional[str] = Field(None, description="Recruiter or contact name")
    contact_email: Optional[str] = Field(None, description="Recruiter or contact email")
    resume_version: Optional[str] = Field(None, description="Which resume version you sent")
    priority: Optional[str] = Field("medium", description="low, medium, high, urgent")
    tags: List[str] = Field(default_factory=list, description="Labels for filtering")
    notes: Optional[str] = Field(None, description="Any notes about this application")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
