@echo off
setlocal

if "%~1"=="" goto :usage
if "%~2"=="" goto :usage

set "PHOTOS_DIR=%~1"
set "BRIEF_FILE=%~2"
if "%~3"=="" (
  set "OUTPUT_ROOT=%~dp0compare_out_4"
) else (
  set "OUTPUT_ROOT=%~3"
)

set "ROOT_DIR=%~dp0"
set "CLI=%ROOT_DIR%run_pipeline_cli.py"
set "TOKENS_OCEAN=%ROOT_DIR%config\demo_brand_tokens_ocean_med.json"
set "TOKENS_PREMIUM=%ROOT_DIR%config\demo_brand_tokens_premium_gold.json"
set "FIGMA_MAP_ALT=%ROOT_DIR%config\demo_figma_template_map_alt.json"

echo.
echo [1/4] Render default...
python "%CLI%" --photos-dir "%PHOTOS_DIR%" --brief-file "%BRIEF_FILE%" --output "%OUTPUT_ROOT%\default"
if errorlevel 1 goto :fail

echo.
echo [2/4] Render ocean...
python "%CLI%" --photos-dir "%PHOTOS_DIR%" --brief-file "%BRIEF_FILE%" --design-tokens "%TOKENS_OCEAN%" --output "%OUTPUT_ROOT%\ocean"
if errorlevel 1 goto :fail

echo.
echo [3/4] Render premium...
python "%CLI%" --photos-dir "%PHOTOS_DIR%" --brief-file "%BRIEF_FILE%" --design-tokens "%TOKENS_PREMIUM%" --output "%OUTPUT_ROOT%\premium"
if errorlevel 1 goto :fail

echo.
echo [4/4] Render premium_alt...
python "%CLI%" --photos-dir "%PHOTOS_DIR%" --brief-file "%BRIEF_FILE%" --design-tokens "%TOKENS_PREMIUM%" --figma-map "%FIGMA_MAP_ALT%" --output "%OUTPUT_ROOT%\premium_alt"
if errorlevel 1 goto :fail

echo.
echo Done. Compare folders:
echo   "%OUTPUT_ROOT%\default"
echo   "%OUTPUT_ROOT%\ocean"
echo   "%OUTPUT_ROOT%\premium"
echo   "%OUTPUT_ROOT%\premium_alt"
goto :end

:usage
echo Usage:
echo   render_compare_variants_4.cmd ^<photos_dir^> ^<brief_file^> [output_root]
echo Example:
echo   render_compare_variants_4.cmd "D:\content-factory\Karusel\demo_photos" "D:\content-factory\Karusel\demo_brief.txt"
exit /b 1

:fail
echo.
echo Render failed.
exit /b 1

:end
endlocal
