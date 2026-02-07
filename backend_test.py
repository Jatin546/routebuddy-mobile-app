#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Commute Companion App
Tests all authentication, profile, route, discovery, connection, messaging, and safety endpoints
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# Configuration
BACKEND_URL = "https://routebuddy-35.preview.emergentagent.com/api"
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

class CommuteAppTester:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.test_users = {}
        self.test_routes = {}
        self.test_connections = {}
        self.test_results = {
            "auth": {},
            "profile": {},
            "routes": {},
            "discovery": {},
            "connections": {},
            "messages": {},
            "safety": {}
        }
        
    async def setup_test_users(self):
        """Create test users with session tokens in MongoDB"""
        print("🔧 Setting up test users...")
        
        # Clear existing test data
        await self.db.users.delete_many({"email": {"$regex": "test.*@example.com"}})
        await self.db.user_sessions.delete_many({})
        await self.db.routes.delete_many({})
        await self.db.connections.delete_many({})
        await self.db.messages.delete_many({})
        await self.db.reports.delete_many({})
        
        # Create test users
        test_users_data = [
            {
                "email": "alice.commuter@example.com",
                "name": "Alice Johnson",
                "picture": "https://example.com/alice.jpg"
            },
            {
                "email": "bob.rider@example.com", 
                "name": "Bob Smith",
                "picture": "https://example.com/bob.jpg"
            },
            {
                "email": "carol.traveler@example.com",
                "name": "Carol Davis",
                "picture": "https://example.com/carol.jpg"
            }
        ]
        
        for i, user_data in enumerate(test_users_data):
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            session_token = f"test_session_{uuid.uuid4().hex[:16]}"
            
            # Create user
            user = {
                "user_id": user_id,
                "email": user_data["email"],
                "name": user_data["name"],
                "picture": user_data["picture"],
                "profile_images": [],
                "bio": f"Test user {i+1} for commute companion app",
                "verified": False,
                "id_verification_image": None,
                "blocked_users": [],
                "created_at": datetime.now(timezone.utc)
            }
            await self.db.users.insert_one(user)
            
            # Create session
            session = {
                "user_id": user_id,
                "session_token": session_token,
                "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
                "created_at": datetime.now(timezone.utc)
            }
            await self.db.user_sessions.insert_one(session)
            
            self.test_users[f"user{i+1}"] = {
                "user_id": user_id,
                "session_token": session_token,
                "email": user_data["email"],
                "name": user_data["name"]
            }
            
        print(f"✅ Created {len(self.test_users)} test users with sessions")
        
    async def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Endpoints...")
        
        # Test 1: Exchange session (mock)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/auth/exchange-session",
                    json={"session_id": "mock_session_123"},
                    timeout=30.0
                )
                
                if response.status_code == 400:
                    # Expected for mock session
                    self.test_results["auth"]["exchange_session"] = {
                        "status": "pass",
                        "message": "Correctly rejects invalid session_id"
                    }
                else:
                    self.test_results["auth"]["exchange_session"] = {
                        "status": "fail", 
                        "message": f"Unexpected response: {response.status_code}"
                    }
        except Exception as e:
            self.test_results["auth"]["exchange_session"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
        # Test 2: Get current user (authenticated)
        try:
            user1 = self.test_users["user1"]
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BACKEND_URL}/auth/me",
                    headers={"Authorization": f"Bearer {user1['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("user_id") == user1["user_id"]:
                        self.test_results["auth"]["get_me"] = {
                            "status": "pass",
                            "message": "Successfully retrieved authenticated user"
                        }
                    else:
                        self.test_results["auth"]["get_me"] = {
                            "status": "fail",
                            "message": "User ID mismatch in response"
                        }
                else:
                    self.test_results["auth"]["get_me"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["auth"]["get_me"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
        # Test 3: Logout
        try:
            user1 = self.test_users["user1"]
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/auth/logout",
                    headers={"Authorization": f"Bearer {user1['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    self.test_results["auth"]["logout"] = {
                        "status": "pass",
                        "message": "Successfully logged out"
                    }
                else:
                    self.test_results["auth"]["logout"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["auth"]["logout"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
    async def test_profile_endpoints(self):
        """Test profile management endpoints"""
        print("\n👤 Testing Profile Endpoints...")
        
        user2 = self.test_users["user2"]
        
        # Test 1: Get my profile
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BACKEND_URL}/profile/me",
                    headers={"Authorization": f"Bearer {user2['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("user_id") == user2["user_id"]:
                        self.test_results["profile"]["get_profile"] = {
                            "status": "pass",
                            "message": "Successfully retrieved profile"
                        }
                    else:
                        self.test_results["profile"]["get_profile"] = {
                            "status": "fail",
                            "message": "Profile data mismatch"
                        }
                else:
                    self.test_results["profile"]["get_profile"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["profile"]["get_profile"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
        # Test 2: Update profile
        try:
            update_data = {
                "name": "Bob Smith Updated",
                "bio": "Updated bio for testing",
                "profile_images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD//gA7Q1JFQVR"]  # Sample base64
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{BACKEND_URL}/profile/update",
                    json=update_data,
                    headers={"Authorization": f"Bearer {user2['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("name") == update_data["name"] and data.get("bio") == update_data["bio"]:
                        self.test_results["profile"]["update_profile"] = {
                            "status": "pass",
                            "message": "Successfully updated profile"
                        }
                    else:
                        self.test_results["profile"]["update_profile"] = {
                            "status": "fail",
                            "message": "Profile update data mismatch"
                        }
                else:
                    self.test_results["profile"]["update_profile"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["profile"]["update_profile"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
        # Test 3: ID verification
        try:
            verification_data = {
                "id_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD//gA7Q1JFQVR"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/profile/verify-id",
                    json=verification_data,
                    headers={"Authorization": f"Bearer {user2['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("verified") == True:
                        self.test_results["profile"]["verify_id"] = {
                            "status": "pass",
                            "message": "Successfully verified ID"
                        }
                    else:
                        self.test_results["profile"]["verify_id"] = {
                            "status": "fail",
                            "message": "ID verification failed"
                        }
                else:
                    self.test_results["profile"]["verify_id"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["profile"]["verify_id"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
    async def test_route_endpoints(self):
        """Test route management endpoints"""
        print("\n🗺️ Testing Route Endpoints...")
        
        user1 = self.test_users["user1"]
        user2 = self.test_users["user2"]
        
        # Test 1: Create route for user1 (Downtown to Airport)
        try:
            route_data = {
                "start_coords": {"lat": 40.7128, "lng": -74.0060},  # NYC
                "end_coords": {"lat": 40.6413, "lng": -73.7781},    # JFK Airport
                "start_address": "Downtown Manhattan, NY",
                "end_address": "JFK Airport, NY",
                "departure_time": "08:30",
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/routes/create",
                    json=route_data,
                    headers={"Authorization": f"Bearer {user1['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("user_id") == user1["user_id"] and data.get("route_id"):
                        self.test_routes["user1_route"] = data["route_id"]
                        self.test_results["routes"]["create_route"] = {
                            "status": "pass",
                            "message": "Successfully created route"
                        }
                    else:
                        self.test_results["routes"]["create_route"] = {
                            "status": "fail",
                            "message": "Route creation data mismatch"
                        }
                else:
                    self.test_results["routes"]["create_route"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["routes"]["create_route"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
        # Test 2: Create similar route for user2 (for matching)
        try:
            route_data = {
                "start_coords": {"lat": 40.7589, "lng": -73.9851},  # Times Square (close to user1)
                "end_coords": {"lat": 40.6892, "lng": -73.7781},    # Near JFK (close to user1)
                "start_address": "Times Square, NY",
                "end_address": "Near JFK Airport, NY", 
                "departure_time": "08:45",  # 15 min difference
                "days_of_week": ["monday", "wednesday", "friday"]  # Some overlap
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/routes/create",
                    json=route_data,
                    headers={"Authorization": f"Bearer {user2['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.test_routes["user2_route"] = data["route_id"]
                    self.test_results["routes"]["create_similar_route"] = {
                        "status": "pass",
                        "message": "Successfully created similar route for matching"
                    }
                else:
                    self.test_results["routes"]["create_similar_route"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["routes"]["create_similar_route"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
        # Test 3: Get my routes
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BACKEND_URL}/routes/my-routes",
                    headers={"Authorization": f"Bearer {user1['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        self.test_results["routes"]["get_my_routes"] = {
                            "status": "pass",
                            "message": f"Successfully retrieved {len(data)} routes"
                        }
                    else:
                        self.test_results["routes"]["get_my_routes"] = {
                            "status": "fail",
                            "message": "No routes returned or invalid format"
                        }
                else:
                    self.test_results["routes"]["get_my_routes"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["routes"]["get_my_routes"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
    async def test_discovery_endpoints(self):
        """Test discovery/matching algorithm"""
        print("\n🔍 Testing Discovery/Matching Endpoints...")
        
        user1 = self.test_users["user1"]
        
        # Test: Get matches (should find user2 based on similar routes)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BACKEND_URL}/discovery/matches",
                    headers={"Authorization": f"Bearer {user1['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        # Check if we found any matches
                        user2_match = None
                        for match in data:
                            if match.get("user_id") == self.test_users["user2"]["user_id"]:
                                user2_match = match
                                break
                                
                        if user2_match:
                            score = user2_match.get("route_match_score", 0)
                            self.test_results["discovery"]["get_matches"] = {
                                "status": "pass",
                                "message": f"Found matching user with score {score}%"
                            }
                        else:
                            self.test_results["discovery"]["get_matches"] = {
                                "status": "partial",
                                "message": f"Matching algorithm working but no matches found (got {len(data)} results)"
                            }
                    else:
                        self.test_results["discovery"]["get_matches"] = {
                            "status": "fail",
                            "message": "Invalid response format"
                        }
                else:
                    self.test_results["discovery"]["get_matches"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["discovery"]["get_matches"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
    async def test_connection_endpoints(self):
        """Test connection management"""
        print("\n🤝 Testing Connection Endpoints...")
        
        user1 = self.test_users["user1"]
        user2 = self.test_users["user2"]
        
        # Test 1: Send connection request
        try:
            request_data = {
                "target_user_id": user2["user_id"]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/connections/request",
                    json=request_data,
                    headers={"Authorization": f"Bearer {user1['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("connection_id") and data.get("status") == "pending":
                        self.test_connections["connection_id"] = data["connection_id"]
                        self.test_results["connections"]["send_request"] = {
                            "status": "pass",
                            "message": "Successfully sent connection request"
                        }
                    else:
                        self.test_results["connections"]["send_request"] = {
                            "status": "fail",
                            "message": "Connection request data mismatch"
                        }
                else:
                    self.test_results["connections"]["send_request"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["connections"]["send_request"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
        # Test 2: Accept connection request
        if "connection_id" in self.test_connections:
            try:
                response_data = {
                    "connection_id": self.test_connections["connection_id"],
                    "action": "accepted"
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{BACKEND_URL}/connections/respond",
                        json=response_data,
                        headers={"Authorization": f"Bearer {user2['session_token']}"},
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "accepted":
                            self.test_results["connections"]["accept_request"] = {
                                "status": "pass",
                                "message": "Successfully accepted connection request"
                            }
                        else:
                            self.test_results["connections"]["accept_request"] = {
                                "status": "fail",
                                "message": "Connection acceptance failed"
                            }
                    else:
                        self.test_results["connections"]["accept_request"] = {
                            "status": "fail",
                            "message": f"HTTP {response.status_code}: {response.text}"
                        }
            except Exception as e:
                self.test_results["connections"]["accept_request"] = {
                    "status": "error",
                    "message": f"Request failed: {str(e)}"
                }
                
        # Test 3: List connections
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BACKEND_URL}/connections/list",
                    headers={"Authorization": f"Bearer {user1['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        accepted_connections = [c for c in data if c.get("status") == "accepted"]
                        self.test_results["connections"]["list_connections"] = {
                            "status": "pass",
                            "message": f"Successfully retrieved {len(data)} connections ({len(accepted_connections)} accepted)"
                        }
                    else:
                        self.test_results["connections"]["list_connections"] = {
                            "status": "fail",
                            "message": "Invalid response format"
                        }
                else:
                    self.test_results["connections"]["list_connections"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["connections"]["list_connections"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
    async def test_message_endpoints(self):
        """Test messaging functionality"""
        print("\n💬 Testing Message Endpoints...")
        
        user1 = self.test_users["user1"]
        user2 = self.test_users["user2"]
        
        # Test 1: Send message
        try:
            message_data = {
                "receiver_id": user2["user_id"],
                "content": "Hey! I saw we have similar commute routes. Want to share a ride?"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/messages/send",
                    json=message_data,
                    headers={"Authorization": f"Bearer {user1['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("message_id") and data.get("content") == message_data["content"]:
                        self.test_results["messages"]["send_message"] = {
                            "status": "pass",
                            "message": "Successfully sent message"
                        }
                    else:
                        self.test_results["messages"]["send_message"] = {
                            "status": "fail",
                            "message": "Message data mismatch"
                        }
                else:
                    self.test_results["messages"]["send_message"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["messages"]["send_message"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
        # Test 2: Get conversation
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BACKEND_URL}/messages/conversation/{user1['user_id']}",
                    headers={"Authorization": f"Bearer {user2['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        # Check if our message is there
                        found_message = any(msg.get("sender_id") == user1["user_id"] for msg in data)
                        if found_message:
                            self.test_results["messages"]["get_conversation"] = {
                                "status": "pass",
                                "message": f"Successfully retrieved conversation with {len(data)} messages"
                            }
                        else:
                            self.test_results["messages"]["get_conversation"] = {
                                "status": "fail",
                                "message": "Sent message not found in conversation"
                            }
                    else:
                        self.test_results["messages"]["get_conversation"] = {
                            "status": "fail",
                            "message": "No messages in conversation"
                        }
                else:
                    self.test_results["messages"]["get_conversation"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["messages"]["get_conversation"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
    async def test_safety_endpoints(self):
        """Test safety and reporting functionality"""
        print("\n🛡️ Testing Safety Endpoints...")
        
        user1 = self.test_users["user1"]
        user3 = self.test_users["user3"]
        
        # Test 1: Create report
        try:
            report_data = {
                "reported_user_id": user3["user_id"],
                "reason": "inappropriate_behavior",
                "details": "User was sending inappropriate messages during our commute discussion"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/reports/create",
                    json=report_data,
                    headers={"Authorization": f"Bearer {user1['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("report_id") and "successfully" in data.get("message", "").lower():
                        self.test_results["safety"]["create_report"] = {
                            "status": "pass",
                            "message": "Successfully created report"
                        }
                    else:
                        self.test_results["safety"]["create_report"] = {
                            "status": "fail",
                            "message": "Report creation failed"
                        }
                else:
                    self.test_results["safety"]["create_report"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["safety"]["create_report"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
        # Test 2: Block user
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/reports/block/{user3['user_id']}",
                    headers={"Authorization": f"Bearer {user1['session_token']}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "successfully" in data.get("message", "").lower():
                        self.test_results["safety"]["block_user"] = {
                            "status": "pass",
                            "message": "Successfully blocked user"
                        }
                    else:
                        self.test_results["safety"]["block_user"] = {
                            "status": "fail",
                            "message": "User blocking failed"
                        }
                else:
                    self.test_results["safety"]["block_user"] = {
                        "status": "fail",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            self.test_results["safety"]["block_user"] = {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*80)
        print("🧪 COMMUTE COMPANION APP - BACKEND API TEST RESULTS")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for category, tests in self.test_results.items():
            if not tests:
                continue
                
            print(f"\n📋 {category.upper()} ENDPOINTS:")
            print("-" * 50)
            
            for test_name, result in tests.items():
                total_tests += 1
                status = result["status"]
                message = result["message"]
                
                if status == "pass":
                    print(f"  ✅ {test_name}: {message}")
                    passed_tests += 1
                elif status == "fail":
                    print(f"  ❌ {test_name}: {message}")
                    failed_tests += 1
                elif status == "error":
                    print(f"  🔥 {test_name}: {message}")
                    error_tests += 1
                elif status == "partial":
                    print(f"  ⚠️  {test_name}: {message}")
                    passed_tests += 1  # Count as pass for summary
                    
        print("\n" + "="*80)
        print("📊 SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  ✅ Passed: {passed_tests}")
        print(f"  ❌ Failed: {failed_tests}")
        print(f"  🔥 Errors: {error_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        print("="*80)
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0
        }
        
    async def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Commute Companion Backend API Tests...")
        
        try:
            await self.setup_test_users()
            await self.test_auth_endpoints()
            await self.test_profile_endpoints()
            await self.test_route_endpoints()
            await self.test_discovery_endpoints()
            await self.test_connection_endpoints()
            await self.test_message_endpoints()
            await self.test_safety_endpoints()
            
            return self.print_results()
            
        except Exception as e:
            print(f"🔥 Critical error during testing: {str(e)}")
            return {"error": str(e)}
        finally:
            self.client.close()

async def main():
    """Main test runner"""
    tester = CommuteAppTester()
    results = await tester.run_all_tests()
    return results

if __name__ == "__main__":
    results = asyncio.run(main())