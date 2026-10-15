from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pymongo import ReturnDocument

from ..db import get_db
from ..models import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def to_out(doc: dict) -> TaskOut:
    return TaskOut(
        id=str(doc["_id"]),
        title=doc["title"],
        done=doc["done"],
        created_at=doc["created_at"],
    )


def parse_id(task_id: str) -> ObjectId:
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return ObjectId(task_id)


@router.get("", response_model=list[TaskOut])
async def list_tasks(db=Depends(get_db)):
    docs = await db.tasks.find().sort("created_at", -1).to_list(length=500)
    return [to_out(d) for d in docs]


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, db=Depends(get_db)):
    doc = {
        "title": payload.title,
        "done": False,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.tasks.insert_one(doc)
    doc["_id"] = result.inserted_id
    return to_out(doc)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: str, payload: TaskUpdate, db=Depends(get_db)):
    changes = payload.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")
    doc = await db.tasks.find_one_and_update(
        {"_id": parse_id(task_id)},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return to_out(doc)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, db=Depends(get_db)):
    result = await db.tasks.delete_one({"_id": parse_id(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
