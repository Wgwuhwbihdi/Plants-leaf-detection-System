from app import create_app

app = create_app()
print('DEBUG', app.debug)
client = app.test_client()
r = client.get('/')
print('HOME', r.status_code, r.headers)
r = client.get('/login')
print('LOGIN', r.status_code, r.headers)
