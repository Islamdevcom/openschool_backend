import logging
import os
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import UploadFile

from ..models.discipline_file import DisciplineFile
from ..models.discipline import Discipline

logger = logging.getLogger(__name__)

# Директория для хранения файлов
UPLOAD_DIR = "uploads/disciplines"


# ========== DisciplineFile CRUD ==========

async def save_discipline_file(
    db: Session,
    discipline_id: int,
    file: UploadFile,
    uploaded_by_id: int
) -> DisciplineFile:
    """
    Сохранить файл для дисциплины

    Args:
        db: Сессия БД
        discipline_id: ID дисциплины
        file: Загружаемый файл
        uploaded_by_id: ID пользователя который загружает

    Returns:
        DisciplineFile: Созданная запись о файле
    """
    logger.info(f"Saving file {file.filename} for discipline {discipline_id}")

    # Создаем директорию если не существует
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Генерируем уникальное имя файла
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{discipline_id}_{int(os.time.time())}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Сохраняем файл
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    file_size = len(content)
    file_type = file_extension.lstrip('.').lower()

    # Создаем запись в БД
    discipline_file = DisciplineFile(
        discipline_id=discipline_id,
        filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        uploaded_by=uploaded_by_id
    )

    db.add(discipline_file)
    db.commit()
    db.refresh(discipline_file)

    logger.info(f"Successfully saved file ID: {discipline_file.id}")
    return discipline_file


def get_discipline_files(db: Session, discipline_id: int) -> list[DisciplineFile]:
    """
    Получить все файлы дисциплины

    Args:
        db: Сессия БД
        discipline_id: ID дисциплины

    Returns:
        list[DisciplineFile]: Список файлов
    """
    logger.info(f"Fetching files for discipline {discipline_id}")

    files = (
        db.query(DisciplineFile)
        .filter(DisciplineFile.discipline_id == discipline_id)
        .order_by(DisciplineFile.created_at.desc())
        .all()
    )

    logger.info(f"Found {len(files)} files for discipline {discipline_id}")
    return files


def get_file_by_id(db: Session, file_id: int) -> Optional[DisciplineFile]:
    """
    Получить файл по ID

    Args:
        db: Сессия БД
        file_id: ID файла

    Returns:
        DisciplineFile | None: Файл или None
    """
    return db.query(DisciplineFile).filter(DisciplineFile.id == file_id).first()


def delete_discipline_file(db: Session, file_id: int) -> bool:
    """
    Удалить файл дисциплины

    Args:
        db: Сессия БД
        file_id: ID файла

    Returns:
        bool: True если удален, False если не найден
    """
    logger.info(f"Deleting file {file_id}")

    file_record = get_file_by_id(db, file_id)
    if not file_record:
        logger.warning(f"File {file_id} not found")
        return False

    # Удаляем физический файл
    try:
        if os.path.exists(file_record.file_path):
            os.remove(file_record.file_path)
            logger.info(f"Deleted physical file: {file_record.file_path}")
    except Exception as e:
        logger.error(f"Error deleting physical file: {str(e)}")

    # Удаляем запись из БД
    db.delete(file_record)
    db.commit()

    logger.info(f"Successfully deleted file {file_id}")
    return True


def get_school_all_discipline_files(db: Session, school_id: int) -> list[DisciplineFile]:
    """
    Получить все файлы всех дисциплин школы

    Args:
        db: Сессия БД
        school_id: ID школы

    Returns:
        list[DisciplineFile]: Список файлов
    """
    logger.info(f"Fetching all discipline files for school {school_id}")

    files = (
        db.query(DisciplineFile)
        .join(Discipline)
        .filter(Discipline.school_id == school_id)
        .order_by(DisciplineFile.created_at.desc())
        .all()
    )

    logger.info(f"Found {len(files)} files for school {school_id}")
    return files
