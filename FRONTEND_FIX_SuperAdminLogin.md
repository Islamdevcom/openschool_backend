# Исправление SuperAdminLoginPage.jsx

## Проблема
Кнопка входа суперадмина не работает - используется заглушка вместо реального API.

## Решение

### Файл: `src/pages/auth/SuperAdminLoginPage.jsx`

**1. Добавьте импорты в начало файла:**

```javascript
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginSuperAdmin } from '../../auth/authService';
import './SuperAdminLoginPage.css';
```

**2. Внутри компонента добавьте navigate:**

```javascript
export default function SuperAdminLoginPage() {
  const navigate = useNavigate();

  // Existing state declarations...
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(''); // Добавьте это!

  // ... rest of states
```

**3. Замените функцию `handleSubmit` на:**

```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  setError('');
  setLoading(true);

  try {
    console.log('🔐 Attempting superadmin login...');
    const data = await loginSuperAdmin(email, password);

    console.log('✅ Login successful:', data);

    // Сохраняем данные пользователя
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('role', data.role);
    localStorage.setItem('email', data.email);
    localStorage.setItem('full_name', data.full_name);

    // Перенаправляем на панель суперадмина
    navigate('/superadmin');

  } catch (err) {
    console.error('❌ Login error:', err);
    setError(err.message || 'Ошибка входа. Проверьте email и пароль.');
  } finally {
    setLoading(false);
  }
};
```

**4. В форме добавьте отображение ошибки (перед кнопкой):**

```jsx
{error && (
  <div style={{
    padding: '12px',
    marginBottom: '16px',
    backgroundColor: '#fee',
    border: '1px solid #fcc',
    borderRadius: '8px',
    color: '#c33',
    fontSize: '14px'
  }}>
    {error}
  </div>
)}

<button
  type="submit"
  disabled={loading}
  className="login-button"
>
  {loading ? 'Вход...' : 'Войти'}
</button>
```

## Тестирование

После исправления попробуйте войти с данными:
- **Email:** `superadmin@openschool.com`
- **Password:** `@34567`

Должно перенаправить на `/superadmin` и в консоли появится "✅ Login successful"

## Commit message

```
fix: implement real API authentication for superadmin login

- Replace mock setTimeout with loginSuperAdmin API call
- Add error handling and display
- Add navigation to /superadmin dashboard after successful login
- Add console logging for debugging
```
