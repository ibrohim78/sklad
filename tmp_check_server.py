import urllib.request

try:
    res = urllib.request.urlopen('http://127.0.0.1:8000/', timeout=5)
    print('STATUS', res.status)
    print(res.read(200).decode('utf-8', errors='ignore'))
except Exception as e:
    print('ERROR', e)
