@echo off
:: Navigate to the project folder
cd /d "C:\Users\SSD\Desktop\Form137_manager"

:: Keep the window open if there is an error
echo Starting CNHS Form 137 System...
python -m streamlit run app.py
pause