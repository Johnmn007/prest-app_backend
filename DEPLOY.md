# Despliegue en Railway + Vercel

## Backend — Railway

### Variables de entorno requeridas en Railway:

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Railway la provee automáticamente al agregar PostgreSQL |
| `JWT_SECRET` | Generar con: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_EXPIRE` | Minutos de expiración del token (ej: 1440 = 24h) |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `FRONTEND_URL` | URL de tu app en Vercel (ej: `https://dilver.vercel.app`) |
| `ALLOWED_ORIGINS` | `["https://dilver.vercel.app"]` |

### Pasos:
1. Crear proyecto en Railway
2. Agregar servicio PostgreSQL
3. Conectar repositorio GitHub
4. Configurar variables de entorno
5. Railway detecta `Procfile` y despliega automáticamente
6. Ejecutar migraciones: `alembic upgrade head`
7. Crear admin: `python crear_admin.py`

---

## Frontend — Vercel

### Variables de entorno requeridas en Vercel:

| Variable | Descripción |
|---|---|
| `VITE_API_URL` | URL del backend en Railway (ej: `https://dilver-backend.railway.app`) |

### Pasos:
1. Conectar repositorio en Vercel
2. Configurar `Root Directory` → `dilver_frontend`
3. Agregar variable `VITE_API_URL`
4. Vercel detecta Vite automáticamente y despliega

---

## Generar JWT_SECRET seguro

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
