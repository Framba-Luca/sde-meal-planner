from typing import List, Dict, Any, Optional
from src.core.database import db_adapter
from src.schemas.recipe import CustomRecipeCreate

class RecipeService:
    def create_custom_recipe(self, recipe: CustomRecipeCreate) -> Optional[int]:
        """Create a custom recipe with ingredients."""
        query_recipe = """
            INSERT INTO custom_recipes 
            (user_id, name, category, area, instructions, image, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        query_ingredient = """
            INSERT INTO custom_recipe_ingredients 
            (recipe_id, ingredient_name, measure)
            VALUES (%s, %s, %s)
        """
        
        try:
            with db_adapter.get_cursor() as cur:
                # 1. Insert the main recipe
                cur.execute(query_recipe, (
                    recipe.user_id, recipe.name, recipe.category, 
                    recipe.area, recipe.instructions, recipe.image, recipe.tags
                ))
                result = cur.fetchone()
                if not result:
                    return None
                
                recipe_id = result['id']
                
                # 2. Insert ingredients (if present)
                for ingredient in recipe.ingredients:
                    cur.execute(query_ingredient, (
                        recipe_id, 
                        ingredient.get('name', ''), 
                        ingredient.get('measure', '')
                    ))
                
                return recipe_id
        except Exception as e:
            print(f"Error creating custom recipe: {e}")
            return None

    def get_custom_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a recipe and its ingredients by ID."""
        query_recipe = "SELECT * FROM custom_recipes WHERE id = %s"
        query_ingredients = "SELECT * FROM custom_recipe_ingredients WHERE recipe_id = %s"
        
        with db_adapter.get_cursor() as cur:
            cur.execute(query_recipe, (recipe_id,))
            recipe = cur.fetchone()
            
            if recipe:
                cur.execute(query_ingredients, (recipe_id,))
                ingredients = cur.fetchall()
                # Format ingredients to standardize output
                recipe['ingredients'] = [
                    {'name': i['ingredient_name'], 'measure': i['measure']} 
                    for i in ingredients
                ]
            
            return recipe

    def get_custom_recipes_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all recipes for a user (without ingredients for lightweight response)."""
        query = "SELECT * FROM custom_recipes WHERE user_id = %s ORDER BY created_at DESC"
        with db_adapter.get_cursor() as cur:
            cur.execute(query, (user_id,))
            return cur.fetchall()

    def update_custom_recipe(self, recipe_id: int, recipe_data: Dict[str, Any]) -> bool:
        """Update recipe fields (does not handle complex ingredient updates for now)."""
        # Dynamically build the query based on provided fields
        fields = []
        values = []
        
        allowed_fields = ['name', 'category', 'area', 'instructions', 'image', 'tags']
        
        for key in allowed_fields:
            if key in recipe_data:
                fields.append(f"{key} = %s")
                values.append(recipe_data[key])
        
        if not fields:
            return False
            
        values.append(recipe_id)
        query = f"UPDATE custom_recipes SET {', '.join(fields)} WHERE id = %s"
        
        try:
            with db_adapter.get_cursor() as cur:
                cur.execute(query, tuple(values))
                return cur.rowcount > 0
        except Exception as e:
            print(f"Error updating recipe: {e}")
            return False

    def delete_custom_recipe(self, recipe_id: int) -> bool:
        """Delete a recipe (ingredients are cascade deleted from the DB)."""
        query = "DELETE FROM custom_recipes WHERE id = %s"
        try:
            with db_adapter.get_cursor() as cur:
                cur.execute(query, (recipe_id,))
                return cur.rowcount > 0
        except Exception as e:
            print(f"Error deleting recipe: {e}")
            return False