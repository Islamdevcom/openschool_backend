-- SQL Запросы для проверки безопасности после инцидента
-- Выполните эти запросы через Neon.tech SQL Editor или Railway Database

-- 1. Проверить всех пользователей (ищем подозрительные аккаунты)
SELECT
    id,
    full_name,
    email,
    role,
    school_id,
    is_verified,
    created_at
FROM users
ORDER BY id DESC
LIMIT 50;

-- 2. Проверить недавно созданных пользователей (за последние 7 дней)
SELECT
    id,
    full_name,
    email,
    role,
    created_at
FROM users
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- 3. Подсчитать пользователей по ролям
SELECT
    role,
    COUNT(*) as count
FROM users
GROUP BY role
ORDER BY count DESC;

-- 4. Проверить всех superadmin'ов (должен быть только ОДИН!)
SELECT
    id,
    full_name,
    email,
    role,
    created_at
FROM users
WHERE role = 'superadmin'
ORDER BY id;

-- 5. Проверить school_admin'ов
SELECT
    u.id,
    u.full_name,
    u.email,
    u.school_id,
    s.name as school_name,
    u.created_at
FROM users u
LEFT JOIN schools s ON u.school_id = s.id
WHERE u.role = 'school_admin'
ORDER BY u.created_at DESC;

-- 6. Проверить все школы
SELECT
    id,
    name,
    code,
    created_at
FROM schools
ORDER BY id;

-- 7. Проверить пользователей БЕЗ школы (independent)
SELECT
    id,
    full_name,
    email,
    role,
    school_id,
    created_at
FROM users
WHERE school_id IS NULL
ORDER BY created_at DESC;

-- 8. Проверить подозрительные email адреса
-- (ищем временные email, известные домены хакеров и т.д.)
SELECT
    id,
    full_name,
    email,
    role,
    created_at
FROM users
WHERE
    email LIKE '%temp%'
    OR email LIKE '%fake%'
    OR email LIKE '%test%@%'
    OR email LIKE '%guerrillamail%'
    OR email LIKE '%10minutemail%'
    OR email LIKE '%throwaway%'
ORDER BY created_at DESC;

-- 9. Общая статистика
SELECT
    'Total Users' as metric,
    COUNT(*) as value
FROM users
UNION ALL
SELECT
    'Total Schools',
    COUNT(*)
FROM schools
UNION ALL
SELECT
    'Superadmins',
    COUNT(*)
FROM users WHERE role = 'superadmin'
UNION ALL
SELECT
    'School Admins',
    COUNT(*)
FROM users WHERE role = 'school_admin'
UNION ALL
SELECT
    'Teachers',
    COUNT(*)
FROM users WHERE role = 'teacher'
UNION ALL
SELECT
    'Students',
    COUNT(*)
FROM users WHERE role = 'student';
