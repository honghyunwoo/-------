
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import schema
from app.models.team import Team, team_member_association
from app.models.user import User

def create_team(db: Session, team: schema.TeamCreate, owner: User) -> Team:
    """Create a new team with the user as the owner."""
    db_team = Team(name=team.name, owner_id=owner.id)
    db_team.members.append(owner)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

def get_team(db: Session, team_id: int) -> Optional[Team]:
    """Get a team by its ID."""
    return db.query(Team).filter(Team.id == team_id).first()

def get_user_teams(db: Session, user: User) -> List[Team]:
    """Get all teams a user is a member of."""
    return user.teams

def add_member_to_team(db: Session, team: Team, user: User, role: str = "member") -> Team:
    """Add a user to a team."""
    if user not in team.members:
        # The association object needs to be created explicitly if it has extra data
        # Here we don't have extra data on the association table itself in the model
        # so we can just append.
        team.members.append(user)
        db.commit()
        db.refresh(team)
    return team

def remove_member_from_team(db: Session, team: Team, user: User) -> Team:
    """Remove a user from a team."""
    if user in team.members and user.id != team.owner_id: # Owner cannot be removed
        team.members.remove(user)
        db.commit()
        db.refresh(team)
    return team

def delete_team(db: Session, team: Team, owner: User) -> Optional[Team]:
    """Delete a team. Only the owner can delete it."""
    if team.owner_id == owner.id:
        db.delete(team)
        db.commit()
        return team
    return None

