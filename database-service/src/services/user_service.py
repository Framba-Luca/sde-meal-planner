from typing import Optional, List
from sqlmodel import Session, select
from src.models.user_model import User
from src.schemas.user import UserCreate


class UserService:
    def __init__(self, session: Session):
        # Inject the session (active DB connection)
        self.session = session

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieves a user by username.
        Equivalent to: SELECT * FROM users WHERE username = '...'
        """
        statement = select(User).where(User.username == username)
        # .first() returns the first match or None
        return self.session.exec(statement).first()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Returns a paginated list of users.
        Equivalent to: SELECT * FROM users OFFSET skip LIMIT limit
        """
        statement = select(User).offset(skip).limit(limit)
        return self.session.exec(statement).all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieves a user by primary key.
        """
        return self.session.get(User, user_id)

    def create_user(self, user_in: UserCreate) -> User:
        """
        Creates a new user.
        No manual try/except is needed here: if an error occurs
        (e.g. duplicate username), SQLAlchemy will raise an exception
        that will be handled in the Router layer.
        """
        # Create the ORM model instance
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=user_in.hashed_password,
            is_active=True
        )

        # Add to the session
        self.session.add(db_user)
        # Persist to the database
        self.session.commit()
        # Refresh to get the generated ID and timestamps
        self.session.refresh(db_user)

        return db_user
