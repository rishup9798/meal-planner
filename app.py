from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)
engine = create_engine(os.getenv("DATABASE_URL"))

@app.route("/")
def home():
    return jsonify({"message": "Meal Planner API is live!"})

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
