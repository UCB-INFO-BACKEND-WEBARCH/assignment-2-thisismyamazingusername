from marshmallow import ValidationError
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app import db
from app.jobs import get_queue, send_due_soon_notification, should_queue_notification
from app.models import Task
from app.schemas import TaskCreateSchema, TaskResponseSchema, TaskUpdateSchema


tasks_bp = Blueprint("tasks", __name__)


task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()
task_response_schema = TaskResponseSchema()


def _parse_completed_filter(raw_value: str):
    lowered = raw_value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueError("Query parameter 'completed' must be 'true' or 'false'.")


@tasks_bp.get("/tasks")
def list_tasks():
    query = select(Task).options(joinedload(Task.category)).order_by(Task.id.asc())

    raw_completed = request.args.get("completed")
    if raw_completed is not None:
        try:
            completed = _parse_completed_filter(raw_completed)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        query = query.where(Task.completed == completed)

    tasks = db.session.execute(query).scalars().all()
    return jsonify({"tasks": task_response_schema.dump(tasks, many=True)}), 200


@tasks_bp.get("/tasks/<int:task_id>")
def get_task(task_id: int):
    task = (
        db.session.execute(
            select(Task).options(joinedload(Task.category)).where(Task.id == task_id)
        )
        .scalars()
        .first()
    )
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(task_response_schema.dump(task)), 200


@tasks_bp.post("/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}

    try:
        data = task_create_schema.load(payload)
    except ValidationError as error:
        return jsonify({"errors": error.messages}), 400

    task = Task(
        title=data["title"],
        description=data.get("description"),
        due_date=data.get("due_date"),
        category_id=data.get("category_id"),
    )
    db.session.add(task)
    db.session.commit()

    notification_queued = False
    if should_queue_notification(task.due_date):
        queue = get_queue(current_app.config["REDIS_URL"])
        queue.enqueue(send_due_soon_notification, task.title)
        notification_queued = True

    reloaded_task = (
        db.session.execute(
            select(Task).options(joinedload(Task.category)).where(Task.id == task.id)
        )
        .scalars()
        .first()
    )

    return (
        jsonify(
            {
                "task": task_response_schema.dump(reloaded_task),
                "notification_queued": notification_queued,
            }
        ),
        201,
    )


@tasks_bp.put("/tasks/<int:task_id>")
def update_task(task_id: int):
    task = db.session.get(Task, task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    payload = request.get_json(silent=True) or {}

    try:
        data = task_update_schema.load(payload)
    except ValidationError as error:
        return jsonify({"errors": error.messages}), 400

    for field_name, value in data.items():
        setattr(task, field_name, value)

    db.session.commit()

    reloaded_task = (
        db.session.execute(
            select(Task).options(joinedload(Task.category)).where(Task.id == task.id)
        )
        .scalars()
        .first()
    )
    return jsonify(task_response_schema.dump(reloaded_task)), 200


@tasks_bp.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    task = db.session.get(Task, task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"}), 200
