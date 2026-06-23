# Mobile Access Guide

To run the QuizFall server and access it from a mobile device on the same network, follow these steps:

### 1. Configure Django (Already Done)
Ensure `quizfall/settings.py` includes your local IP or a wildcard in `ALLOWED_HOSTS`:
```python
ALLOWED_HOSTS = ['*']
```

### 2. Find Your Computer's IP Address
Run this command in your terminal:
```powershell
ipconfig
```
Look for the **IPv4 Address** (e.g., `192.168.1.6`).

### 3. Run the Server
Start the server using `0.0.0.0` to allow external connections:
```powershell
python manage.py runserver 0.0.0.0:8000
```

### 4. Access on Mobile
1. Connect your phone to the **same Wi-Fi** as your computer.
2. Open the mobile browser.
3. Enter the URL: `http://<YOUR_IP>:8000` (e.g., `http://192.168.1.6:8000`).

### Troubleshooting
- **Firewall**: If it fails to load, ensure port `8000` is allowed through Windows Firewall.
  - Run as Admin: `netsh advfirewall firewall add rule name="Django 8000" dir=in action=allow protocol=TCP localport=8000`
- **Network Isolation**: Ensure your Wi-Fi router doesn't have "AP Isolation" or "Guest Mode" enabled.
