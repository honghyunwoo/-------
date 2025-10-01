
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import schema
from app.models.template import Template
from app.models.user import User
from app.utils import cache

def create_template(db: Session, template: schema.TemplateCreate, user: User) -> Template:
    """Create a new template for a user."""
    db_template = Template(
        **template.model_dump(),
        user_id=user.id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def get_template(db: Session, template_id: int) -> Optional[schema.Template]:
    """Get a template by its ID."""
    cache_key = f"template:{template_id}"
    cached_template = cache.get_cache(cache_key)
    if cached_template:
        return schema.Template(**cached_template)

    db_template = db.query(Template).filter(Template.id == template_id).first()
    if db_template:
        template_schema = schema.Template.from_orm(db_template)
        cache.set_cache(cache_key, template_schema.model_dump())
        return template_schema
    return None

def get_templates(
    db: Session, user_id: Optional[int] = None, category: Optional[str] = None, skip: int = 0, limit: int = 100
) -> List[schema.Template]:
    """Get a list of templates."""
    # Only cache public templates for simplicity
    if user_id is None:
        cache_key = f"templates:public:category={category}:skip={skip}:limit={limit}"
        cached_templates = cache.get_cache(cache_key)
        if cached_templates:
            return [schema.Template(**t) for t in cached_templates]

    query = db.query(Template)
    # Public templates (user_id is None) or user's own templates
    if user_id:
        query = query.filter((Template.user_id == user_id) | (Template.user_id == None))
    else:
        # If no user is specified, only show public templates
        query = query.filter(Template.user_id == None)

    if category:
        query = query.filter(Template.category == category)
    
    db_templates = query.offset(skip).limit(limit).all()
    
    # Convert to Pydantic schemas
    templates_schema = [schema.Template.from_orm(t) for t in db_templates]

    if user_id is None and templates_schema:
        templates_dict = [t.model_dump() for t in templates_schema]
        cache.set_cache(cache_key, templates_dict)

    return templates_schema

def delete_template(db: Session, template_id: int, user: User) -> Optional[Template]:
    """Delete a user's custom template."""
    db_template = db.query(Template).filter(Template.id == template_id, Template.user_id == user.id).first()
    if db_template:
        db.delete(db_template)
        db.commit()
    return db_template

