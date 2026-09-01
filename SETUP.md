# Setup Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 12+
- Redis
- Docker (optional)

## Backend Setup

### 1. Environment Configuration

```bash
# Navigate to backend directory
cd backend

# Copy the example environment file
cp .env.example .env

# Edit .env with your actual values
nano .env  # or use your preferred editor
```

### 2. Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb luron_db

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Run Backend

```bash
# Start development server
python manage.py runserver

# In another terminal, start Celery (if needed)
celery -A core worker -l info
```

Backend will be available at: `http://localhost:8000`

---

## Frontend Setup

### 1. Environment Configuration

```bash
# Navigate to frontend directory
cd frontend

# Copy the example environment file
cp .env.example .env.local

# Edit .env.local with your actual values
nano .env.local  # or use your preferred editor
```

### 2. Node Dependencies

```bash
# Install dependencies
npm install
# or
yarn install
```

### 3. Run Frontend

```bash
# Start development server
npm run dev
# or
yarn dev
```

Frontend will be available at: `http://localhost:3000`

---

## Docker Setup (Optional)

### Build and Run with Docker Compose

```bash
# From project root directory
docker-compose up -d

# Create database
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

Services will be available at:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

---

## Environment Variables

### Backend `.env` Required Variables

```
SECRET_KEY=<generate-with-django>
DEBUG=True                          # Only for development
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@localhost:5432/luron_db
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-xxx
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
ELEVENLABS_API_KEY=sk_xxx
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

### Frontend `.env.local` Required Variables

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Common Issues

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Database Connection Issues
- Verify PostgreSQL is running
- Check DATABASE_URL format
- Ensure database exists and user has permissions

### Node Modules Issues
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

## Development Workflow

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Test thoroughly
4. Commit: `git commit -m "Add your feature"`
5. Push: `git push origin feature/your-feature`
6. Create Pull Request

---

## Additional Resources

- See `SECURITY.md` for security guidelines
- Backend: Django documentation at https://docs.djangoproject.com/
- Frontend: Next.js documentation at https://nextjs.org/docs
