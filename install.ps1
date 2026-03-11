# ==============================================
# InstaLens - Instagram Followers Scraper
# One-line installer for Windows
# ==============================================

$ErrorActionPreference = "Stop"

# Configuration
$RepoUrl = "https://github.com/efdutra/InstaLens.git"
$PythonMinVersion = [Version]"3.9"
$NodeMinVersion = [Version]"18.0"

# ==============================================
# Helper Functions
# ==============================================

function Print-Header {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                        ║" -ForegroundColor Cyan
    Write-Host "║   📸 InstaLens Installer               ║" -ForegroundColor Cyan
    Write-Host "║   Instagram Followers Scraper          ║" -ForegroundColor Cyan
    Write-Host "║                                        ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Print-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "▶ $Message" -ForegroundColor Blue -BackgroundColor Black
}

function Print-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Print-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Print-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Ask-YesNo {
    param([string]$Question)
    
    while ($true) {
        $response = Read-Host "$Question (y/n)"
        if ($response -match '^[yY]') { return $true }
        if ($response -match '^[nN]') { return $false }
        Write-Host "Please answer 'y' or 'n'" -ForegroundColor Red
    }
}

# ==============================================
# Dependency Checks
# ==============================================

function Test-Python {
    Print-Step "Checking Python..."
    
    try {
        $pythonCmd = Get-Command python -ErrorAction Stop
        $version = (python --version 2>&1) -replace 'Python ', ''
        $pythonVersion = [Version]$version
        
        if ($pythonVersion -ge $PythonMinVersion) {
            Print-Success "Python $version found"
            return $true
        } else {
            Print-Warning "Python $version found, but $PythonMinVersion+ required"
            return $false
        }
    } catch {
        Print-Error "Python not found"
        return $false
    }
}

function Test-Node {
    Print-Step "Checking Node.js..."
    
    try {
        $nodeCmd = Get-Command node -ErrorAction Stop
        $version = (node --version) -replace 'v', ''
        $nodeVersion = [Version]$version
        
        if ($nodeVersion -ge $NodeMinVersion) {
            Print-Success "Node.js $version found"
            return $true
        } else {
            Print-Warning "Node.js $version found, but $NodeMinVersion+ required"
            return $false
        }
    } catch {
        Print-Error "Node.js not found"
        return $false
    }
}

function Test-Git {
    Print-Step "Checking Git..."
    
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $version = (git --version) -replace 'git version ', ''
        Print-Success "Git $version found"
        return $true
    } else {
        Print-Error "Git not found"
        return $false
    }
}

function Test-Pnpm {
    if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
        Print-Warning "pnpm not found - installing globally..."
        npm install -g pnpm
        Print-Success "pnpm installed"
    } else {
        Print-Success "pnpm found"
    }
}

function Ask-InstallLocation {
    $currentDir = Get-Location
    $defaultLocation = Join-Path $currentDir "InstaLens"
    
    Write-Host ""
    Print-Step "Choose installation directory"
    Write-Host ""
    Print-Info "Current directory: $currentDir"
    Write-Host ""
    
    if (Ask-YesNo "Install InstaLens in current directory ($defaultLocation)?") {
        return $defaultLocation
    } else {
        Write-Host ""
        $customPath = Read-Host "Enter installation path (or press Enter for $env:USERPROFILE\InstaLens)"
        
        if ([string]::IsNullOrWhiteSpace($customPath)) {
            return "$env:USERPROFILE\InstaLens"
        } else {
            return $customPath
        }
    }
}

function Install-Dependencies {
    # Check Git
    if (-not (Test-Git)) {
        Write-Host ""
        Print-Info "Git is required to clone the repository."
        Print-Info "Download from: https://git-scm.com/download/win"
        Print-Error "Please install Git and run this script again."
        exit 1
    }
    
    # Check Python
    if (-not (Test-Python)) {
        Write-Host ""
        Print-Info "Python 3.9+ is required to run InstaLens backend."
        Print-Info "Download from: https://www.python.org/downloads/"
        Print-Warning "Make sure to check 'Add Python to PATH' during installation!"
        
        if (Ask-YesNo "Open Python download page in browser?") {
            Start-Process "https://www.python.org/downloads/"
        }
        
        Print-Error "Please install Python 3.9+ and run this script again."
        exit 1
    }
    
    # Check Node.js
    if (-not (Test-Node)) {
        Write-Host ""
        Print-Info "Node.js 18+ is required to run InstaLens frontend."
        Print-Info "Download from: https://nodejs.org/"
        
        if (Ask-YesNo "Open Node.js download page in browser?") {
            Start-Process "https://nodejs.org/"
        }
        
        Print-Error "Please install Node.js 18+ and run this script again."
        exit 1
    }
    
    Test-Pnpm
}

