import requests

BASE_URL = "http://localhost:5000"

print("1. Testing Admin Authentication (/api/auth/login)...")
session = requests.Session()
login_res = session.post(f"{BASE_URL}/api/auth/login", json={
    "email": "admin@mediapp.local",
    "password": "Admin@123"
})
print(f"Login status: {login_res.status_code}")
login_data = login_res.json()
print("Login response keys:", list(login_data.keys()))
user = login_data.get("user", {})
print(f"User: {user.get('name')} | Role: {user.get('role')} | ID: {user.get('id')}")

headers = {}
if "token" in login_data:
    headers["Authorization"] = f"Bearer {login_data['token']}"

print("\n2. Testing GET /api/admin/stats / analytics...")
stats_res = session.get(f"{BASE_URL}/api/admin/stats", headers=headers)
print(f"Stats status: {stats_res.status_code}")
stats_data = stats_res.json()
metrics = stats_data.get("metrics", {})
print("Metrics:")
for k, v in metrics.items():
    if not isinstance(v, (list, dict)):
        print(f"  {k}: {v}")
    elif isinstance(v, dict):
        print(f"  {k}: {v}")

print(f"\nLow stock items count in response: {len(stats_data.get('low_stock', []))}")
for item in stats_data.get("low_stock", [])[:3]:
    print("  Item:", item)

print(f"\nRecent orders count in response: {len(stats_data.get('recent_orders', []))}")
for o in stats_data.get("recent_orders", []):
    if o.get("id") == "ORD-20261122-B09D":
        print("  -> Found target order:", o)

print("\n3. Testing GET /api/admin/audit-logs...")
logs_res = session.get(f"{BASE_URL}/api/admin/audit-logs", headers=headers)
print(f"Audit logs status: {logs_res.status_code}")
logs_data = logs_res.json()
print(f"Total audit log rows returned: {len(logs_data.get('logs', []))}")
found_target = False
for l in logs_data.get("logs", []):
    if l.get("order_id") == "ORD-20261122-B09D":
        print(f"  Target log: Order {l.get('order_id')} | {l.get('from_status')} -> {l.get('to_status')} | role={l.get('role')} | notes={l.get('notes')}")
        found_target = True
if not found_target:
    print("  Note: Target order was in earlier logs, showing latest 3 logs:")
    for l in logs_data.get("logs", [])[:3]:
        print(f"  Log: Order {l.get('order_id')} | {l.get('to_status')} | {l.get('notes')}")

print("\n4. Testing GET /api/admin/system-health...")
health_res = session.get(f"{BASE_URL}/api/admin/system-health", headers=headers)
print(f"System health status: {health_res.status_code}")
print(health_res.json())

print("\n5. Testing GET /api/admin/pharmacies...")
pharm_res = session.get(f"{BASE_URL}/api/admin/pharmacies", headers=headers)
print(f"Pharmacies status: {pharm_res.status_code}")
print(f"Pharmacies count: {len(pharm_res.json().get('pharmacies', []))}")

print("\n6. Testing GET /api/admin/users...")
users_res = session.get(f"{BASE_URL}/api/admin/users", headers=headers)
print(f"Users status: {users_res.status_code}")
print(f"Users count: {len(users_res.json().get('users', []))}")
