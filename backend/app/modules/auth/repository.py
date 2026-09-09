"""
AegisAI Auth Module â€” User Repository.

The repository pattern isolates all database access from business logic.
This makes the service layer testable in isolation and enables swapping
the persistence layer without touching service code.
"""

from sqlalchemy.orm import Session

from app.modules.auth.models import User


class UserRepository:
    """
    Data access layer for the `users` table.

    All query methods are explicit and typed â€” no magic or dynamic queries.
    Every method handles only a single responsibility.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user by primary key.

        Args:
            user_id: Integer primary key.

        Returns:
            User instance or None if not found.
        """
        return self._db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email address (case-sensitive).

        Args:
            email: Lowercase email address.

        Returns:
            User instance or None.
        """
        return self._db.query(User).filter(User.email == email.lower()).first()

    def create(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str = "CITIZEN",
    ) -> User:
        """
        Persist a new user record.

        Args:
            name: Full name.
            email: Unique email address (stored lowercase).
            password_hash: Bcrypt-hashed password â€” NEVER the plain text.
            role: Platform role string.

        Returns:
            Persisted User instance with populated `id` and timestamps.
        """
        user = User(
            name=name.strip(),
            email=email.lower(),
            password_hash=password_hash,
            role=role.upper(),
            is_active=True,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role_filter: str | None = None,
        active_only: bool = False,
    ) -> tuple[list[User], int]:
        """
        Retrieve a paginated list of users.

        Args:
            skip: Number of records to skip (offset).
            limit: Maximum records to return.
            role_filter: If set, filter by this role.
            active_only: If True, return only active users.

        Returns:
            Tuple of (list of User, total count).
        """
        query = self._db.query(User)

        if role_filter:
            query = query.filter(User.role == role_filter.upper())
        if active_only:
            query = query.filter(User.is_active.is_(True))

        total = query.count()
        users = query.order_by(User.id).offset(skip).limit(limit).all()
        return users, total

    def update_role(self, user_id: int, role: str) -> User | None:
        """
        Update a user's platform role.

        Args:
            user_id: Target user's primary key.
            role: New role string.

        Returns:
            Updated User instance or None if not found.
        """
        user = self.get_by_id(user_id)
        if user is None:
            return None
        user.role = role.upper()
        self._db.commit()
        self._db.refresh(user)
        return user

    def deactivate(self, user_id: int) -> User | None:
        """
        Soft-deactivate a user account (sets is_active=False).

        Args:
            user_id: Target user's primary key.

        Returns:
            Updated User instance or None if not found.
        """
        user = self.get_by_id(user_id)
        if user is None:
            return None
        user.is_active = False
        self._db.commit()
        self._db.refresh(user)
        return user

    def reactivate(self, user_id: int) -> User | None:
        """Reactivate a previously deactivated user account."""
        user = self.get_by_id(user_id)
        if user is None:
            return None
        user.is_active = True
        self._db.commit()
        self._db.refresh(user)
        return user
