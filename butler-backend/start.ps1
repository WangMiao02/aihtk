# 启动后端
Write-Host "=== 安装后端依赖 ===" -ForegroundColor Cyan
Set-Location "d:\aihackton\butler-backend"
pip install -r requirements.txt

Write-Host ""
Write-Host "=== 启动 FastAPI 后端 (port 8000) ===" -ForegroundColor Green
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
