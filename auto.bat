
call crowdin download sources
call crowdin download translations -l pt-BR

set "DESTINO=C:\Users\Ruy_R\OneDrive\Documents\GitHub\Usuimo-PTBR\PTBR"

if not exist "%DESTINO%" mkdir "%DESTINO%"

for %%F in (*PTBR*.json) do (
    move "%%F" "%DESTINO%"
)

del /f /q *EN*.json

git add .

git diff --cached --quiet
if %errorlevel%==0 (
    echo Nenhuma alteracao detectada. Commit nao criado.
) else (
    git commit -m "Atualização automatica PT-BR via Crowdin"
)
git fetch origin
git push
echo Concluído!
pause