# ==============================================
# Main Installation
# ==============================================

function Main {
    Print-Header
    
    # Ask where to install
    $InstallDir = Ask-InstallLocation
    Print-Info "Will install to: $InstallDir"
    
    # Check if already installed
    if (Test-Path $InstallDir) {
        Print-Info "InstaLens already installed at: $InstallDir"
        
        if (Ask-YesNo "Do you want to update and run?") {
            Set-Location $InstallDir
            Print-Step "Updating repository..."
            git pull
            Print-Success "Repository updated"
        } else {
            Set-Location $InstallDir
        }
    } else {
        # Check and install dependencies
        Install-Dependencies
        
        # Clone repository
        Print-Step "Cloning InstaLens repository..."
        git clone $RepoUrl $InstallDir
        Set-Location $InstallDir
        Print-Success "Repository cloned to: $InstallDir"
        
        # Setup backend
        Print-Step "Setting up backend..."
        Set-Location backend
        
        if (-not (Test-Path "venv")) {
            python -m venv venv
            Print-Success "Virtual environment created"
        }
        
        & .\venv\Scripts\Activate.ps1
        python -m pip install --upgrade pip --quiet
        pip install -r requirements.txt --quiet
        python -m playwright install chromium
        
        # Create .env file
        if (-not (Test-Path ".env")) {
            @"
# Browser settings
SESSION_FILE=session.json
HEADLESS=false
BROWSER_TYPE=chromium

# CORS Configuration (allow all for development)
CORS_ORIGINS=*
"@ | Out-File -FilePath ".env" -Encoding utf8
            Print-Success "Backend .env created"
        }
        
        Set-Location ..
        Print-Success "Backend setup complete"
        
        # Setup frontend
        Print-Step "Setting up frontend..."
        Set-Location frontend
        
        if (-not (Test-Path "node_modules")) {
            pnpm install
            Print-Success "Frontend dependencies installed"
        }
        
        Set-Location ..
        Print-Success "Frontend setup complete"
    }
    
    # Run application
    Write-Host ""
    Print-Header
    Print-Success "🚀 Installation complete!"
    Write-Host ""
    Print-Info "Starting InstaLens..."
    Write-Host ""
    
    # Start backend in background
    $BackendPath = Join-Path $InstallDir "backend"
    $BackendJob = Start-Job -ScriptBlock {
        param($Path)
        Set-Location $Path
        & .\venv\Scripts\Activate.ps1
        python main.py
    } -ArgumentList $BackendPath
    
    Start-Sleep -Seconds 5
    Print-Success "Backend started (Job ID: $($BackendJob.Id))"
    Print-Info "Backend running on: " -NoNewline
    Write-Host "http://localhost:8000" -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host ""
    
    # Start frontend (foreground - will show Vite output)
    Set-Location (Join-Path $InstallDir "frontend")
    Write-Host ""
    Print-Info "Starting frontend..."
    Print-Info "Frontend will run on: " -NoNewline
    Write-Host "http://localhost:5173" -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host ""
    Print-Warning "Press Ctrl+C to stop both servers"
    Write-Host ""
    
    pnpm dev
    
    # Cleanup on exit
    Stop-Job $BackendJob -ErrorAction SilentlyContinue
    Remove-Job $BackendJob -ErrorAction SilentlyContinue
}

# ==============================================
# Run
# ==============================================

try {
    Main
} catch {
    Write-Host ""
    Print-Error "Installation failed: $_"
    Write-Host ""
    Print-Info "Please check the error message above and try again."
    Print-Info "If the problem persists, open an issue at: https://github.com/efdutra/InstaLens/issues"
    exit 1
}
