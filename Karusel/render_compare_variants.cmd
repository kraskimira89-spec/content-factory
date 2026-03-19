@echo off
setlocal

if "%~1"=="" goto :usage
if "%~2"=="" goto :usage

set "PHOTOS_DIR=%~1"
set "BRIEF_FILE=%~2"
if "%~3"=="" (
  set "OUTPUT_ROOT=%~dp0compare_out"
) else (
  set "OUTPUT_ROOT=%~3"
)

set "ROOT_DIR=%~dp0"
set "CLI=%ROOT_DIR%run_pipeline_cli.py"

echo.
echo [1/3] Render default...
python "%CLI%" --photos-dir "%PHOTOS_DIR%" --brief-file "%BRIEF_FILE%" --output "%OUTPUT_ROOT%\default"
if errorlevel 1 goto :fail

echo.
echo [2/3] Render ocean...
python "%CLI%" --photos-dir "%PHOTOS_DIR%" --brief-file "%BRIEF_FILE%" --design-tokens "%ROOT_DIR%config\demo_brand_tokens_ocean_med.json" --output "%OUTPUT_ROOT%\ocean"
if errorlevel 1 goto :fail

echo.
echo [3/3] Render premium...
python "%CLI%" --photos-dir "%PHOTOS_DIR%" --brief-file "%BRIEF_FILE%" --design-tokens "%ROOT_DIR%config\demo_brand_tokens_premium_gold.json" --output "%OUTPUT_ROOT%\premium"
if errorlevel 1 goto :fail

echo.
echo Done. Compare folders:
echo   "%OUTPUT_ROOT%\default"
echo   "%OUTPUT_ROOT%\ocean"
echo   "%OUTPUT_ROOT%\premium"
goto :end

:usage
echo Usage:
echo   render_compare_variants.cmd ^<photos_dir^> ^<brief_file^> [output_root]
echo Example:
echo   render_compare_variants.cmd "D:\content-factory\Karusel\demo_photos" "D:\content-factory\Karusel\demo_brief.txt"
exit /b 1

:fail
echo.
echo Render failed.
exit /b 1

:end
endlocal
