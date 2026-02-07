# RouteBuddy - Commute Companion Mobile App

A modern mobile application that helps people connect with others traveling on the same route, making daily commutes safer and more social.

![Platform](https://img.shields.io/badge/Platform-iOS%20%7C%20Android-blue)
![Stack](https://img.shields.io/badge/Stack-Expo%20%7C%20FastAPI%20%7C%20MongoDB-green)
![Status](https://img.shields.io/badge/Status-MVP%20Complete-success)

## 🎯 Overview

RouteBuddy connects commuters traveling on similar routes through intelligent GPS-based matching. Features include real-time chat, ID verification, and a smart algorithm that matches users based on route proximity, departure times, and travel days.

## ✨ Features

- 🔐 **Google OAuth Authentication** - Secure login with Emergent integration
- 🗺️ **GPS Route Matching** - Smart algorithm matches users on similar routes (free approach, no maps API needed)
- 💬 **Real-Time Chat** - Socket.IO powered instant messaging
- 👤 **Rich Profiles** - Up to 6 photos, bio, verified badges
- 🛡️ **Safety First** - ID verification, user reporting, blocking
- 🤝 **Connection System** - Send/accept connection requests
- 📱 **Native Mobile Experience** - Built with Expo for iOS & Android
- 🐳 **Docker Support** - Complete containerization with docker-compose
- 🎨 **Light/Dark Theme** - Auto-detection and manual theme switching
- ✨ **Smooth Animations** - Splash screen and onboarding with beautiful transitions

## 🏗️ Tech Stack

### Frontend
- **Expo** (React Native)
- **Expo Router** (file-based routing)
- **TypeScript**
- **Socket.IO Client** (real-time messaging)
- **Expo Location** (GPS functionality)
- **Expo Image Picker** (photo uploads)

### Backend
- **FastAPI** (Python)
- **Socket.IO** (async real-time)
- **Motor** (MongoDB async driver)
- **Pydantic** (data validation)

### Database
- **MongoDB** with 6 collections (users, routes, connections, messages, sessions, reports)

## 📁 Project Structure

```
routebuddy/
├── backend/
│   ├── server.py              # Main FastAPI server (740 lines)
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
├── frontend/
│   ├── app/                   # Expo Router screens
│   │   ├── (auth)/           # Authentication screens
│   │   ├── (tabs)/           # Main tab navigation
│   │   ├── index.tsx         # Splash screen
│   │   ├── onboarding.tsx    # Onboarding flow
│   │   ├── chat.tsx          # Real-time chat
│   │   └── ...               # Other screens
│   ├── contexts/             # React contexts
│   ├── utils/                # Utility functions
│   ├── app.json              # Expo configuration
│   └── package.json          # Dependencies
└── docs/                     # Documentation files
```

## 🚀 Quick Start

### 🐳 Option 1: Run with Docker (Recommended)

**No version conflicts, no dependency issues - everything just works!**

#### Prerequisites
- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- Docker Compose v2.0+
- 8GB RAM minimum

#### Start the Application

```bash
# Clone the repository
git clone https://github.com/Jatin546/routebuddy-mobile-app.git
cd routebuddy-mobile-app

# Start all services (MongoDB, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend   # Backend API logs
docker-compose logs -f frontend  # Frontend/Expo logs
docker-compose logs -f mongodb   # Database logs
```

#### Access the Application

Once running, access:
- **Frontend Web**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **MongoDB**: mongodb://localhost:27017

#### Stop the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (reset database)
docker-compose down -v
```

#### Mobile Testing with Expo Go

1. Start services: `docker-compose up -d`
2. Check frontend logs: `docker-compose logs -f frontend`
3. Find the QR code in the logs
4. Scan with Expo Go app on your phone

---

### 💻 Option 2: Run Without Docker (Manual Setup)

#### Prerequisites
- Node.js 18+
- Python 3.11+
- MongoDB running locally
- Expo CLI: `npm install -g expo-cli`

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

#### Frontend Setup

```bash
cd frontend
yarn install
yarn start
```

#### Environment Variables

**Backend (.env):**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
```

**Frontend (.env):**
```
EXPO_PUBLIC_BACKEND_URL=http://localhost:8001
```

---

## 🐳 Docker Commands

### Development Commands

```bash
# Rebuild containers after code changes
docker-compose up -d --build

# Restart a specific service
docker-compose restart backend
docker-compose restart frontend

# Access container shell
docker-compose exec backend bash      # Backend container
docker-compose exec frontend sh       # Frontend container
docker-compose exec mongodb mongosh   # MongoDB shell

# Install new packages
docker-compose exec backend pip install package-name
docker-compose exec frontend yarn add package-name

# View container status
docker-compose ps

# Remove everything (including volumes)
docker-compose down -v
```

### Troubleshooting

**Ports already in use:**
```bash
# Check what's using the ports
lsof -i :3000
lsof -i :8001
lsof -i :27017

# Stop and restart
docker-compose down
docker-compose up -d
```

**Containers won't start:**
```bash
# Clean up Docker
docker system prune -a
docker volume prune

# Rebuild
docker-compose up -d --build
```

**Frontend hot reload not working:**
```bash
# Clear cache and rebuild
docker-compose down
docker-compose up -d --build frontend
```

## 📱 Running on Mobile

### Using Expo Go:
1. Install Expo Go from App Store (iOS) or Play Store (Android)
2. Run `yarn start` in frontend directory
3. Scan QR code with Expo Go app

### Using Web:
1. Run `yarn start` in frontend directory
2. Press `w` to open in web browser

## 🔑 Key Features Breakdown

### Smart Matching Algorithm
- Uses **Haversine formula** to calculate distances between GPS coordinates
- Matches based on:
  - Start location proximity (≤5 km)
  - End location proximity (≤5 km)
  - Departure time (≤30 min difference)
  - Shared travel days
- Returns top 50 matches with compatibility scores

### Real-Time Chat
- Socket.IO integration for instant messaging
- Message history stored in MongoDB
- Read receipts and timestamps
- Typing indicators ready for implementation

### Security & Safety
- ID verification with image upload
- User reporting system
- Block/unblock functionality
- Session-based authentication (7-day expiry)

## 📊 API Endpoints

### Authentication
- `POST /api/auth/exchange-session` - Exchange OAuth session
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Profile Management
- `GET /api/profile/me` - Get my profile
- `PUT /api/profile/update` - Update profile
- `POST /api/profile/verify-id` - Submit ID verification

### Routes
- `POST /api/routes/create` - Create route
- `GET /api/routes/my-routes` - List routes
- `PUT /api/routes/{id}` - Update route
- `DELETE /api/routes/{id}` - Delete route

### Discovery
- `GET /api/discovery/matches` - Get matched users

### Connections
- `POST /api/connections/request` - Send request
- `POST /api/connections/respond` - Accept/reject
- `GET /api/connections/list` - List connections

### Messages
- `GET /api/messages/conversation/{user_id}` - Get messages
- `POST /api/messages/send` - Send message
- Socket.IO events for real-time delivery

### Safety
- `POST /api/reports/create` - Report user
- `POST /api/reports/block/{user_id}` - Block user

## 💾 Database Schema

### Users Collection
```javascript
{
  user_id: "user_abc123",
  email: "user@example.com",
  name: "John Doe",
  profile_images: ["base64...", "base64..."],  // Up to 6
  bio: "Love commuting!",
  verified: true,
  blocked_users: ["user_xyz"]
}
```

### Routes Collection
```javascript
{
  route_id: "route_abc123",
  user_id: "user_abc123",
  start_coords: { lat: 40.7128, lng: -74.0060 },
  end_coords: { lat: 40.7589, lng: -73.9851 },
  departure_time: "08:30",
  days_of_week: ["monday", "tuesday"],
  active: true
}
```

## 🎨 App Screens

1. **Splash Screen** - Branded entry point
2. **Onboarding** - 3-slide introduction
3. **Login** - Google OAuth
4. **Profile Setup** - Name, bio, 6 photos
5. **Route Setup** - GPS location, time, days
6. **Discover** - Browse matched route buddies
7. **Connections** - Manage connection requests
8. **Messages** - Chat conversations
9. **Chat** - Real-time 1-on-1 messaging
10. **User Profile** - View other users
11. **ID Verification** - Upload ID document
12. **Report User** - Safety reporting
13. **My Profile** - User settings

## 🧪 Testing

### Backend Tests
```bash
cd backend
python backend_test.py
```

All 17 API endpoints tested and passing (100% success rate).

### Frontend Testing
Test on mobile using Expo Go or in web browser.

## 🚀 Deployment

### Backend
- Deploy to any Python hosting (AWS, GCP, Heroku, Railway)
- Requires MongoDB connection
- Set environment variables

### Frontend
- Build with Expo EAS: `eas build`
- Deploy to App Store & Play Store
- Or deploy web version

## 📈 Performance Optimizations

- **Batch database queries** - 94-98% reduction in DB calls
- **Optimized matching algorithm** - 3 queries instead of 50+
- **Efficient connection listings** - 2 queries instead of 100+

## 🔐 Security Features

- HTTPOnly cookies for web
- Session tokens (7-day expiry)
- CORS configuration
- User blocking system
- Report functionality
- ID verification

## 🛠️ Development

### Run with Hot Reload

**Backend:**
```bash
cd backend
uvicorn server:app --reload
```

**Frontend:**
```bash
cd frontend
yarn start
```

### Clear Cache
```bash
cd frontend
yarn start -c
```

## 📝 Documentation

- `COMPLETE_CODEBASE_GUIDE.md` - Complete code reference
- `DEPLOYMENT_FIXES.md` - Deployment optimizations applied
- `auth_testing.md` - Authentication testing guide
- `README_ROUTEBUDDY.md` - Detailed app documentation

## 🤝 Contributing

This is an MVP project. Contributions welcome!

## 📄 License

MIT License - Free to use and modify

## 🎯 Roadmap

- [ ] Add visual maps integration (Google Maps)
- [ ] Push notifications
- [ ] Group commutes
- [ ] Activity planning features
- [ ] Rating system
- [ ] Premium subscription model

## 👥 Authors

Built as a comprehensive mobile app MVP for connecting commute companions.

## 🙏 Acknowledgments

- Expo team for excellent mobile framework
- FastAPI for blazing fast Python API
- MongoDB for flexible data storage
- Emergent for OAuth integration

---

**Built with ❤️ for safer, more social commuting!**

For questions or support, please open an issue.
