
from sqlalchemy.orm import Session

from app.models import schema
from app.models.branding import Branding
from app.models.user import User
from app.utils import watermark

def get_branding(db: Session, user: User) -> Branding:
    """Get or create a branding profile for a user."""
    db_branding = db.query(Branding).filter(Branding.user_id == user.id).first()
    if not db_branding:
        db_branding = Branding(user_id=user.id)
        db.add(db_branding)
        db.commit()
        db.refresh(db_branding)
    return db_branding

def update_branding(db: Session, user: User, branding_data: schema.BrandingCreate) -> Branding:
    """Update a user's branding profile."""
    db_branding = get_branding(db, user)
    for key, value in branding_data.model_dump(exclude_unset=True).items():
        setattr(db_branding, key, value)
    db.commit()
    db.refresh(db_branding)
    return db_branding

def apply_branding_to_video(db: Session, user: User, video_path: str, output_path: str):
    """Applies the user's branding to a video."""
    branding_profile = get_branding(db, user)

    if branding_profile.logo_image_path:
        # This assumes the path is a local path. In a real system, this might be a URL
        # that needs to be downloaded first.
        watermark.add_watermark_to_video(
            video_path=video_path,
            watermark_path=branding_profile.logo_image_path,
            output_path=output_path
        )
        return output_path
    
    # You could also add text watermarks based on brand colors/fonts as a fallback

    return video_path # Return original path if no branding applied

