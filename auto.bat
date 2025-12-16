
call crowdin download sources
call crowdin download translations -l pt-BR

set "DESTINO=C:\Users\Ruy_R\OneDrive\Documents\GitHub\Usuimo-PTBR\PTBR"
set "DESTINO2=E:\sister-windows-beta\www\data\PTBR"

if not exist "%DESTINO%" mkdir "%DESTINO%"

for %%F in (*PTBR*.json) do (
    copy /Y "%%F" "%DESTINO2%"
)

for %%F in (*PTBR*.json) do (
    move "%%F" "%DESTINO%"
)

del /f /q *EN*.json

git add .

git diff --cached --quiet
if %errorlevel%==0 (
    echo Nenhuma alteracao detectada. Commit nao criado.
) else (
    set /p COMMIT_MSG=Digite a mensagem do commit: 
    if "!COMMIT_MSG!"=="" (
        echo Mensagem vazia. Commit cancelado.
    ) else (
        git commit -m "!COMMIT_MSG!"
    )
)
echo Concluído!
pause