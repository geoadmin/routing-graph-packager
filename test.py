import requests
from base64 import b64encode

auth = ('nils@gis-ops.com', 'manchmal')
auth_joined = ":".join(auth).encode()
auth_encoded = b64encode(bytes(auth_joined))
auth_header = {'Authorization': f'Basic {auth_encoded.decode()}'}
response = requests.post(
    'http://localhost:5000/api/v1/users',
    headers=auth_header,
    json={
        'email': 'bogus',
        'password': 'bogus'
    }
)

print(response.request.headers)
requests_auth = response.request.headers['Authorization'][6:]

print(response.status_code)

response = requests.post(
    'http://localhost:5000/api/v1/users/', auth=auth, json={
        'email': 'bogus',
        'password': 'bogus'
    }
)

print(response.request.headers)
print(response.status_code)
