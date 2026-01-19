from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from src.models.recipe_model import Recipe, RecipeIngredient
from src.schemas.recipe import CustomRecipeCreate


class RecipeService:
    def __init__(self, session: Session):
        self.session = session

    def create_custom_recipe(self, recipe_in: CustomRecipeCreate) -> int:
        # 1. Create the Recipe object
        db_recipe = Recipe(
            user_id=recipe_in.user_id,
            name=recipe_in.name,
            category=recipe_in.category,
            area=recipe_in.area,
            instructions=recipe_in.instructions,
            image=recipe_in.image,
            tags=recipe_in.tags,
            is_custom=True
        )

        # 2. Handle ingredients (automatic relationship handling)
        # recipe_in.ingredients is a list of dicts:
        # [{'name': 'Pasta', 'measure': '500g'}]
        for ing_data in recipe_in.ingredients:
            ingredient = RecipeIngredient(
                ingredient_name=ing_data.get("name", ""),
                measure=ing_data.get("measure", "")
            )
            # Add to the parent's 'ingredients' list
            db_recipe.ingredients.append(ingredient)

        # 3. Single save operation (SQLAlchemy handles parent-child transaction)
        self.session.add(db_recipe)
        self.session.commit()
        self.session.refresh(db_recipe)

        return db_recipe.id

    def get_custom_recipe_by_id(self, recipe_id: int) -> Optional[Recipe]:
        # SQLModel automatically loads ingredients when accessed,
        # but for performance it may be better to explicitly join
        # if they are needed immediately, or rely on default lazy loading.
        return self.session.get(Recipe, recipe_id)

    def get_recipe_by_external_id(self, external_id: str) -> Optional[Recipe]:
        statement = select(Recipe).where(Recipe.external_id == external_id)
        return self.session.exec(statement).first()

    def get_recipes_by_user(self, user_id: int) -> List[Recipe]:
        statement = select(Recipe).where(Recipe.user_id == user_id)
        return self.session.exec(statement).all()

    def create_shadow_recipe(self, recipe_data: Dict[str, Any]) -> int:
        """
        Creates or updates a Shadow Recipe (cached from an external API).
        """
        # Check if it already exists
        existing = self.get_recipe_by_external_id(str(recipe_data.get("external_id")))

        if existing:
            return existing.id

        # If it does not exist, create a new one
        shadow_recipe = Recipe(
            name=recipe_data.get("name"),
            image=recipe_data.get("image"),
            external_id=str(recipe_data.get("external_id")),
            category=recipe_data.get("category"),
            area=recipe_data.get("area"),
            is_custom=False
        )
        self.session.add(shadow_recipe)
        self.session.commit()
        self.session.refresh(shadow_recipe)
        return shadow_recipe.id

    def delete_custom_recipe(self, recipe_id: int) -> bool:
        recipe = self.session.get(Recipe, recipe_id)
        if not recipe:
            return False
        # Cascade delete will also remove related ingredients
        self.session.delete(recipe)
        self.session.commit()
        return True
