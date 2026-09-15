from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate


def create_user(
    db: Session,
    user_data: UserCreate,
) -> User:

    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user(
    db: Session,
    user_id,
) -> User | None:

    return db.get(User, user_id)