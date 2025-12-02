# API Documentation

## Overview
REST APIs have been implemented for all core features using Django Rest Framework.

## Base URL
```
http://127.0.0.1:8000/api/
```

## Authentication
All endpoints require authentication. Use HTTP Basic Auth with your credentials:
- **Username**: Your user account (e.g., `gv_admin`, `gv10_01`)
- **Password**: Your password (e.g., `Password123`)

## Available Endpoints

### 1. Users API
- **Endpoint**: `/api/users/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Description**: Manage user accounts
- **Count**: 47 users

### 2. Schools API
- **Endpoint**: `/api/schools/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Description**: Manage schools
- **Count**: 2 schools

### 3. Classes API
- **Endpoint**: `/api/classes/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Description**: Manage school classes
- **Count**: 24 classes

### 4. Students API
- **Endpoint**: `/api/students/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Description**: Manage students
- **Count**: 40 students

### 5. Subjects API
- **Endpoint**: `/api/subjects/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Description**: Manage subjects
- **Count**: 7 subjects

### 6. Assessments API
- **Endpoint**: `/api/assessments/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Description**: Manage student assessments
- **Count**: 36 assessments

### 7. Timetable API
- **Endpoint**: `/api/timetable/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Description**: Manage timetable entries
- **Count**: 30 entries

## Pagination
All list endpoints are paginated with 10 items per page by default.

## Example Usage

### Using cURL
```bash
# List all students
curl -u gv_admin:Password123 http://127.0.0.1:8000/api/students/

# Get a specific student
curl -u gv_admin:Password123 http://127.0.0.1:8000/api/students/1/

# Create a new subject
curl -u gv_admin:Password123 -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Physics"}' \
  http://127.0.0.1:8000/api/subjects/
```

### Using Python requests
```python
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('gv_admin', 'Password123')
response = requests.get('http://127.0.0.1:8000/api/students/', auth=auth)
print(response.json())
```

## Testing
Run the test script to verify all endpoints:
```bash
python test_api.py
```

All 7 endpoints are verified and working correctly.
