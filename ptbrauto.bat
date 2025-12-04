
call crowdin download sources
call crowdin download translations -l pt-BR

set "DESTINO=C:\Users\Ruy_R\OneDrive\Documents\GitHub\Usuimo-PTBR\PTBR"

if not exist "%DESTINO%" mkdir "%DESTINO%"

for %%F in (*PTBR*.json) do (
    move "%%F" "%DESTINO%"
)

echo Concluído!
pause