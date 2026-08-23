#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$img = Join-Path $here "lsforzini44_lock_screen_2560x1440.jpg"

if (-not (Test-Path -LiteralPath $img)) {
    throw "Lock screen image not found: $img"
}

Write-Host "[INFO] Setting lock screen → $img"

# Enterprise / Personalization CSP (most reliable)
$csp = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\PersonalizationCSP"
if (-not (Test-Path $csp)) {
    New-Item -Path $csp -Force | Out-Null
}
New-ItemProperty -Path $csp -Name "LockScreenImagePath" -Value $img -PropertyType String -Force | Out-Null
New-ItemProperty -Path $csp -Name "LockScreenImageUrl" -Value $img -PropertyType String -Force | Out-Null
New-ItemProperty -Path $csp -Name "LockScreenImageStatus" -Value 1 -PropertyType DWord -Force | Out-Null

# Group Policy personalization lock image
$pol = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization"
if (-not (Test-Path $pol)) {
    New-Item -Path $pol -Force | Out-Null
}
New-ItemProperty -Path $pol -Name "LockScreenImage" -Value $img -PropertyType String -Force | Out-Null
New-ItemProperty -Path $pol -Name "NoChangingLockScreen" -Value 0 -PropertyType DWord -Force | Out-Null

# Ensure Spotlight is not overriding
$cdm = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
if (Test-Path $cdm) {
    Set-ItemProperty -Path $cdm -Name "RotatingLockScreenEnabled" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
    Set-ItemProperty -Path $cdm -Name "RotatingLockScreenOverlayEnabled" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
}

Write-Host "[INFO] Registry keys written"
Get-ItemProperty -Path $csp | Select-Object LockScreenImagePath, LockScreenImageUrl, LockScreenImageStatus | Format-List
Write-Host "[INFO] Done. Lock screen (Win+L) to verify."
