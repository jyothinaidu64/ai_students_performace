#!/usr/bin/env python
"""
Test script for API endpoints
"""
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000/api/"
USERNAME = "gv_admin"
PASSWORD = "Password123"

def test_endpoint(endpoint, method="GET"):
    url = f"{BASE_URL}{endpoint}/"
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    
    try:
        if method == "GET":
            response = requests.get(url, auth=auth)
        else:
            response = requests.request(method, url, auth=auth)
        
        print(f"\n{method} {endpoint}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'results' in data:
                print(f"Count: {data.get('count', 0)}")
                print(f"Results: {len(data['results'])} items")
            elif isinstance(data, list):
                print(f"Results: {len(data)} items")
            else:
                print(f"Response: {str(data)[:100]}")
        else:
            print(f"Error: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        print(f"\n{method} {endpoint}/")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("API Testing Report")
    print("=" * 60)
    
    endpoints = [
        "users",
        "schools",
        "classes",
        "students",
        "subjects",
        "assessments",
        "timetable"
    ]
    
    results = {}
    for endpoint in endpoints:
        results[endpoint] = test_endpoint(endpoint)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for endpoint, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{endpoint:20s} {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} endpoints working")
