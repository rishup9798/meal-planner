from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
engine = create_engine(os.getenv("DATABASE_URL"))

HTML = """<!DOCTYPE html>
<html>
<head><title>Meal Planner</title></head>
<body>
<h1 style="color:green">UI IS WORKING!</h1>
<p>Database test: <span id="db"></span></p>
<script>
fetch('/recipes').then(r=>r.json()).then(d=>{
  document.getElementById('db').textContent = 'Connected! Recipes: ' + d.length;
}).catch(e=>{
  document.getElementById('db').textContent = 'DB Error: ' + e;
});
</script>
</body>
</html>"""

@app.route("/")
def home():
    return jsonify({"message": "Meal Planner API is live!"})

@app.route("/ui")
def ui():
    return HTML, 200, {"Content-Type": "text/html"}

@app.route("/recipes", methods=["GET"])
def get_recipes():
    try:
        with engine.connect() as c:
            rows = c.execute(text("SELECT * FROM recipes")).fetchall()
            return jsonify([dict(r._mapping) for r in rows])
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/recipes", methods=["POST"])
def add_recipe():
    try:
        d = request.json
        if not d or not d.get("name"):
            return jsonify({"error": "Recipe name required"}), 400
        with engine.connect() as c:
            c.execute(text(
                "INSERT INTO recipes (name, cuisine, prep_minutes, servings) "
                "VALUES (:name, :cuisine, :prep, :servings)"
            ), {"name": d["name"], "cuisine": d.get("cuisine",""),
                "prep": d.get("prep_minutes",0), "servings": d.get("servings",2)})
            c.commit()
        logger.info(f"Recipe added: {d['name']}")
        return jsonify({"message": "Recipe added"}), 201
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/recipes/search", methods=["GET"])
def search_recipes():
    try:
        cuisine = request.args.get("cuisine","")
        with engine.connect() as c:
            rows = c.execute(text(
                "SELECT * FROM recipes WHERE cuisine LIKE :c"
            ), {"c": f"%{cuisine}%"}).fetchall()
            return jsonify([dict(r._mapping) for r in rows])
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/recipes/<int:recipe_id>/ingredients", methods=["POST"])
def add_ingredient(recipe_id):
    try:
        d = request.json
        if not d or not d.get("name"):
            return jsonify({"error": "Ingredient name required"}), 400
        with engine.connect() as c:
            c.execute(text(
                "INSERT INTO ingredients (recipe_id, name, quantity, unit) "
                "VALUES (:rid, :name, :qty, :unit)"
            ), {"rid": recipe_id, "name": d["name"],
                "qty": d.get("quantity",""), "unit": d.get("unit","")})
            c.commit()
        return jsonify({"message": "Ingredient added"}), 201
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/recipes/<int:recipe_id>/ingredients", methods=["GET"])
def get_ingredients(recipe_id):
    try:
        with engine.connect() as c:
            rows = c.execute(text(
                "SELECT * FROM ingredients WHERE recipe_id = :rid"
            ), {"rid": recipe_id}).fetchall()
            return jsonify([dict(r._mapping) for r in rows])
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/mealplan", methods=["GET"])
def get_mealplan():
    try:
        week = request.args.get("week","2024-W01")
        with engine.connect() as c:
            rows = c.execute(text(
                "SELECT mp.day_of_week, r.name FROM meal_plans mp "
                "JOIN recipes r ON mp.recipe_id = r.id "
                "WHERE mp.week_label = :week"
            ), {"week": week}).fetchall()
            return jsonify([dict(r._mapping) for r in rows])
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/mealplan", methods=["POST"])
def plan_meal():
    try:
        d = request.json
        if not d or not d.get("week") or not d.get("recipe_id"):
            return jsonify({"error": "week and recipe_id required"}), 400
        with engine.connect() as c:
            c.execute(text(
                "INSERT INTO meal_plans (week_label, day_of_week, recipe_id) "
                "VALUES (:week, :day, :rid)"
            ), {"week": d["week"], "day": d["day"], "rid": d["recipe_id"]})
            c.commit()
        return jsonify({"message": "Meal planned"}), 201
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True) 
