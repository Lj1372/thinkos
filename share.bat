@echo off
echo.
echo  ThinkOS — Share with Friends (Cloudflare Tunnel)
echo  ──────────────────────────────────────────────────
echo.

REM Start ThinkOS in background
start "ThinkOS Server" cmd /c "python app.py"
timeout /t 3 /nobreak >nul

echo  Starting public tunnel...
echo  Your shareable URL will appear below in a few seconds.
echo  Send the https://....trycloudflare.com link to anyone.
echo.
echo  Press Ctrl+C to stop sharing.
echo.
cloudflared.exe tunnel --url http://localhost:5000
