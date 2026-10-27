import os, subprocess, sys, time, urllib.request, json

# 1. Kill old panel PID 26100
import subprocess

try:
    subprocess.run(['powershell', '-Command', 'Stop-Process -Id 26100 -Force -ErrorAction SilentlyContinue'], check=False)
    print("Stopped old panel process 26100")
except Exception as e:
    print("Kill error:", e)

time.sleep(1.5)

# 2. Start new panel process
pythonw = r'C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\pythonw.exe'
if not os.path.exists(pythonw):
    pythonw = sys.executable

panel_script = r'C:\Codes\OpenOrbit\OpenOrbit Panel.pyw'
cmd = [pythonw, panel_script, '--pencere-yok']

print(f"Launching {cmd}...")
subprocess.Popen(cmd, cwd=r'C:\Codes\OpenOrbit', creationflags=0x00000008 | 0x00000200)

# 3. Wait for port 8077 to respond
for i in range(15):
    time.sleep(1)
    try:
        html = urllib.request.urlopen('http://127.0.0.1:8077/', timeout=2).read().decode('utf-8')
        if 'panel-token' in html:
            token = html.split('content="')[1].split('"')[0]
            print(f"Panel is online! Token: {token}")
            
            # Check /api/ayarlar
            req = urllib.request.Request('http://127.0.0.1:8077/api/ayarlar', headers={'X-Panel-Belirteci': token})
            data = json.loads(urllib.request.urlopen(req, timeout=2).read().decode('utf-8'))
            savas_settings = [s for s in data.get('sema', []) if s.get('grup') == 'savas']
            print("\nLive settings under 'savas':")
            for s in savas_settings[-5:]:
                print(f"  {s['anahtar']} -> {s['ad']} (unit: {s.get('birim')})")
            
            # Check translation of ad
            en = json.load(open('server/panel/arayuz/en.json', encoding='utf-8'))
            for s in savas_settings[-5:]:
                translated = en.get(s['ad'], s['ad'])
                unit_tr = en.get(s.get('birim'), s.get('birim'))
                print(f"  English: {translated} (unit: {unit_tr})")
            break
    except Exception as e:
        print(f"Waiting for panel... ({e})")
