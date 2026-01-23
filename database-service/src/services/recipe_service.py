from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from src.models.recipe_model import Recipe, RecipeIngredient
from src.schemas.recipe import CustomRecipeCreate, RecipeUpdate


class RecipeService:
    def __init__(self, session: Session):
        self.session = session

    def create_custom_recipe(self, recipe_in: CustomRecipeCreate) -> Recipe:
        # 1. Prepare ingredient data
        # Pydantic guarantees that 'ing' is an IngredientCreate object, not a dict.
        # We map the 'name' field from the schema to 'ingredient_name' in the DB model.
        db_ingredients = [
            RecipeIngredient(
                ingredient_name=ing.name,
                measure=ing.measure
            ) for ing in recipe_in.ingredients
        ]

        # 2. Create Recipe object
        # Exclude 'ingredients' from the dump because we handle them as a relationship
        recipe_data = recipe_in.model_dump(exclude={"ingredients"})

        # Automatic unpacking of fields (name, category, area, etc.)
        db_recipe = Recipe(**recipe_data)
        db_recipe.is_custom = True

        # 3. Associate relationship
        db_recipe.ingredients = db_ingredients

        # 4. Persist to database
        self.session.add(db_recipe)
        self.session.commit()
        self.session.refresh(db_recipe)

        return db_recipe

    def update_custom_recipe(self, recipe_id: int, recipe_update: RecipeUpdate) -> Optional[Recipe]:
        db_recipe = self.session.get(Recipe, recipe_id)
        if not db_recipe:
            return None

        # Retrieve only fields that are set (ignore None values)
        update_data = recipe_update.model_dump(exclude_unset=True)

        # 1. Ingredient handling (if present in the update)
        if "ingredients" in update_data:
            # Remove ingredients from the "simple" fields to update
            new_ingredients_data = update_data.pop("ingredients")

            # Overwrite the ingredient list.
            # SQLModel/SQLAlchemy will handle removal of old ones
            # and insertion of new ones.
            # Note: new_ingredients_data is a list of DICTS because it comes from model_dump()
            db_recipe.ingredients = [
                RecipeIngredient(
                    ingredient_name=ing["name"],
                    measure=ing.get("measure")
                ) for ing in new_ingredients_data
            ]

        # 2. Automatic update of remaining fields
        # sqlmodel_update applies changes to the existing object
        db_recipe.sqlmodel_update(update_data)

        self.session.add(db_recipe)
        self.session.commit()
        self.session.refresh(db_recipe)
        return db_recipe

    def get_custom_recipe_by_id(self, recipe_id: int) -> Optional[Recipe]:
        statement = select(Recipe).where(Recipe.id == recipe_id)
        return self.session.exec(statement).first()

    def get_recipe(
        self, 
        query: Optional[str] = None, 
        category: Optional[str] = None, 
        area: Optional[str] = None, 
        ingredient: Optional[str] = None
    ) -> List[Recipe]:
        statement = select(Recipe)

        if ingredient:
            statement = statement.join(RecipeIngredient)
            statement = statement.where(RecipeIngredient.ingredient_name.ilike(f"%{ingredient}%"))

        if query:
            statement = statement.where(Recipe.name.ilike(f"%{query}%"))

        if category:
            statement = statement.where(Recipe.category.ilike(category))

        # 4. Filtro per Area
        if area:
            statement = statement.where(Recipe.area.ilike(area))
        statement = statement.distinct()

        return self.session.exec(statement).all()

    def get_recipe_by_external_id(self, external_id: str) -> Optional[Recipe]:
        statement = select(Recipe).where(Recipe.external_id == external_id)
        return self.session.exec(statement).first()

    def get_recipes_by_user(self, user_id: int) -> List[Recipe]:
        statement = select(Recipe).where(Recipe.user_id == user_id)
        return self.session.exec(statement).all()

    def delete_custom_recipe(self, recipe_id: int) -> bool:
        recipe = self.session.get(Recipe, recipe_id)
        if not recipe:
            return False
        self.session.delete(recipe)
        self.session.commit()
        return True

    def create_shadow_recipe(self, recipe_data: Dict[str, Any]) -> int:
        # Here you could optimize by using unpacking if recipe_data were a Pydantic object,
        # but since it is a raw Dict, the current manual approach is safer.
        existing = self.get_recipe_by_external_id(str(recipe_data.get("external_id")))
        if existing:
            return existing.id

        # Initial attempt using ** unpacking (only safe if keys match model fields)
        shadow_recipe = Recipe(
            **recipe_data,
            is_custom=False
        )

        # Manual overwrite for safety in case external data is "dirty"
        # (This mirrors your original logic)
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
