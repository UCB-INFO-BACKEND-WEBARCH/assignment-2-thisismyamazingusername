from marshmallow import ValidationError
from flask import Blueprint, jsonify, request
from sqlalchemy import func, select

from app import db
from app.models import Category, Task
from app.schemas import CategoryCreateSchema


categories_bp = Blueprint("categories", __name__)
category_create_schema = CategoryCreateSchema()


@categories_bp.get("/categories")
def list_categories():
    rows = db.session.execute(
        select(Category, func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id.asc())
    ).all()

    categories = [
        {
            "id": category.id,
            "name": category.name,
            "color": category.color,
            "task_count": task_count,
        }
        for category, task_count in rows
    ]
    return jsonify({"categories": categories}), 200


@categories_bp.get("/categories/<int:category_id>")
def get_category(category_id: int):
    category = db.session.get(Category, category_id)
    if category is None:
        return jsonify({"error": "Category not found"}), 404

    tasks = (
        db.session.execute(
            select(Task).where(Task.category_id == category.id).order_by(Task.id.asc())
        )
        .scalars()
        .all()
    )

    response = {
        "id": category.id,
        "name": category.name,
        "color": category.color,
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "completed": task.completed,
            }
            for task in tasks
        ],
    }
    return jsonify(response), 200


@categories_bp.post("/categories")
def create_category():
    payload = request.get_json(silent=True) or {}

    try:
        data = category_create_schema.load(payload)
    except ValidationError as error:
        return jsonify({"errors": error.messages}), 400

    existing = db.session.execute(
        select(Category).where(func.lower(Category.name) == data["name"].lower())
    ).scalars().first()
    if existing is not None:
        return jsonify({"errors": {"name": ["Category with this name already exists."]}}), 400

    category = Category(name=data["name"], color=data.get("color"))
    db.session.add(category)
    db.session.commit()

    return (
        jsonify({"id": category.id, "name": category.name, "color": category.color}),
        201,
    )


@categories_bp.delete("/categories/<int:category_id>")
def delete_category(category_id: int):
    category = db.session.get(Category, category_id)
    if category is None:
        return jsonify({"error": "Category not found"}), 404

    task_count = db.session.execute(
        select(func.count(Task.id)).where(Task.category_id == category.id)
    ).scalar_one()
    if task_count > 0:
        return (
            jsonify(
                {
                    "error": "Cannot delete category with existing tasks. Move or delete tasks first."
                }
            ),
            400,
        )

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted"}), 200
