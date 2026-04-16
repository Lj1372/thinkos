@echo off
echo.
echo  ThinkOS — Share via ngrok
echo  ─────────────────────────
echo.
echo  NOTE: First time? You need a free ngrok account.
echo  1. Go to https://ngrok.com and sign up (free)
echo  2. Copy your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
echo  3. Run: ngrok config add-authtoken YOUR_TOKEN_HERE
echo  Then run this script again.
echo.

REM Start ThinkOS in background
start "ThinkOS" cmd /c "python app.py"
timeout /t 2 /nobreak >nul

echo  Starting ngrok tunnel on port 5000...
echo  Your public URL will appear below. Share it with friends.
echo  Press Ctrl+C to stop sharing.
echo.
ngrok http 5000
