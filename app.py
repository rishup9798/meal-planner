from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)
engine = create_engine(os.getenv("DATABASE_URL"))

# --- Home ---
@app.route("/")
def home():
    return jsonify({"message": "Meal Planner API is live!"})

# --- UI ---
@app.route("/ui")
def ui():
    return render_template("index.html")

# --- Recipes ---
@app.route("/recipes", methods=["GET"])
def get_recipes():
    with engine.connect() as c:
        rows = c.execute(text("SELECT * FROM recipes")).fetchall()
        return jsonify([dict(r._mapping) for r in rows])

@app.route("/recipes", methods=["POST"])
def add_recipe():
    d = request.json
    with engine.connect() as c:
        c.execute(text(
            "INSERT INTO recipes (name, cuisine, prep_minutes, servings) "
            "VALUES (:name, :cuisine, :prep, :servings)"
        ), {"name": d["name"], "cuisine": d.get("cuisine", ""),
            "prep": d.get("prep_minutes", 0), "servings": d.get("servings", 2)})
        c.commit()
    return jsonify({"message": "Recipe added"}), 201

@app.route("/recipes/search", methods=["GET"])
def search_recipes():
    cuisine = request.args.get("cuisine", "")
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT * FROM recipes WHERE cuisine LIKE :c"
        ), {"c": f"%{cuisine}%"}).fetchall()
        return jsonify([dict(r._mapping) for r in rows])

# --- Ingredients ---
@app.route("/recipes/<int:recipe_id>/ingredients", methods=["POST"])
def add_ingredient(recipe_id):
    d = request.json
    with engine.connect() as c:
        c.execute(text(
            "INSERT INTO ingredients (recipe_id, name, quantity, unit) "
            "VALUES (:rid, :name, :qty, :unit)"
        ), {"rid": recipe_id, "name": d["name"],
            "qty": d.get("quantity", ""), "unit": d.get("unit", "")})
        c.commit()
    return jsonify({"message": "Ingredient added"}), 201

@app.route("/recipes/<int:recipe_id>/ingredients", methods=["GET"])
def get_ingredients(recipe_id):
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT * FROM ingredients WHERE recipe_id = :rid"
        ), {"rid": recipe_id}).fetchall()
        return jsonify([dict(r._mapping) for r in rows])

# --- Meal Plans ---
@app.route("/mealplan", methods=["GET"])
def get_mealplan():
    week = request.args.get("week", "2024-W01")
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT mp.day_of_week, r.name FROM meal_plans mp "
            "JOIN recipes r ON mp.recipe_id = r.id "
            "WHERE mp.week_label = :week"
        ), {"week": week}).fetchall()
        return jsonify([dict(r._mapping) for r in rows])

@app.route("/mealplan", methods=["POST"])
def plan_meal():
    d = request.json
    with engine.connect() as c:
        c.execute(text(
            "INSERT INTO meal_plans (week_label, day_of_week, recipe_id) "
            "VALUES (:week, :day, :rid)"
        ), {"week": d["week"], "day": d["day"], "rid": d["recipe_id"]})
        c.commit()
    return jsonify({"message": "Meal planned"}), 201

if __name__ == "__main__":
    app.run(debug=True)
