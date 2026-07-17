<#
.SYNOPSIS
    Keil MDK v5.43a 下载与安装自动化脚本 (Windows)
.DESCRIPTION
    自动从 ARM Keil 官方网站下载 MDK-ARM v5.43a 评估版，
    并提供交互式安装引导。
    
    用法:
        .\download-keil5.ps1                   # 交互模式：手动填写信息下载
        .\download-keil5.ps1 -Auto             # 自动模式：使用默认信息提交下载
        .\download-keil5.ps1 -InstallOnly      # 仅安装（跳过下载，需本地已有安装包）
    
    注意:
        评估版安装包约 872MB，下载可能需要较长时间。
        无许可证将以 Lite/Evaluation 模式运行（代码限制 32KB）。
#>

$KeilVersion = "5.43a"
$InstallerExe = "MDK$($KeilVersion.Replace('.',''))" + "a.exe"

param(
    [switch]$Auto,
    [switch]$InstallOnly
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallerFile = Join-Path $ScriptDir $InstallerExe

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       Keil MDK-ARM v5.43a 下载与安装助手              ║" -ForegroundColor Cyan
Write-Host "║       ARM Keil MDK - Microcontroller Development Kit   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── 步骤 1: 下载 ───────────────────────────────────────
if (-not $InstallOnly) {
    if (Test-Path $InstallerFile) {
        Write-Host "[✓] 安装包已存在: $InstallerFile" -ForegroundColor Green
        Write-Host "    大小: $('{0:N1} MB' -f ((Get-Item $InstallerFile).Length / 1MB))"
    }
    else {
        Write-Host "[1/3] 正在准备下载 Keil MDK-ARM v5.43a..." -ForegroundColor Yellow
        Write-Host "      安装包大小: ~872 MB"
        Write-Host ""
        
        if (-not $Auto) {
            Write-Host "═══════════════════════════════════════════════" -ForegroundColor Magenta
            Write-Host "  请打开浏览器，访问以下地址手动下载:" -ForegroundColor White
            Write-Host ""
            Write-Host "  →  https://www.keil.com/demo/eval/arm.htm" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  填写联系信息 (可随意填写) 后点击 Submit" -ForegroundColor White
            Write-Host "  下载的文件请保存为: MDK543a.exe" -ForegroundColor White
            Write-Host "  放在本脚本同目录下即可" -ForegroundColor White
            Write-Host "═══════════════════════════════════════════════" -ForegroundColor Magenta
            Write-Host ""
            
            # 尝试在浏览器中打开下载页面
            try {
                Start-Process "https://www.keil.com/demo/eval/arm.htm"
                Write-Host "[→] 已自动打开浏览器跳转到下载页面" -ForegroundColor Green
            }
            catch {
                Write-Host "[!] 无法自动打开浏览器，请手动访问以上链接" -ForegroundColor Red
            }
            
            Write-Host ""
            $userInput = Read-Host "下载完成后按 Enter 继续..."
        }
        else {
            # 自动下载模式 - 尝试通过 curl 提交表单
            Write-Host "[→] 自动模式: 正在提交下载请求..." -ForegroundColor Green
            
            # 第一次请求获取 cookies
            $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
            $null = Invoke-WebRequest -Uri "https://www.keil.com/demo/eval/arm.htm" -SessionVariable session
            
            # 提交表单
            $formData = @{
                firstname   = "User"
                lastname    = "Dev"
                email       = "dev" + (Get-Random -Min 1000 -Max 9999) + "@outlook.com"
                company     = "MyCompany"
                jobtitle    = "Engineer"
                countrycode = "CN"
                phone       = "13800138000"
                products    = "downloaded an RVMDK eval"
                device      = "STM32F103"
                Submit      = "Submit"
            }
            
            try {
                $response = Invoke-WebRequest -Uri "https://www.keil.com/demo/eval/arm.htm" `
                    -Method POST `
                    -Body $formData `
                    -WebSession $session `
                    -MaximumRedirection 5 `
                    -ErrorAction SilentlyContinue
                
                # 检查是否有下载链接的跳转
                if ($response.Content -match 'https?://[^""\s]+MDK[^""\s]+\.exe') {
                    $downloadUrl = $Matches[0]
                    Write-Host "[→] 找到下载链接: $downloadUrl" -ForegroundColor Green
                    Write-Host "[→] 开始下载 (872 MB)..." -ForegroundColor Yellow
                    
                    Invoke-WebRequest -Uri $downloadUrl -OutFile $InstallerFile -WebSession $session
                    
                    if (Test-Path $InstallerFile) {
                        Write-Host "[✓] 下载完成!" -ForegroundColor Green
                    }
                }
                else {
                    Write-Host "[!] 需要手动下载" -ForegroundColor Yellow
                    Write-Host "    请访问: https://www.keil.com/demo/eval/arm.htm" -ForegroundColor Cyan
                    
                    try {
                        Start-Process "https://www.keil.com/demo/eval/arm.htm"
                    }
                    catch {}
                    
                    $userInput = Read-Host "下载完成后按 Enter 继续..."
                }
            }
            catch {
                Write-Host "[!] 自动下载失败: $_" -ForegroundColor Red
                Write-Host "    请手动访问下载页面" -ForegroundColor Yellow
                Start-Process "https://www.keil.com/demo/eval/arm.htm"
                $userInput = Read-Host "下载完成后按 Enter 继续..."
            }
        }
        
        # 检查文件是否已下载
        if (-not (Test-Path $InstallerFile)) {
            Write-Host ""
            Write-Host "[!] 未检测到安装包文件" -ForegroundColor Red
            Write-Host "    请确认 MDK543a.exe 已放在脚本同目录下" -ForegroundColor Yellow
            $userInput = Read-Host "准备好后按 Enter 继续安装（或按 Ctrl+C 取消）"
        }
    }
}

# ─── 步骤 2: 安装 ───────────────────────────────────────
if (Test-Path $InstallerFile) {
    Write-Host ""
    Write-Host "[2/3] 准备安装 Keil MDK-ARM v5.43a..." -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Magenta
    Write-Host "  安装步骤:" -ForegroundColor White
    Write-Host ""
    Write-Host "  1. 右键以管理员身份运行: $InstallerFile" -ForegroundColor Cyan
    Write-Host "  2. 点击 Next → I Agree" -ForegroundColor White
    Write-Host "  3. 选择安装路径 (建议默认)" -ForegroundColor White
    Write-Host "     C:\Keil_v5\" -ForegroundColor Cyan
    Write-Host "  4. 填写用户信息 (随意)" -ForegroundColor White
    Write-Host "  5. 等待安装完成 (可能需要5-10分钟)" -ForegroundColor White
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Magenta
    Write-Host ""
    
    try {
        Write-Host "[→] 正在启动安装程序 (请求管理员权限)..." -ForegroundColor Green
        Start-Process -FilePath $InstallerFile -Verb RunAs
        Write-Host "[✓] 安装程序已启动，请按照安装向导完成安装" -ForegroundColor Green
    }
    catch {
        Write-Host "[!] 无法自动启动安装程序" -ForegroundColor Red
        Write-Host "    请手动找到文件并右键以管理员身份运行:" -ForegroundColor Yellow
        Write-Host "    $InstallerFile" -ForegroundColor Cyan
    }
}
else {
    Write-Host "[!] 未找到安装包，请先下载" -ForegroundColor Red
}

# ─── 步骤 3: 安装后配置 ─────────────────────────────────
$keilPaths = @(
    "C:\Keil_v5\UV4\UV4.exe",
    "C:\Keil_v5\ARM\ARMCC\bin\fromelf.exe"
)

Write-Host ""
Write-Host "[3/3] 安装后检查..." -ForegroundColor Yellow
Write-Host ""

$uv4Found = $false
foreach ($p in $keilPaths) {
    if (Test-Path $p) {
        Write-Host "[✓] $p" -ForegroundColor Green
        if ($p -match "UV4\.exe$") { $uv4Found = $true }
    }
    else {
        Write-Host "[ ] $p" -ForegroundColor DarkGray
    }
}

if ($uv4Found) {
    # 添加到 PATH
    $uv4Dir = Split-Path -Parent (Resolve-Path "C:\Keil_v5\UV4\UV4.exe")
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$uv4Dir*") {
        try {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$uv4Dir", "User")
            Write-Host ""
            Write-Host "[✓] 已将 UV4 添加到用户 PATH 环境变量" -ForegroundColor Green
            Write-Host "    重启终端后可直接使用 UV4.exe 命令" -ForegroundColor White
        }
        catch {
            Write-Host "[!] PATH 添加失败，请手动添加: $uv4Dir" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  安装完成后的验证命令:" -ForegroundColor White
Write-Host ""
Write-Host "  UV4.exe -?            # 查看命令行帮助" -ForegroundColor Gray
Write-Host "  UV4.exe -b project.uvprojx   # 命令行编译项目" -ForegroundColor Gray
Write-Host ""
Write-Host "  详细使用指南请查看同目录下的 SKILL.md 文件" -ForegroundColor White
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
