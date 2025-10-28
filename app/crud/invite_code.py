import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.invite_code import InviteCode
from ..models.user import User
from ..models.teacher_student_link import TeacherStudentLink  # связь teacher ↔ student

# Буквы/цифры без двусмысленных символов (O/0, I/1)
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_random_code(length: int = 6) -> str:
    """Сгенерировать код приглашения указанной длины."""
    return ''.join(random.choices(ALPHABET, k=length))


def create_invite_code(db: Session, teacher_id: int, ttl_days: int = 7) -> InviteCode:
    """
    Создать уникальный инвайт-код для преподавателя (used=False).
    TTL контролируем при использовании (см. _is_expired).
    """
    print(f"🎯 Создаем код для преподавателя: {teacher_id}")
    
    for attempt in range(5):  # до 5 попыток на случай коллизий по unique(code)
        code = generate_random_code()
        print(f"🎲 Попытка {attempt + 1}: сгенерирован код {code}")
        
        invite = InviteCode(code=code, teacher_id=teacher_id)  # used=False по умолчанию в модели
        db.add(invite)
        try:
            db.commit()
            db.refresh(invite)
            print(f"✅ Код {code} успешно сохранен в БД с ID: {invite.id}")
            return invite
        except IntegrityError as e:
            print(f"❌ Коллизия кода {code}: {e}")
            db.rollback()
            continue
    raise RuntimeError("Не удалось сгенерировать уникальный код приглашения")


def _is_expired(invite: InviteCode, ttl_days: int = 7) -> bool:
    """Проверка, что инвайт просрочен по created_at."""
    return (datetime.utcnow() - invite.created_at) > timedelta(days=ttl_days)


def use_invite_code(db: Session, code: str, student_id: int) -> str:
    """
    Использовать код приглашения:
    - Валидируем и проверяем TTL/used
    - Создаём запись в teacher_student_links
    - Помечаем инвайт used=True
    Возвращаем статус: "success" | "expired" | "invalid" | "student_not_found" | "already_linked".
    """
    print(f"🔍 Ищем код: {code} для студента: {student_id}")
    
    invite = (
        db.query(InviteCode)
        .filter(InviteCode.code == code, InviteCode.used == False)
        .first()
    )
    
    print(f"📝 Найденный инвайт: {invite}")
    
    if not invite:
        # Дополнительная проверка - может код есть, но уже использован?
        any_invite = db.query(InviteCode).filter(InviteCode.code == code).first()
        if any_invite:
            print(f"❌ Код существует, но used={any_invite.used}")
        else:
            print("❌ Код вообще не найден в базе")
        return "invalid"

    print(f"⏰ Проверяем срок действия кода...")
    if _is_expired(invite):
        print("❌ Код просрочен")
        return "expired"

    student = db.query(User).filter(User.id == student_id).first()
    print(f"👨‍🎓 Найден студент: {student}")
    
    if not student:
        print("❌ Студент не найден")
        return "student_not_found"
    
    if student.role != "student":
        print(f"❌ Роль пользователя: {student.role}, а нужна: student")
        return "invalid"

    # Уже привязан к этому учителю?
    exists = (
        db.query(TeacherStudentLink)
        .filter(
            TeacherStudentLink.teacher_id == invite.teacher_id,
            TeacherStudentLink.student_id == student.id
        )
        .first()
    )
    
    print(f"🔗 Существующая связь: {exists}")
    
    if exists:
        print("ℹ️ Студент уже привязан к этому преподавателю")
        # ❌ НЕ помечаем код использованным при already_linked - код остается доступным
        return "already_linked"

    # Создаём связь и помечаем инвайт использованным
    try:
        print("✅ Создаем связь преподаватель-студент...")
        link = TeacherStudentLink(teacher_id=invite.teacher_id, student_id=student.id)
        db.add(link)
        invite.used = True  # ✅ Помечаем использованным только при успешном создании связи
        db.commit()
        print("✅ Связь успешно создана!")
        return "success"
    except Exception as e:
        print(f"❌ Ошибка при создании связи: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        db.rollback()
        return "invalid"