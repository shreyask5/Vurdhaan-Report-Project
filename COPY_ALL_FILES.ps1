# PowerShell Script to Copy All Implementation Files to Correct Location
# Run from: C:\chrome-win64\vurdhaan report project\github\Vurdhaan-Report-Project

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  CSV Validation & AI Chat - File Copy Script" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Define source and destination
$sourceRoot = "C:\chrome-win64\vurdhaan report project\frontend\src"
$destRoot = "C:\chrome-win64\vurdhaan report project\github\Vurdhaan-Report-Project\frontend\src"

# Check if source exists
if (!(Test-Path $sourceRoot)) {
    Write-Host "❌ Source directory not found: $sourceRoot" -ForegroundColor Red
    Write-Host "Files may have already been moved or script is run from wrong location" -ForegroundColor Yellow
    exit 1
}

# Check if destination exists
if (!(Test-Path $destRoot)) {
    Write-Host "❌ Destination directory not found: $destRoot" -ForegroundColor Red
    exit 1
}

Write-Host "Source: $sourceRoot" -ForegroundColor Green
Write-Host "Dest: $destRoot" -ForegroundColor Green
Write-Host ""

# Create destination directories if they don't exist
$directories = @(
    "components\project",
    "services",
    "contexts",
    "pages",
    "utils"
)

Write-Host "Creating directories..." -ForegroundColor Yellow
foreach ($dir in $directories) {
    $fullPath = Join-Path $destRoot $dir
    if (!(Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  ✓ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  ✓ Exists: $dir" -ForegroundColor Gray
    }
}

Write-Host ""

# Function to copy files with progress
function Copy-ImplementationFiles {
    param (
        [string]$SourcePath,
        [string]$DestPath,
        [string]$FilePattern,
        [string]$Category
    )

    if (!(Test-Path $SourcePath)) {
        Write-Host "  ⚠ Source not found: $SourcePath" -ForegroundColor Yellow
        return 0
    }

    $files = Get-ChildItem -Path $SourcePath -Filter $FilePattern
    $count = 0

    foreach ($file in $files) {
        $destFile = Join-Path $DestPath $file.Name
        try {
            Copy-Item -Path $file.FullName -Destination $destFile -Force
            Write-Host "  ✓ Copied: $($file.Name)" -ForegroundColor Green
            $count++
        } catch {
            Write-Host "  ✗ Failed: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    return $count
}

# Copy Component Files (12 files)
Write-Host "Copying Component Files..." -ForegroundColor Yellow
$componentFiles = Copy-ImplementationFiles `
    -SourcePath (Join-Path $sourceRoot "components\project") `
    -DestPath (Join-Path $destRoot "components\project") `
    -FilePattern "*.tsx" `
    -Category "Components"
Write-Host "  → Copied $componentFiles component files" -ForegroundColor Cyan
Write-Host ""

# Copy Service Files (2 files)
Write-Host "Copying Service Files..." -ForegroundColor Yellow
$serviceFiles = Copy-ImplementationFiles `
    -SourcePath (Join-Path $sourceRoot "services") `
    -DestPath (Join-Path $destRoot "services") `
    -FilePattern "*.ts" `
    -Category "Services"
Write-Host "  → Copied $serviceFiles service files" -ForegroundColor Cyan
Write-Host ""

# Copy Context Files (2 files)
Write-Host "Copying Context Files..." -ForegroundColor Yellow
$contextFiles = Copy-ImplementationFiles `
    -SourcePath (Join-Path $sourceRoot "contexts") `
    -DestPath (Join-Path $destRoot "contexts") `
    -FilePattern "*.tsx" `
    -Category "Contexts"
Write-Host "  → Copied $contextFiles context files" -ForegroundColor Cyan
Write-Host ""

# Copy Page Files (3 files)
Write-Host "Copying Page Files..." -ForegroundColor Yellow
$pageFiles = Copy-ImplementationFiles `
    -SourcePath (Join-Path $sourceRoot "pages") `
    -DestPath (Join-Path $destRoot "pages") `
    -FilePattern "*.tsx" `
    -Category "Pages"
Write-Host "  → Copied $pageFiles page files" -ForegroundColor Cyan
Write-Host ""

# Copy Utility Files (3 files) - already created but verify
Write-Host "Verifying Utility Files..." -ForegroundColor Yellow
$utilFiles = @("csv.ts", "compression.ts", "validation.ts")
$utilCount = 0
foreach ($file in $utilFiles) {
    $destFile = Join-Path $destRoot "utils\$file"
    if (Test-Path $destFile) {
        Write-Host "  ✓ Exists: $file" -ForegroundColor Green
        $utilCount++
    } else {
        Write-Host "  ⚠ Missing: $file" -ForegroundColor Yellow
    }
}
Write-Host "  → Verified $utilCount utility files" -ForegroundColor Cyan
Write-Host ""

# Copy Type Files (2 files) - already created but verify
Write-Host "Verifying Type Files..." -ForegroundColor Yellow
$typeFiles = @("validation.ts", "chat.ts")
$typeCount = 0
foreach ($file in $typeFiles) {
    $destFile = Join-Path $destRoot "types\$file"
    if (Test-Path $destFile) {
        Write-Host "  ✓ Exists: $file" -ForegroundColor Green
        $typeCount++
    } else {
        Write-Host "  ⚠ Missing: $file" -ForegroundColor Yellow
    }
}
Write-Host "  → Verified $typeCount type files" -ForegroundColor Cyan
Write-Host ""

# Summary
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
$totalCopied = $componentFiles + $serviceFiles + $contextFiles + $pageFiles
Write-Host "Components: $componentFiles / 12" -ForegroundColor $(if ($componentFiles -eq 12) { "Green" } else { "Yellow" })
Write-Host "Services:   $serviceFiles / 2" -ForegroundColor $(if ($serviceFiles -eq 2) { "Green" } else { "Yellow" })
Write-Host "Contexts:   $contextFiles / 2" -ForegroundColor $(if ($contextFiles -eq 2) { "Green" } else { "Yellow" })
Write-Host "Pages:      $pageFiles / 3" -ForegroundColor $(if ($pageFiles -eq 3) { "Green" } else { "Yellow" })
Write-Host "Utils:      $utilCount / 3" -ForegroundColor $(if ($utilCount -eq 3) { "Green" } else { "Yellow" })
Write-Host "Types:      $typeCount / 2" -ForegroundColor $(if ($typeCount -eq 2) { "Green" } else { "Yellow" })
Write-Host "---" -ForegroundColor Gray
Write-Host "Total Copied: $totalCopied" -ForegroundColor Cyan
Write-Host "Total Files: $($totalCopied + $utilCount + $typeCount) / 24" -ForegroundColor Cyan
Write-Host ""

if (($totalCopied + $utilCount + $typeCount) -eq 24) {
    Write-Host "✅ ALL FILES SUCCESSFULLY COPIED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Update frontend/tailwind.config.ts"
    Write-Host "2. Add LZ-String to frontend/index.html"
    Write-Host "3. Create frontend/.env"
    Write-Host "4. Update frontend/src/App.tsx with routes"
    Write-Host "5. Run: cd frontend && npm install react-router-dom"
} else {
    Write-Host "⚠ Some files are missing. Check the output above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
