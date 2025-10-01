
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import schema
from app.models.user import User
from app.services import auth, team as team_service

router = APIRouter()

@router.post("/", response_model=schema.Team)
def create_team(
    team: schema.TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    """Create a new team, with the current user as the owner."""
    return team_service.create_team(db=db, team=team, owner=current_user)

@router.get("/", response_model=List[schema.Team])
def read_user_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    """Get all teams the current user is a member of."""
    return team_service.get_user_teams(db=db, user=current_user)

@router.get("/{team_id}", response_model=schema.Team)
def read_team(team_id: int, db: Session = Depends(get_db)):
    """Get a specific team by ID."""
    db_team = team_service.get_team(db, team_id=team_id)
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return db_team

@router.post("/{team_id}/members", response_model=schema.Team)
def add_team_member(
    team_id: int,
    member: schema.TeamMember,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    db_team = team_service.get_team(db, team_id=team_id)
    if not db_team or db_team.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add members to this team")
    
    # You would typically look up the user by email or ID
    # For simplicity, we assume user_id is passed directly
    member_user = db.query(User).filter(User.id == member.user_id).first()
    if not member_user:
        raise HTTPException(status_code=404, detail="User to be added not found")

    return team_service.add_member_to_team(db, db_team, member_user, member.role)

# Additional endpoints for removing members, deleting teams etc. can be added here

