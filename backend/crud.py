from sqlalchemy.orm import Session
from datetime import datetime
from . import database, schemas

def get_habit(db: Session, habit_id: int):
    return db.query(database.Habit).filter(database.Habit.id == habit_id).first()

def get_latest_habit(db: Session):
    return db.query(database.Habit).order_by(database.Habit.created_at.desc()).first()

def get_habits(db: Session, skip: int = 0, limit: int = 100):
    return db.query(database.Habit).offset(skip).limit(limit).all()

def create_habit(db: Session, habit: schemas.HabitCreate):
    db_habit = database.Habit(
        name=habit.name,
        description=habit.description,
        triggers=habit.triggers,
        motivation=habit.motivation,
        target_reduction=habit.target_reduction,
        created_at=datetime.utcnow()
    )
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit

def delete_habit(db: Session, habit_id: int):
    db_habit = get_habit(db, habit_id)
    if db_habit:
        db.delete(db_habit)
        db.commit()
        return True
    return False

def get_logs(db: Session, habit_id: int):
    return db.query(database.Log).filter(database.Log.habit_id == habit_id).order_by(database.Log.date.asc()).all()

def create_log(db: Session, log: schemas.LogCreate, habit_id: int):
    # If a log already exists for this habit on this date, we will update it instead of creating a duplicate
    existing_log = db.query(database.Log).filter(
        database.Log.habit_id == habit_id,
        database.Log.date == log.date
    ).first()

    if existing_log:
        existing_log.metric_value = log.metric_value
        existing_log.craving_level = log.craving_level
        existing_log.slip_up = log.slip_up
        existing_log.notes = log.notes
        db.commit()
        db.refresh(existing_log)
        return existing_log

    db_log = database.Log(
        habit_id=habit_id,
        date=log.date,
        metric_value=log.metric_value,
        craving_level=log.craving_level,
        slip_up=log.slip_up,
        notes=log.notes,
        created_at=datetime.utcnow()
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_chat_history(db: Session, habit_id: int, limit: int = 50):
    return db.query(database.ChatMessage).filter(
        database.ChatMessage.habit_id == habit_id
    ).order_by(database.ChatMessage.timestamp.asc()).limit(limit).all()

def create_chat_message(db: Session, msg: schemas.ChatMessageCreate, habit_id: int):
    db_msg = database.ChatMessage(
        habit_id=habit_id,
        sender=msg.sender,
        message=msg.message,
        timestamp=datetime.utcnow()
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg
