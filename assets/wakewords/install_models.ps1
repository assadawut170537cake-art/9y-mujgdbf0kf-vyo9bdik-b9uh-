param (
    [string]$TargetPythonEnv = ""
)

Write-Host "============================================="
Write-Host " Jarvis Local Wake Word Models Installer"
Write-Host "============================================="

$sourcePath = $PSScriptRoot
$models = @("hey_jarvis_v0.1.onnx", "hey_jarvis_v0.1.tflite")

# หากมีการระบุ Python Environment
if ($TargetPythonEnv -ne "") {
    $targetDir = Join-Path $TargetPythonEnv "Lib\site-packages\openwakeword\resources\models"
} else {
    # ค้นหา Python ในระบบ
    $pythonExe = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonExe) {
        $sitePackages = & $pythonExe.Source -c "import site; print(site.getsitepackages()[0])"
        $targetDir = Join-Path $sitePackages "openwakeword\resources\models"
    } else {
        Write-Host "Error: ไม่พบ Python ในระบบ กรุณาระบุ -TargetPythonEnv" -ForegroundColor Red
        exit 1
    }
}

if (-not (Test-Path $targetDir)) {
    Write-Host "สร้างไดเรกทอรีเป้าหมาย: $targetDir"
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
}

foreach ($model in $models) {
    $src = Join-Path $sourcePath $model
    $dst = Join-Path $targetDir $model
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $dst -Force
        Write-Host "ติดตั้ง $model สำเร็จ -> $dst" -ForegroundColor Green
    } else {
        Write-Host "ไม่พบไฟล์โมเดล $src" -ForegroundColor Red
    }
}

Write-Host "ติดตั้งโมเดลเสียงเรียก (Wake Word) เสร็จสมบูรณ์แล้ว!"
