from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, or_
from datetime import datetime

from src.models.review_model import Review
from src.models.user_model import User
from src.models.recipe_model import Recipe

class ReviewService:
    def __init__(self, session: Session):
        self.session = session

    def create_review(self, user_id: int, recipe_id: int, rating: int, comment: str, created_at: Optional[datetime] = None) -> int:
        if not created_at:
            created_at = datetime.utcnow()
        db_review = Review(user_id=user_id, recipe_id=recipe_id, rating=rating, comment=comment, created_at=created_at)
        self.session.add(db_review)
        self.session.commit()
        self.session.refresh(db_review)
        return db_review.id

    def get_reviews_by_recipe(self, recipe_identifier: str, search_mode: str = "auto") -> List[Dict[str, Any]]:
        """
        Retrieves reviews ensuring no ID collision.
        :param search_mode: 'external' (API recipes), 'internal' (Custom recipes), or 'auto' (Try both - risky)
        """
        
        statement = select(Recipe)
        
        if search_mode == "external":
            statement = statement.where(Recipe.external_id == str(recipe_identifier))
            
        elif search_mode == "internal":
            if not str(recipe_identifier).isdigit():
                return []
            statement = statement.where(Recipe.id == int(recipe_identifier))
            
        else:
            conditions = [Recipe.external_id == str(recipe_identifier)]
            if str(recipe_identifier).isdigit():
                conditions.append(Recipe.id == int(recipe_identifier))
            statement = statement.where(or_(*conditions))

        recipe = self.session.exec(statement).first()

        if not recipe:
            return []
        
        # 2. JOIN REVIEW + USER
        statement_reviews = (
            select(Review, User.username)
            .join(User, Review.user_id == User.id)
            .where(Review.recipe_id == recipe.id)
            .order_by(Review.created_at.desc())
        )
        
        results = self.session.exec(statement_reviews).all()

        response_data = []
        for review, username in results:
            r_dict = review.model_dump()
            r_dict["username"] = username if username else "Unknown"
            response_data.append(r_dict)

        return response_data

    def get_review_by_id(self, review_id: int) -> Optional[Review]:
        return self.session.get(Review, review_id)

    def delete_review_raw(self, review_id: int) -> bool:
        review = self.session.get(Review, review_id)
        if not review:
            return False
        self.session.delete(review)
        self.session.commit()
        return True