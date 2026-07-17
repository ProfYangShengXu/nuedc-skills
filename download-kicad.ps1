<#
.SYNOPSIS
    KiCad 10.0.3 下载与安装脚本 (Windows)
.DESCRIPTION
    自动从 GitHub 下载 KiCad 10.0.3 并启动安装程序
    安装包约 921MB，下载可能需要 10-30 分钟
#>

$KiCadVersion = "10.0.3"
$InstallerName = "kicad-$KiCadVersion-x86_64.exe"
$DownloadUrl = "https://github.com/KiCad/kicad-source-mirror/releases/download/$KiCadVersion/$InstallerName"
$OutputPath = Join-Path $PSScriptRoot $InstallerName

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  KiCad $KiCadVersion 下载与安装助手              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Download
if (-not (Test-Path $OutputPath)) {
    Write-Host "[1/3] 正在下载 KiCad $KiCadVersion ($([math]::Round(921/1,0)) MB)..." -ForegroundColor Yellow
    Write-Host "      $DownloadUrl" -ForegroundColor Gray
    
    try {
        $web = New-Object System.Net.WebClient
        $web.DownloadProgressChanged = {
            $pct = $_.ProgressPercentage
            $bar = "#" * [math]::Floor($pct / 5) + "." * (20 - [math]::Floor($pct / 5))
            Write-Progress -Activity "下载 KiCad..." -PercentComplete $pct -Status "$pct% $bar"
        }
        $web.DownloadFileAsync($DownloadUrl, $OutputPath)
        while ($web.IsBusy) { Start-Sleep -Seconds 1 }
        Write-Progress -Activity "下载 KiCad..." -Completed
        
        if (Test-Path $OutputPath) {
            Write-Host "[✓] 下载完成: $([math]::Round((Get-Item $OutputPath).Length/1MB,1)) MB" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "[!] 下载失败: $_" -ForegroundColor Red
        Write-Host "    请手动下载:" -ForegroundColor Yellow
        Write-Host "    $DownloadUrl" -ForegroundColor Cyan
        $userInput = Read-Host "下载完成后放脚本同目录，按 Enter 继续"
    }
}
else {
    Write-Host "[✓] 安装包已存在: $([math]::Round((Get-Item $OutputPath).Length/1MB,1)) MB" -ForegroundColor Green
}

# Step 2: Install
if (Test-Path $OutputPath) {
    Write-Host ""
    Write-Host "[2/3] 启动 KiCad 安装程序..." -ForegroundColor Yellow
    Write-Host "     ⚠ 安装过程中请按向导操作:"
    Write-Host "       Next → I Agree → Install → Finish"
    Write-Host ""
    
    try {
        Start-Process -FilePath $OutputPath -Verb RunAs -Wait
        Write-Host "[✓] 安装完成" -ForegroundColor Green
    }
    catch {
        Write-Host "[!] 安装失败或用户取消" -ForegroundColor Red
        Write-Host "    请手动运行: $OutputPath" -ForegroundColor Yellow
    }
}

# Step 3: Verify
Write-Host ""
Write-Host "[3/3] 验证安装..." -ForegroundColor Yellow

$kicadPaths = @(
    "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe",
    "C:\Program Files\KiCad\10.0\bin\kicad.exe",
    "C:\Program Files\KiCad\10.0\bin\python.exe"
)

foreach ($p in $kicadPaths) {
    if (Test-Path $p) {
        Write-Host "[✓] $p" -ForegroundColor Green
    }
}

# Try to add to PATH
$kicadBin = "C:\Program Files\KiCad\10.0\bin"
if (Test-Path $kicadBin) {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$kicadBin*") {
        try {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$kicadBin", "User")
            Write-Host "[✓] KiCad 已添加到 PATH" -ForegroundColor Green
        }
        catch {
            Write-Host "[!] PATH 添加失败，请手动添加: $kicadBin" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  KiCad CLI 验证命令:" -ForegroundColor White
Write-Host "    kicad-cli version" -ForegroundColor Gray
Write-Host "    kicad-cli --help" -ForegroundColor Gray
Write-Host ""
Write-Host "  KiCad 技能文件:" -ForegroundColor White
Write-Host "    .reasonix/skills/kicad/SKILL.md" -ForegroundColor Gray
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
