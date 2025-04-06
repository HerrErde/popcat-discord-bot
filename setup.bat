@echo off

echo Setting up bot...
python -m venv .venv
call .venv\Scripts\activate

cd src

echo Installing bot packages...
echo Upgrade Pip...
python.exe -m pip install --upgrade pip > nul
pip install -r requirements.txt

echo Finished bot...

exit