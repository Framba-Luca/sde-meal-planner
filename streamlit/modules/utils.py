def get_ingredients_list(meal):
    """
    Extract and format the ingredient list ingredienti from a past object.
    """
    final_list = []

    if "ingredients" in meal and isinstance(meal["ingredients"], list):
        for item in meal["ingredients"]:
            if not isinstance(item, dict):
                continue

            
            ing_name = (item.get("ingredient") or item.get("name") or "").strip()
            meas = (item.get("measure") or "").strip()
            
            if ing_name:
                # Se c'è la misura, aggiungiamo uno spazio dopo, altrimenti stringa vuota
                meas_part = f"{meas} " if meas else ""
                final_list.append(f"• {meas_part}{ing_name}")
        
        # Se abbiamo trovato ingredienti con questo metodo, usiamo questi e ci fermiamo.
        if final_list:
            return final_list

    for i in range(1, 21):
        ing_key = f"strIngredient{i}"
        meas_key = f"strMeasure{i}"
        
        raw_ing = meal.get(ing_key)
        raw_meas = meal.get(meas_key)

        clean_ing = (raw_ing or "").strip()
        clean_meas = (raw_meas or "").strip()

        if clean_ing:
            meas_part = f"{clean_meas} " if clean_meas else ""
            final_list.append(f"• {meas_part}{clean_ing}")
            
    return final_list