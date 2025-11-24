# app/services/openai_service.py
"""
OpenAI сервис для генерации контента AI-инструментов.
Используется всеми 26 инструментами учителя.
"""
import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI

logger = logging.getLogger(__name__)

# Инициализация клиента OpenAI
client = None


def get_openai_client():
    """Получить клиент OpenAI (lazy initialization)"""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")
        client = OpenAI(api_key=api_key)
    return client


async def generate_with_openai(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    response_format: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Базовая функция для генерации контента через OpenAI.

    Args:
        system_prompt: Системный промпт с инструкциями
        user_prompt: Пользовательский запрос
        model: Модель OpenAI (gpt-4o-mini по умолчанию)
        temperature: Температура генерации (0.0-1.0)
        max_tokens: Максимальное количество токенов в ответе
        response_format: Формат ответа (для JSON mode)

    Returns:
        Dict с результатом и метаданными
    """
    start_time = time.time()

    try:
        openai_client = get_openai_client()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Добавляем JSON mode если нужен структурированный ответ
        if response_format:
            kwargs["response_format"] = response_format

        response = openai_client.chat.completions.create(**kwargs)

        generation_time = int((time.time() - start_time) * 1000)

        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0

        # Пробуем распарсить JSON если возможно
        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            parsed_content = {"text": content}

        return {
            "success": True,
            "content": parsed_content,
            "raw_content": content,
            "tokens_used": tokens_used,
            "generation_time_ms": generation_time,
            "model": model
        }

    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        generation_time = int((time.time() - start_time) * 1000)

        return {
            "success": False,
            "error": str(e),
            "content": None,
            "tokens_used": 0,
            "generation_time_ms": generation_time,
            "model": model
        }


# ============================================================================
# ПРОМПТЫ ДЛЯ ИНСТРУМЕНТОВ
# ============================================================================

TOOL_PROMPTS = {
    # 1. Планирование урока
    "lesson_plan": {
        "system": """Ты опытный методист и учитель. Создай детальный план урока на русском языке.
План должен быть структурированным и практичным. Ответ дай в формате JSON:
{
    "title": "Название урока",
    "subject": "Предмет",
    "grade": "Класс",
    "duration": "Длительность в минутах",
    "objectives": ["Цель 1", "Цель 2"],
    "materials": ["Материал 1", "Материал 2"],
    "lesson_structure": [
        {"phase": "Вводная часть", "duration": "5 мин", "activities": "Описание"},
        {"phase": "Основная часть", "duration": "30 мин", "activities": "Описание"},
        {"phase": "Закрепление", "duration": "10 мин", "activities": "Описание"}
    ],
    "assessment": "Способ оценивания",
    "homework": "Домашнее задание",
    "differentiation": "Дифференциация для разных уровней"
}""",
        "user_template": "Создай план урока по предмету '{subject}' на тему '{topic}' для {grade} класса. Длительность: {duration} минут. {additional_requirements}"
    },

    # 2. Цели обучения
    "learning_objectives": {
        "system": """Ты эксперт по образовательным стандартам. Создай SMART цели обучения на русском языке.
Ответ в формате JSON:
{
    "topic": "Тема",
    "cognitive_objectives": [
        {"level": "Знание", "objective": "Ученик сможет..."},
        {"level": "Понимание", "objective": "Ученик сможет..."},
        {"level": "Применение", "objective": "Ученик сможет..."}
    ],
    "skill_objectives": ["Навык 1", "Навык 2"],
    "assessment_criteria": ["Критерий 1", "Критерий 2"]
}""",
        "user_template": "Создай цели обучения для темы '{topic}' по предмету '{subject}' для {grade} класса."
    },

    # 3. Расписание
    "schedule": {
        "system": """Ты помощник по составлению расписания. Создай оптимальное расписание уроков.
Ответ в формате JSON:
{
    "schedule": [
        {"day": "Понедельник", "lessons": [
            {"time": "8:00-8:45", "subject": "Предмет", "room": "Кабинет"}
        ]}
    ],
    "recommendations": ["Рекомендация 1"]
}""",
        "user_template": "Составь расписание на {period} для {grade} класса. Предметы: {subjects}. {constraints}"
    },

    # 4. Учебные материалы
    "materials": {
        "system": """Ты создатель учебных материалов. Создай качественный учебный материал на русском языке.
Ответ в формате JSON:
{
    "title": "Название",
    "type": "Тип материала",
    "content": "Основной контент",
    "key_points": ["Ключевой момент 1"],
    "examples": ["Пример 1"],
    "practice_tasks": ["Задание 1"],
    "summary": "Краткое резюме"
}""",
        "user_template": "Создай учебный материал типа '{material_type}' по теме '{topic}' для {grade} класса по предмету '{subject}'."
    },

    # 5. Рабочие листы
    "worksheet": {
        "system": """Ты создатель рабочих листов для учеников. Создай интерактивный рабочий лист.
Ответ в формате JSON:
{
    "title": "Название рабочего листа",
    "instructions": "Инструкции для ученика",
    "tasks": [
        {"number": 1, "type": "fill_blank", "question": "Вопрос", "answer": "Ответ"},
        {"number": 2, "type": "multiple_choice", "question": "Вопрос", "options": ["A", "B", "C"], "correct": "A"}
    ],
    "total_points": 10,
    "time_estimate": "15 минут"
}""",
        "user_template": "Создай рабочий лист по теме '{topic}' для {grade} класса. Предмет: {subject}. Количество заданий: {num_tasks}. Сложность: {difficulty}."
    },

    # 6. Тесты/Викторины
    "quiz": {
        "system": """Ты создатель тестов и викторин. Создай качественный тест на русском языке.
Ответ в формате JSON:
{
    "title": "Название теста",
    "description": "Описание",
    "time_limit": "20 минут",
    "questions": [
        {
            "id": 1,
            "type": "multiple_choice",
            "question": "Текст вопроса",
            "options": ["A) Вариант 1", "B) Вариант 2", "C) Вариант 3", "D) Вариант 4"],
            "correct_answer": "A",
            "explanation": "Объяснение правильного ответа",
            "points": 1
        }
    ],
    "total_points": 10,
    "passing_score": 7
}""",
        "user_template": "Создай тест по теме '{topic}' для {grade} класса. Предмет: {subject}. Количество вопросов: {num_questions}. Сложность: {difficulty}."
    },

    # 7. Презентации
    "presentation": {
        "system": """Ты создатель образовательных презентаций. Создай структуру презентации.
Ответ в формате JSON:
{
    "title": "Название презентации",
    "slides": [
        {"number": 1, "title": "Заголовок", "content": "Контент", "speaker_notes": "Заметки для докладчика"},
        {"number": 2, "title": "Заголовок", "bullet_points": ["Пункт 1", "Пункт 2"]}
    ],
    "total_slides": 10,
    "estimated_duration": "30 минут"
}""",
        "user_template": "Создай презентацию по теме '{topic}' для {grade} класса. Предмет: {subject}. Количество слайдов: {num_slides}."
    },

    # 8. Оценивание
    "assessment": {
        "system": """Ты эксперт по оцениванию. Оцени работу ученика и дай обратную связь.
Ответ в формате JSON:
{
    "score": 85,
    "max_score": 100,
    "grade": "4",
    "strengths": ["Сильная сторона 1"],
    "areas_for_improvement": ["Область для улучшения 1"],
    "detailed_feedback": "Подробный отзыв",
    "recommendations": ["Рекомендация 1"]
}""",
        "user_template": "Оцени работу ученика по теме '{topic}'. Предмет: {subject}. Критерии: {criteria}. Работа ученика: {student_work}"
    },

    # 9. Критерии оценки (Рубрики)
    "rubric": {
        "system": """Ты эксперт по созданию рубрик оценивания. Создай детальную рубрику.
Ответ в формате JSON:
{
    "title": "Название рубрики",
    "criteria": [
        {
            "name": "Критерий 1",
            "weight": 25,
            "levels": [
                {"score": 4, "description": "Отлично - описание"},
                {"score": 3, "description": "Хорошо - описание"},
                {"score": 2, "description": "Удовлетворительно - описание"},
                {"score": 1, "description": "Неудовлетворительно - описание"}
            ]
        }
    ],
    "total_points": 100
}""",
        "user_template": "Создай рубрику оценивания для задания '{assignment_type}' по теме '{topic}'. Предмет: {subject}. Класс: {grade}."
    },

    # 10. Ключ ответов
    "answer_key": {
        "system": """Ты создатель ключей ответов. Создай подробный ключ с объяснениями.
Ответ в формате JSON:
{
    "title": "Ключ ответов",
    "answers": [
        {"question_number": 1, "correct_answer": "A", "explanation": "Объяснение"},
        {"question_number": 2, "correct_answer": "15", "solution_steps": ["Шаг 1", "Шаг 2"]}
    ],
    "grading_notes": "Заметки для проверки"
}""",
        "user_template": "Создай ключ ответов для вопросов: {questions}. Тема: '{topic}'. Предмет: {subject}."
    },

    # 11. Стратегии преподавания
    "teaching_strategy": {
        "system": """Ты эксперт по методике преподавания. Предложи эффективные стратегии.
Ответ в формате JSON:
{
    "topic": "Тема",
    "strategies": [
        {
            "name": "Название стратегии",
            "description": "Описание",
            "steps": ["Шаг 1", "Шаг 2"],
            "benefits": ["Преимущество 1"],
            "suitable_for": ["Тип учеников"]
        }
    ],
    "recommended_resources": ["Ресурс 1"],
    "common_mistakes": ["Ошибка 1"]
}""",
        "user_template": "Предложи стратегии преподавания темы '{topic}' для {grade} класса. Предмет: {subject}. Особенности класса: {class_profile}."
    },

    # 12. Вопросы для обсуждения
    "discussion_prompts": {
        "system": """Ты создатель вопросов для дискуссий. Создай вовлекающие вопросы.
Ответ в формате JSON:
{
    "topic": "Тема",
    "warm_up_questions": ["Вопрос для разминки"],
    "main_discussion_questions": [
        {"question": "Вопрос", "thinking_level": "Анализ", "follow_up": "Дополнительный вопрос"}
    ],
    "debate_topics": ["Тема для дебатов"],
    "reflection_questions": ["Рефлексивный вопрос"]
}""",
        "user_template": "Создай вопросы для обсуждения темы '{topic}' для {grade} класса. Предмет: {subject}. Тип дискуссии: {discussion_type}."
    },

    # 13. Интерактивные активности
    "interactive_activities": {
        "system": """Ты создатель интерактивных активностей. Предложи вовлекающие занятия.
Ответ в формате JSON:
{
    "topic": "Тема",
    "activities": [
        {
            "name": "Название активности",
            "type": "Тип (игра/проект/эксперимент)",
            "duration": "15 минут",
            "group_size": "4-5 человек",
            "materials_needed": ["Материал 1"],
            "instructions": ["Шаг 1", "Шаг 2"],
            "learning_outcomes": ["Результат 1"]
        }
    ]
}""",
        "user_template": "Создай интерактивные активности по теме '{topic}' для {grade} класса. Предмет: {subject}. Количество учеников: {num_students}. Время: {duration} минут."
    },

    # 14. Аналитика успеваемости ученика
    "student_analytics": {
        "system": """Ты аналитик образовательных данных. Проанализируй успеваемость ученика.
Ответ в формате JSON:
{
    "student_name": "Имя",
    "overall_performance": "Хорошо",
    "grade_trend": "Рост",
    "strengths": ["Сильная сторона"],
    "weaknesses": ["Слабая сторона"],
    "recommendations": ["Рекомендация"],
    "predicted_grade": "4",
    "intervention_needed": false
}""",
        "user_template": "Проанализируй успеваемость ученика. Данные: {student_data}. Период: {period}."
    },

    # 15. Аналитика класса
    "class_analytics": {
        "system": """Ты аналитик образовательных данных. Проанализируй успеваемость класса.
Ответ в формате JSON:
{
    "class_name": "Класс",
    "average_grade": 4.2,
    "grade_distribution": {"5": 5, "4": 10, "3": 8, "2": 2},
    "top_performers": ["Ученик 1"],
    "struggling_students": ["Ученик 2"],
    "class_trends": "Описание тренда",
    "recommendations": ["Рекомендация"]
}""",
        "user_template": "Проанализируй успеваемость класса. Данные: {class_data}. Предмет: {subject}. Период: {period}."
    },

    # 16. Отслеживание прогресса
    "progress_tracking": {
        "system": """Ты специалист по отслеживанию прогресса. Создай отчет о прогрессе.
Ответ в формате JSON:
{
    "student_name": "Имя",
    "skills_progress": [
        {"skill": "Навык", "initial_level": 2, "current_level": 4, "target_level": 5}
    ],
    "milestones_achieved": ["Достижение 1"],
    "next_goals": ["Цель 1"],
    "time_to_target": "2 недели"
}""",
        "user_template": "Создай отчет о прогрессе ученика. Данные: {progress_data}. Цели: {goals}."
    },

    # 17. Библиотека ресурсов
    "resource_library": {
        "system": """Ты библиотекарь образовательных ресурсов. Подбери релевантные ресурсы.
Ответ в формате JSON:
{
    "topic": "Тема",
    "resources": [
        {
            "title": "Название",
            "type": "video/article/book",
            "description": "Описание",
            "difficulty": "Средний",
            "recommended_for": "Для закрепления"
        }
    ],
    "search_suggestions": ["Поисковый запрос"]
}""",
        "user_template": "Подбери образовательные ресурсы по теме '{topic}' для {grade} класса. Предмет: {subject}. Тип ресурсов: {resource_type}."
    },

    # 18. Управление документами
    "document_summary": {
        "system": """Ты помощник по работе с документами. Создай краткое содержание документа.
Ответ в формате JSON:
{
    "document_title": "Название",
    "summary": "Краткое содержание",
    "key_points": ["Ключевой момент"],
    "terms_glossary": [{"term": "Термин", "definition": "Определение"}],
    "questions_for_discussion": ["Вопрос"]
}""",
        "user_template": "Проанализируй документ и создай краткое содержание. Документ: {document_content}"
    },

    # 19. Проверка ДЗ
    "homework_check": {
        "system": """Ты учитель-проверяющий домашние задания. Проверь работу и дай оценку.
Ответ в формате JSON:
{
    "score": 85,
    "max_score": 100,
    "grade": "4",
    "correct_answers": 8,
    "total_questions": 10,
    "mistakes": [
        {"question": "Вопрос 3", "student_answer": "Ответ ученика", "correct_answer": "Правильный ответ", "explanation": "Объяснение"}
    ],
    "feedback": "Общий отзыв",
    "improvement_tips": ["Совет 1"]
}""",
        "user_template": "Проверь домашнее задание ученика. Тема: '{topic}'. Предмет: {subject}. Задание: {assignment}. Ответы ученика: {student_answers}"
    },

    # 20. Создание ДЗ
    "homework_generator": {
        "system": """Ты создатель домашних заданий. Создай интересное и полезное ДЗ.
Ответ в формате JSON:
{
    "title": "Название ДЗ",
    "instructions": "Инструкции",
    "tasks": [
        {"number": 1, "description": "Описание задания", "points": 10, "estimated_time": "10 минут"}
    ],
    "total_points": 30,
    "due_date_suggestion": "через 3 дня",
    "resources_needed": ["Ресурс 1"],
    "parent_note": "Записка для родителей"
}""",
        "user_template": "Создай домашнее задание по теме '{topic}' для {grade} класса. Предмет: {subject}. Сложность: {difficulty}. Время выполнения: {estimated_time}."
    },

    # 21. Тесты с вариантами
    "mcq_test": {
        "system": """Ты создатель тестов с множественным выбором. Создай качественный тест.
Ответ в формате JSON:
{
    "title": "Название теста",
    "questions": [
        {
            "id": 1,
            "question": "Текст вопроса",
            "options": {
                "A": "Вариант A",
                "B": "Вариант B",
                "C": "Вариант C",
                "D": "Вариант D"
            },
            "correct": "A",
            "difficulty": "medium",
            "explanation": "Объяснение"
        }
    ],
    "answer_key": {"1": "A", "2": "B"},
    "time_limit_minutes": 20
}""",
        "user_template": "Создай тест с вариантами ответов по теме '{topic}' для {grade} класса. Предмет: {subject}. Количество вопросов: {num_questions}."
    },

    # 22. Банк вопросов
    "question_bank": {
        "system": """Ты создатель банка вопросов. Создай разнообразные вопросы.
Ответ в формате JSON:
{
    "topic": "Тема",
    "questions": [
        {
            "id": 1,
            "type": "multiple_choice/short_answer/essay",
            "difficulty": "easy/medium/hard",
            "question": "Текст вопроса",
            "answer": "Ответ",
            "tags": ["тег1", "тег2"]
        }
    ],
    "total_questions": 10
}""",
        "user_template": "Создай банк вопросов по теме '{topic}' для {grade} класса. Предмет: {subject}. Количество: {num_questions}. Типы вопросов: {question_types}."
    },

    # 23. Генерация отчетов
    "report_generator": {
        "system": """Ты создатель отчетов для руководства. Создай профессиональный отчет.
Ответ в формате JSON:
{
    "report_title": "Название отчета",
    "period": "Период",
    "executive_summary": "Краткое резюме",
    "key_metrics": [
        {"metric": "Метрика", "value": "Значение", "trend": "up/down/stable"}
    ],
    "achievements": ["Достижение 1"],
    "challenges": ["Проблема 1"],
    "recommendations": ["Рекомендация 1"],
    "action_items": ["Действие 1"]
}""",
        "user_template": "Создай отчет для руководства. Тип отчета: {report_type}. Период: {period}. Данные: {data}."
    },

    # 24. Отчет об оценках
    "grade_report": {
        "system": """Ты создатель отчетов об успеваемости. Создай детальный отчет.
Ответ в формате JSON:
{
    "report_title": "Отчет об успеваемости",
    "class": "Класс",
    "period": "Период",
    "summary": {
        "average_grade": 4.2,
        "highest_grade": 5,
        "lowest_grade": 2,
        "pass_rate": 92
    },
    "by_student": [
        {"name": "Ученик", "average": 4.5, "grades": [5, 4, 5], "trend": "stable"}
    ],
    "recommendations": ["Рекомендация"]
}""",
        "user_template": "Создай отчет об оценках для класса. Данные: {grades_data}. Период: {period}."
    },

    # 25. Зацепка урока
    "lesson_hook": {
        "system": """Ты создатель увлекательных начал уроков. Создай "зацепку" для урока.
Ответ в формате JSON:
{
    "hooks": [
        {
            "type": "question/story/video/activity/demonstration",
            "title": "Название",
            "content": "Описание зацепки",
            "duration": "3 минуты",
            "engagement_level": "high",
            "materials_needed": ["Материал"],
            "follow_up_questions": ["Вопрос для перехода к теме"]
        }
    ],
    "recommended_hook": 1,
    "connection_to_topic": "Как зацепка связана с темой"
}""",
        "user_template": "Создай увлекательное начало урока (зацепку) для темы '{topic}'. Класс: {grade}. Предмет: {subject}. Стиль: {engagement_style}."
    },

    # 26. Дифференциация
    "differentiation": {
        "system": """Ты эксперт по дифференцированному обучению. Создай задания трех уровней.
Ответ в формате JSON:
{
    "topic": "Тема",
    "level_a": {
        "name": "Продвинутый уровень",
        "description": "Для учеников с высоким уровнем",
        "tasks": ["Сложное задание 1"],
        "expected_outcomes": ["Результат"],
        "extension_activities": ["Дополнительная активность"]
    },
    "level_b": {
        "name": "Базовый уровень",
        "description": "Для большинства учеников",
        "tasks": ["Стандартное задание 1"],
        "expected_outcomes": ["Результат"],
        "support_materials": ["Материал поддержки"]
    },
    "level_c": {
        "name": "Поддерживающий уровень",
        "description": "Для учеников, нуждающихся в поддержке",
        "tasks": ["Упрощенное задание 1"],
        "expected_outcomes": ["Результат"],
        "scaffolding": ["Подсказка/шаблон"]
    },
    "differentiation_strategies": ["Стратегия 1"]
}""",
        "user_template": "Создай дифференцированные задания (уровни A, B, C) по теме '{topic}' для {grade} класса. Предмет: {subject}. Базовое задание: {base_content}."
    }
}


# ============================================================================
# ФУНКЦИИ ГЕНЕРАЦИИ ДЛЯ КАЖДОГО ИНСТРУМЕНТА
# ============================================================================

async def generate_lesson_plan(
    subject: str,
    topic: str,
    grade: str,
    duration: int = 45,
    additional_requirements: str = ""
) -> Dict[str, Any]:
    """Генерация плана урока"""
    prompt_config = TOOL_PROMPTS["lesson_plan"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        duration=duration,
        additional_requirements=additional_requirements
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_learning_objectives(
    subject: str,
    topic: str,
    grade: str
) -> Dict[str, Any]:
    """Генерация целей обучения"""
    prompt_config = TOOL_PROMPTS["learning_objectives"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_schedule(
    grade: str,
    period: str,
    subjects: List[str],
    constraints: str = ""
) -> Dict[str, Any]:
    """Генерация расписания"""
    prompt_config = TOOL_PROMPTS["schedule"]
    user_prompt = prompt_config["user_template"].format(
        grade=grade,
        period=period,
        subjects=", ".join(subjects),
        constraints=constraints
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_materials(
    subject: str,
    topic: str,
    grade: str,
    material_type: str
) -> Dict[str, Any]:
    """Генерация учебных материалов"""
    prompt_config = TOOL_PROMPTS["materials"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        material_type=material_type
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_worksheet(
    subject: str,
    topic: str,
    grade: str,
    num_tasks: int = 10,
    difficulty: str = "medium"
) -> Dict[str, Any]:
    """Генерация рабочего листа"""
    prompt_config = TOOL_PROMPTS["worksheet"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        num_tasks=num_tasks,
        difficulty=difficulty
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_quiz(
    subject: str,
    topic: str,
    grade: str,
    num_questions: int = 10,
    difficulty: str = "medium"
) -> Dict[str, Any]:
    """Генерация теста/викторины"""
    prompt_config = TOOL_PROMPTS["quiz"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        num_questions=num_questions,
        difficulty=difficulty
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_presentation(
    subject: str,
    topic: str,
    grade: str,
    num_slides: int = 10
) -> Dict[str, Any]:
    """Генерация презентации"""
    prompt_config = TOOL_PROMPTS["presentation"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        num_slides=num_slides
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def evaluate_student_work(
    subject: str,
    topic: str,
    criteria: str,
    student_work: str
) -> Dict[str, Any]:
    """Оценивание работы ученика"""
    prompt_config = TOOL_PROMPTS["assessment"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        criteria=criteria,
        student_work=student_work
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_rubric(
    subject: str,
    topic: str,
    grade: str,
    assignment_type: str
) -> Dict[str, Any]:
    """Генерация рубрики оценивания"""
    prompt_config = TOOL_PROMPTS["rubric"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        assignment_type=assignment_type
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_answer_key(
    subject: str,
    topic: str,
    questions: str
) -> Dict[str, Any]:
    """Генерация ключа ответов"""
    prompt_config = TOOL_PROMPTS["answer_key"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        questions=questions
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_teaching_strategy(
    subject: str,
    topic: str,
    grade: str,
    class_profile: str = ""
) -> Dict[str, Any]:
    """Генерация стратегий преподавания"""
    prompt_config = TOOL_PROMPTS["teaching_strategy"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        class_profile=class_profile
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_discussion_prompts(
    subject: str,
    topic: str,
    grade: str,
    discussion_type: str = "general"
) -> Dict[str, Any]:
    """Генерация вопросов для обсуждения"""
    prompt_config = TOOL_PROMPTS["discussion_prompts"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        discussion_type=discussion_type
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_interactive_activities(
    subject: str,
    topic: str,
    grade: str,
    num_students: int = 25,
    duration: int = 15
) -> Dict[str, Any]:
    """Генерация интерактивных активностей"""
    prompt_config = TOOL_PROMPTS["interactive_activities"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        num_students=num_students,
        duration=duration
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def analyze_student_performance(
    student_data: str,
    period: str
) -> Dict[str, Any]:
    """Анализ успеваемости ученика"""
    prompt_config = TOOL_PROMPTS["student_analytics"]
    user_prompt = prompt_config["user_template"].format(
        student_data=student_data,
        period=period
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def analyze_class_performance(
    subject: str,
    class_data: str,
    period: str
) -> Dict[str, Any]:
    """Анализ успеваемости класса"""
    prompt_config = TOOL_PROMPTS["class_analytics"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        class_data=class_data,
        period=period
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def track_progress(
    progress_data: str,
    goals: str
) -> Dict[str, Any]:
    """Отслеживание прогресса"""
    prompt_config = TOOL_PROMPTS["progress_tracking"]
    user_prompt = prompt_config["user_template"].format(
        progress_data=progress_data,
        goals=goals
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def search_resources(
    subject: str,
    topic: str,
    grade: str,
    resource_type: str = "all"
) -> Dict[str, Any]:
    """Поиск образовательных ресурсов"""
    prompt_config = TOOL_PROMPTS["resource_library"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        resource_type=resource_type
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def summarize_document(
    document_content: str
) -> Dict[str, Any]:
    """Создание краткого содержания документа"""
    prompt_config = TOOL_PROMPTS["document_summary"]
    user_prompt = prompt_config["user_template"].format(
        document_content=document_content[:5000]  # Ограничиваем длину
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def check_homework(
    subject: str,
    topic: str,
    assignment: str,
    student_answers: str
) -> Dict[str, Any]:
    """Проверка домашнего задания"""
    prompt_config = TOOL_PROMPTS["homework_check"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        assignment=assignment,
        student_answers=student_answers
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_homework(
    subject: str,
    topic: str,
    grade: str,
    difficulty: str = "medium",
    estimated_time: str = "30 минут"
) -> Dict[str, Any]:
    """Генерация домашнего задания"""
    prompt_config = TOOL_PROMPTS["homework_generator"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        difficulty=difficulty,
        estimated_time=estimated_time
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_mcq_test(
    subject: str,
    topic: str,
    grade: str,
    num_questions: int = 10
) -> Dict[str, Any]:
    """Генерация теста с множественным выбором"""
    prompt_config = TOOL_PROMPTS["mcq_test"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        num_questions=num_questions
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_question_bank(
    subject: str,
    topic: str,
    grade: str,
    num_questions: int = 20,
    question_types: str = "mixed"
) -> Dict[str, Any]:
    """Генерация банка вопросов"""
    prompt_config = TOOL_PROMPTS["question_bank"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        num_questions=num_questions,
        question_types=question_types
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_report(
    report_type: str,
    period: str,
    data: str
) -> Dict[str, Any]:
    """Генерация отчета для руководства"""
    prompt_config = TOOL_PROMPTS["report_generator"]
    user_prompt = prompt_config["user_template"].format(
        report_type=report_type,
        period=period,
        data=data
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_grade_report(
    grades_data: str,
    period: str
) -> Dict[str, Any]:
    """Генерация отчета об оценках"""
    prompt_config = TOOL_PROMPTS["grade_report"]
    user_prompt = prompt_config["user_template"].format(
        grades_data=grades_data,
        period=period
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_lesson_hook(
    subject: str,
    topic: str,
    grade: str,
    engagement_style: str = "interactive"
) -> Dict[str, Any]:
    """Генерация зацепки урока"""
    prompt_config = TOOL_PROMPTS["lesson_hook"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        engagement_style=engagement_style
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )


async def generate_differentiation(
    subject: str,
    topic: str,
    grade: str,
    base_content: str
) -> Dict[str, Any]:
    """Генерация дифференцированных заданий (A/B/C)"""
    prompt_config = TOOL_PROMPTS["differentiation"]
    user_prompt = prompt_config["user_template"].format(
        subject=subject,
        topic=topic,
        grade=grade,
        base_content=base_content
    )
    return await generate_with_openai(
        prompt_config["system"],
        user_prompt,
        response_format={"type": "json_object"}
    )
