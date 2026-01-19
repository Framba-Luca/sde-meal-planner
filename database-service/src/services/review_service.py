from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from datetime import datetime

from src.models.review_model import Review
from src.models.user_model import User  # Needed to JOIN and retrieve the username


class ReviewService:
    def __init__(self, session: Session):
        self.session = session

    def create_review(
        self,
        user_id: int,
        recipe_id: int,
        rating: int,
        comment: str,
        created_at: Optional[datetime] = None
    ) -> int:
        if not created_at:
            created_at = datetime.utcnow()

        db_review = Review(
            user_id=user_id,
            recipe_id=recipe_id,
            rating=rating,
            comment=comment,
            created_at=created_at
        )
        self.session.add(db_review)
        self.session.commit()
        self.session.refresh(db_review)
        return db_review.id

    def get_reviews_by_recipe(self, recipe_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves reviews and performs a JOIN with User to get the username.
        Returns a list of dictionaries compatible with the ReviewResponse schema.
        """
        # SELECT reviews.*, users.username FROM reviews JOIN users ON ...
        statement = (
            select(Review, User.username)
            .join(User)
            .where(Review.recipe_id == recipe_id)
            .order_by(Review.created_at.desc())
        )

        results = self.session.exec(statement).all()

        # SQLModel returns a list of tuples: (ReviewObject, username_string)
        # Convert them into a flat structure suitable for Pydantic
        output = []
        for review, username in results:
            # Convert the Review object to dict and add the username
            review_dict = review.model_dump()
            review_dict["username"] = username
            output.append(review_dict)

        return output

    def get_review_by_id(self, review_id: int) -> Optional[Review]:
        return self.session.get(Review, review_id)

    def delete_review_raw(self, review_id: int) -> bool:
        review = self.session.get(Review, review_id)
        if not review:
            return False
        self.session.delete(review)
        self.session.commit()
        return True
