from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("Testing GET /api/users/list")
response = client.get("/api/users/list?industry=Education")
print(response.status_code)
print(response.json())

print("Testing GET /api/taxonomy/tree")
response = client.get("/api/taxonomy/tree?industry=Education")
print(response.status_code)
print(response.json())
