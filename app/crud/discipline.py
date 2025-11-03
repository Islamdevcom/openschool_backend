import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from ..models.discipline import Discipline
from ..models.teacher_discipline import TeacherDiscipline
from ..models.user import User
from ..schemas.discipline import DisciplineCreate, generate_discipline_id

logger = logging.getLogger(__name__)


# ========== Discipline CRUD ==========

def create_discipline(db: Session, school_id: int, discipline_data: DisciplineCreate) -> Discipline:
    """
    Создать новую дисциплину в школе

    Args:
        db: Сессия БД
        school_id: ID школы
        discipline_data: Данные дисциплины

    Returns:
        Discipline: Созданная дисциплина

    Raises:
        IntegrityError: Если такая дисциплина уже существует в школе
    """
    logger.info(f"Creating discipline: {discipline_data.subject} {discipline_data.grade} for school {school_id}")

    discipline = Discipline(
        school_id=school_id,
        subject=discipline_data.subject,
        grade=discipline_data.grade
    )

    db.add(discipline)
    try:
        db.commit()
        db.refresh(discipline)
        logger.info(f"Successfully created discipline ID: {discipline.id}")
        return discipline
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Discipline already exists: {discipline_data.subject} {discipline_data.grade} in school {school_id}")
        raise


def get_school_disciplines(db: Session, school_id: int) -> list[Discipline]:
    """
    Получить все дисциплины школы

    Args:
        db: Сессия БД
        school_id: ID школы

    Returns:
        list[Discipline]: Список дисциплин
    """
    logger.info(f"Fetching disciplines for school {school_id}")

    disciplines = (
        db.query(Discipline)
        .filter(Discipline.school_id == school_id)
        .order_by(Discipline.subject, Discipline.grade)
        .all()
    )

    logger.info(f"Found {len(disciplines)} disciplines for school {school_id}")
    return disciplines


def get_discipline_by_id(db: Session, discipline_id: int) -> Optional[Discipline]:
    """
    Получить дисциплину по ID

    Args:
        db: Сессия БД
        discipline_id: ID дисциплины

    Returns:
        Discipline | None: Дисциплина или None
    """
    return db.query(Discipline).filter(Discipline.id == discipline_id).first()


# ========== TeacherDiscipline CRUD ==========

def assign_discipline_to_teacher(
    db: Session,
    teacher_id: int,
    discipline_id: int,
    assigned_by_id: int
) -> TeacherDiscipline:
    """
    Назначить дисциплину учителю

    Args:
        db: Сессия БД
        teacher_id: ID учителя
        discipline_id: ID дисциплины
        assigned_by_id: ID администратора который назначает

    Returns:
        TeacherDiscipline: Созданное назначение

    Raises:
        IntegrityError: Если дисциплина уже назначена этому учителю
    """
    logger.info(f"Assigning discipline {discipline_id} to teacher {teacher_id} by admin {assigned_by_id}")

    assignment = TeacherDiscipline(
        teacher_id=teacher_id,
        discipline_id=discipline_id,
        assigned_by=assigned_by_id,
        is_active=True
    )

    db.add(assignment)
    try:
        db.commit()
        db.refresh(assignment)
        logger.info(f"Successfully assigned discipline {discipline_id} to teacher {teacher_id}")
        return assignment
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Discipline {discipline_id} already assigned to teacher {teacher_id}")
        raise


def get_teacher_disciplines(db: Session, teacher_id: int, active_only: bool = True) -> list[TeacherDiscipline]:
    """
    Получить дисциплины учителя

    Args:
        db: Сессия БД
        teacher_id: ID учителя
        active_only: Только активные назначения

    Returns:
        list[TeacherDiscipline]: Список назначений
    """
    logger.info(f"Fetching disciplines for teacher {teacher_id} (active_only={active_only})")

    query = (
        db.query(TeacherDiscipline)
        .filter(TeacherDiscipline.teacher_id == teacher_id)
    )

    if active_only:
        query = query.filter(TeacherDiscipline.is_active == True)

    assignments = (
        query
        .join(Discipline)
        .order_by(Discipline.subject, Discipline.grade)
        .all()
    )

    logger.info(f"Found {len(assignments)} disciplines for teacher {teacher_id}")
    return assignments


def remove_discipline_from_teacher(
    db: Session,
    teacher_id: int,
    discipline_id: int,
    soft_delete: bool = True
) -> bool:
    """
    Удалить дисциплину у учителя

    Args:
        db: Сессия БД
        teacher_id: ID учителя
        discipline_id: ID дисциплины
        soft_delete: Мягкое удаление (is_active=False) или жесткое

    Returns:
        bool: True если удалено, False если не найдено
    """
    logger.info(f"Removing discipline {discipline_id} from teacher {teacher_id} (soft={soft_delete})")

    assignment = (
        db.query(TeacherDiscipline)
        .filter(
            TeacherDiscipline.teacher_id == teacher_id,
            TeacherDiscipline.discipline_id == discipline_id
        )
        .first()
    )

    if not assignment:
        logger.warning(f"Assignment not found: discipline {discipline_id}, teacher {teacher_id}")
        return False

    if soft_delete:
        assignment.is_active = False
        db.commit()
        logger.info(f"Soft deleted assignment (is_active=False)")
    else:
        db.delete(assignment)
        db.commit()
        logger.info(f"Hard deleted assignment from database")

    return True


def check_assignment_exists(db: Session, teacher_id: int, discipline_id: int) -> bool:
    """
    Проверить существует ли назначение дисциплины учителю

    Args:
        db: Сессия БД
        teacher_id: ID учителя
        discipline_id: ID дисциплины

    Returns:
        bool: True если назначение существует
    """
    assignment = (
        db.query(TeacherDiscipline)
        .filter(
            TeacherDiscipline.teacher_id == teacher_id,
            TeacherDiscipline.discipline_id == discipline_id
        )
        .first()
    )

    return assignment is not None


def get_discipline_teachers(db: Session, discipline_id: int, active_only: bool = True) -> list[TeacherDiscipline]:
    """
    Получить всех учителей назначенных на дисциплину

    Args:
        db: Сессия БД
        discipline_id: ID дисциплины
        active_only: Только активные назначения

    Returns:
        list[TeacherDiscipline]: Список назначений
    """
    logger.info(f"Fetching teachers for discipline {discipline_id} (active_only={active_only})")

    query = (
        db.query(TeacherDiscipline)
        .filter(TeacherDiscipline.discipline_id == discipline_id)
    )

    if active_only:
        query = query.filter(TeacherDiscipline.is_active == True)

    assignments = query.all()

    logger.info(f"Found {len(assignments)} teachers for discipline {discipline_id}")
    return assignments
