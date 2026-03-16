# Simple smoke tests for /farmer/summary endpoint
from app import app, server_sessions, customers
import json

client = app.test_client()

print('Testing unauthenticated access...')
r = client.get('/farmer/summary/1')
print('Status:', r.status_code, 'Body:', r.get_data(as_text=True))
assert r.status_code == 401
j = r.get_json()
assert j.get('error') == 'login_required'

print('Creating synthetic customer session...')
sid = 'test-sid-123'
server_sessions[sid] = customers[0]

print('Testing authenticated access for existing farmer...')
r = client.get('/farmer/summary/1?sid=' + sid)
print('Status:', r.status_code)
assert r.status_code == 200
j = r.get_json()
print('JSON keys:', list(j.keys()))
assert j['id'] == 1
assert 'trust_score' in j

print('Testing farmer not found...')
r = client.get('/farmer/summary/999?sid=' + sid)
print('Status:', r.status_code, 'Body:', r.get_data(as_text=True))
assert r.status_code == 404
j = r.get_json()
assert j.get('error') == 'not_found'

print('All tests passed')
