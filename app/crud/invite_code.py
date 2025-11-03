import random
import string
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.invite_code import InviteCode
from ..models.user import User
from ..models.teacher_student_relation import TeacherStudentRelation

# Настройка логгера
logger = logging.getLogger(__name__)

# Буквы/цифры без двусмысленных символов (O/0, I/1)
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_random_code(length: int = 6) -> str:
    """Сгенерировать код приглашения указанной длины."""
    return ''.join(random.choices(ALPHABET, k=length))


def create_invite_code(db: Session, teacher_id: int, ttl_days: int = 7) -> InviteCode:
    """
    Создать уникальный инвайт-код для преподавателя (used=False).
    TTL контролируем при использовании (см. _is_expired).

    Args:
        db: Сессия БД
        teacher_id: ID преподавателя
        ttl_days: Срок действия кода в днях (по умолчанию 7)

    Returns:
        InviteCode: Созданный объект кода приглашения

    Raises:
        RuntimeError: Если не удалось сгенерировать уникальный код за 5 попыток
        SQLAlchemyError: При ошибках базы данных
    """
    logger.info(f"Создание кода приглашения для преподавателя ID: {teacher_id}")

    for attempt in range(5):  # до 5 попыток на случай коллизий по unique(code)
        code = generate_random_code()
        logger.debug(f"Попытка {attempt + 1}/5: сгенерирован код {code}")

        invite = InviteCode(code=code, teacher_id=teacher_id)  # used=False по умолчанию в модели
        db.add(invite)
        try:
            db.commit()
            db.refresh(invite)
            logger.info(f"Код приглашения {code} успешно создан с ID: {invite.id}")
            return invite
        except IntegrityError as e:
            logger.warning(f"Коллизия кода {code} (попытка {attempt + 1}/5): {str(e)}")
            db.rollback()
            continue

    error_msg = f"Не удалось сгенерировать уникальный код приглашения для преподавателя {teacher_id} за 5 попыток"
    logger.error(error_msg)
    raise RuntimeError(error_msg)


def _is_expired(invite: InviteCode, ttl_days: int = 7) -> bool:
    """Проверка, что инвайт просрочен по created_at."""
    return (datetime.utcnow() - invite.created_at) > timedelta(days=ttl_days)


def use_invite_code(db: Session, code: str, student_id: int) -> str:
    """
    Использовать код приглашения:
    - Валидируем и проверяем TTL/used
    - Создаём запись в teacher_student_relations
    - Помечаем инвайт used=True

    Args:
        db: Сессия БД
        code: Код приглашения
        student_id: ID студента

    Returns:
        str: Статус операции - "success" | "expired" | "invalid" | "student_not_found" | "already_linked"
    """
    logger.info(f"Использование кода приглашения '{code}' студентом ID: {student_id}")

    invite = (
        db.query(InviteCode)
        .filter(InviteCode.code == code, InviteCode.used == False)
        .first()
    )

    if not invite:
        # Дополнительная проверка - может код есть, но уже использован?
        any_invite = db.query(InviteCode).filter(InviteCode.code == code).first()
        if any_invite:
            logger.warning(f"Код '{code}' существует, но уже использован (used={any_invite.used})")
        else:
            logger.warning(f"Код '{code}' не найден в базе данных")
        return "invalid"

    logger.debug(f"Код '{code}' найден, проверяем срок действия...")
    if _is_expired(invite):
        logger.warning(f"Код '{code}' просрочен")
        return "expired"

    student = db.query(User).filter(User.id == student_id).first()

    if not student:
        logger.error(f"Студент с ID {student_id} не найден")
        return "student_not_found"

    if student.role != "student":
        logger.warning(f"Пользователь {student_id} имеет роль '{student.role}', требуется 'student'")
        return "invalid"

    # Уже привязан к этому учителю?
    exists = (
        db.query(TeacherStudentRelation)
        .filter(
            TeacherStudentRelation.teacher_id == invite.teacher_id,
            TeacherStudentRelation.student_id == student.id
        )
        .first()
    )

    if exists:
        logger.info(f"Студент {student_id} уже привязан к преподавателю {invite.teacher_id}")
        # НЕ помечаем код использованным при already_linked - код остается доступным
        return "already_linked"

    # Создаём связь и помечаем инвайт использованным
    try:
        logger.info(f"Создание связи преподаватель {invite.teacher_id} - студент {student.id}")
        link = TeacherStudentRelation(teacher_id=invite.teacher_id, student_id=student.id)
        db.add(link)
        invite.used = True  # Помечаем использованным только при успешном создании связи
        db.commit()
        logger.info(f"Связь успешно создана, код '{code}' помечен использованным")
        return "success"
    except Exception as e:
        logger.error(f"Ошибка при создании связи преподаватель-студент: {type(e).__name__}: {str(e)}", exc_info=True)
        db.rollback()
        return "invalid"