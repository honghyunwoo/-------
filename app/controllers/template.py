
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import schema
from app.models.user import User
from app.services import auth, template as template_service

router = APIRouter()

@router.post("/", response_model=schema.Template)
def create_template(
    template: schema.TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    """Create a new template for the current user."""
    return template_service.create_template(db=db, template=template, user=current_user)

@router.get("/", response_model=List[schema.Template])
def read_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth.get_current_user) # To show user-specific templates
):
    """Retrieve templates. Shows public templates and user's own templates."""
    templates = template_service.get_templates(db, user_id=current_user.id, category=category, skip=skip, limit=limit)
    return templates

@router.get("/{template_id}", response_model=schema.Template)
def read_template(template_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific template by its ID."""
    db_template = template_service.get_template(db, template_id=template_id)
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    # Basic check: non-public templates can only be accessed by owner, but that logic is better in the service
    return db_template

@router.delete("/{template_id}", response_model=schema.Template)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    """Delete a user's custom template."""
    db_template = template_service.delete_template(db, template_id=template_id, user=current_user)
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found or you do not have permission to delete it")
    return db_template

