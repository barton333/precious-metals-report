import os, sys, json
sys.path.insert(0, os.path.abspath('src'))
import app as module
app = module.app
client = app.test_client()

def fetch(path):
    rv = client.get(path)
    print('---', path, 'STATUS', rv.status_code)
    body = rv.data.decode('utf-8', errors='replace')
    print(body[:1200])

if __name__ == '__main__':
    fetch('/')
    fetch('/api/products')
    fetch('/api/data')
    fetch('/api/analyze/黄金')
    fetch('/api/refresh')
