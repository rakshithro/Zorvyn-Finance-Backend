from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import user_service
from app.core.security import require_roles, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

# only admins will have the access to manage the users
admin_only = require_roles("admin")


@router.get("/", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(admin_only),
):
    """List all users. Admin only."""
    return user_service.get_all_users(db, skip=skip, limit=limit)


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _=Depends(admin_only),
):
    """Create a user with any role. Admin only."""
    return user_service.create_user(db, data)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a user by ID. Admins can view any user; others can only view themselves."""
    if current_user.role != "admin" and current_user.id != user_id:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return user_service.get_user_by_id(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _=Depends(admin_only),
):
    """Update user role or status. Admin only."""
    return user_service.update_user(db, user_id, data)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(admin_only),
):
    """Delete a user. Admin only."""
    user_service.delete_user(db, user_id)