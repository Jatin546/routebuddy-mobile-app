# 🐳 Docker Setup for RouteBuddy

Complete Docker containerization for RouteBuddy commute companion app with MongoDB, FastAPI backend, and Expo frontend.

## 📦 What's Included

- **MongoDB 7.0** - NoSQL database
- **FastAPI Backend** - Python 3.11 with all dependencies
- **Expo Frontend** - Node 18 with React Native
- **Docker Compose** - Orchestrates all services

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed
- Docker Compose v2.0+
- 8GB RAM minimum
- Ports 3000, 8001, 27017 available

### Start Everything

```bash
# Clone the repository
git clone https://github.com/Jatin546/routebuddy-mobile-app.git
cd routebuddy-mobile-app

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 📋 Services

### MongoDB (Port 27017)
- Database: `test_database`
- No authentication (development only)
- Persistent data volume

### Backend API (Port 8001)
- FastAPI with auto-reload
- Socket.IO for real-time chat
- 17 REST API endpoints
- Access: http://localhost:8001/docs

### Frontend (Port 3000)
- Expo development server
- Hot reload enabled
- Access: http://localhost:3000
- Expo Go: Scan QR in terminal

## 🛠️ Development Commands

### Backend

```bash
# Access backend container
docker-compose exec backend bash

# Run backend tests
docker-compose exec backend python backend_test.py

# Install new Python package
docker-compose exec backend pip install package-name
docker-compose exec backend pip freeze > requirements.txt

# View backend logs
docker-compose logs -f backend
```

### Frontend

```bash
# Access frontend container
docker-compose exec frontend sh

# Install new npm package
docker-compose exec frontend yarn add package-name

# Clear Expo cache
docker-compose exec frontend yarn start -c

# View frontend logs
docker-compose logs -f frontend
```

### Database

```bash
# Access MongoDB shell
docker-compose exec mongodb mongosh

# Backup database
docker-compose exec mongodb mongodump --out=/data/backup

# View MongoDB logs
docker-compose logs -f mongodb
```

## 🔧 Configuration

### Environment Variables

**Backend** (`backend/.env`):
```env
MONGO_URL=mongodb://mongodb:27017
DB_NAME=test_database
```

**Frontend** (`frontend/.env`):
```env
EXPO_PUBLIC_BACKEND_URL=http://localhost:8001
```

### Ports

| Service  | Internal | External | Purpose |
|----------|----------|----------|---------|
| MongoDB  | 27017    | 27017    | Database |
| Backend  | 8001     | 8001     | API      |
| Frontend | 3000     | 3000     | Web      |
| Expo     | 19000-02 | 19000-02 | Dev tools|

## 📱 Mobile Testing

### Using Expo Go

1. Start services: `docker-compose up -d`
2. View frontend logs: `docker-compose logs -f frontend`
3. Find QR code in logs
4. Scan with Expo Go app

### Using Web Browser

1. Open: http://localhost:3000
2. All features work in browser
3. GPS features may need permissions

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check if ports are in use
lsof -i :3000
lsof -i :8001
lsof -i :27017

# Stop conflicting services
docker-compose down
docker system prune -a

# Restart
docker-compose up -d --build
```

### Backend Can't Connect to MongoDB

```bash
# Check MongoDB is running
docker-compose ps

# Restart MongoDB
docker-compose restart mongodb

# Check MongoDB logs
docker-compose logs mongodb
```

### Frontend Hot Reload Not Working

```bash
# Rebuild frontend
docker-compose up -d --build frontend

# Clear cache
docker-compose exec frontend yarn start -c
```

### MongoDB Data Lost

```bash
# Check volume
docker volume ls

# Inspect volume
docker volume inspect routebuddy_mongodb_data

# Backup before removing
docker-compose exec mongodb mongodump --out=/data/backup
```

## 🏗️ Building for Production

### Backend

```bash
# Build production image
docker build -t routebuddy-backend:prod ./backend

# Run production
docker run -p 8001:8001 \
  -e MONGO_URL=mongodb://your-prod-db \
  routebuddy-backend:prod
```

### Frontend

```bash
# Build for Expo
cd frontend
eas build --platform all

# Or build Docker image
docker build -t routebuddy-frontend:prod ./frontend
```

## 📊 Performance

### Resource Usage

- **MongoDB**: ~200MB RAM, ~1GB disk
- **Backend**: ~100MB RAM
- **Frontend**: ~500MB RAM (Node + bundler)

### Optimization Tips

```bash
# Limit container resources
docker-compose --compatibility up

# Use production images
docker-compose -f docker-compose.prod.yml up
```

## 🔐 Security (Production)

### MongoDB

```yaml
environment:
  MONGO_INITDB_ROOT_USERNAME: admin
  MONGO_INITDB_ROOT_PASSWORD: secure_password
```

### Backend

```yaml
environment:
  SECRET_KEY: your-secret-key
  ALLOWED_ORIGINS: https://yourdomain.com
```

### Network

```yaml
networks:
  routebuddy-network:
    internal: true  # Internal network only
```

## 📝 Docker Commands Cheat Sheet

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart single service
docker-compose restart backend

# Rebuild
docker-compose up -d --build

# View logs
docker-compose logs -f [service]

# Execute command
docker-compose exec [service] [command]

# Remove volumes
docker-compose down -v

# Scale services
docker-compose up -d --scale backend=3
```

## 🎯 Next Steps

1. **Development**: Use `docker-compose up -d`
2. **Testing**: Run tests in containers
3. **Production**: Build production images
4. **Deploy**: Push to container registry
5. **Monitor**: Add logging and monitoring

## 🤝 Contributing

See main README.md for contribution guidelines.

## 📄 License

MIT License - see LICENSE file

---

**Built with Docker for easy development and deployment** 🐳
