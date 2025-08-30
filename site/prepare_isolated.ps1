# Copies images from the main app into site/static/img to make the site fully isolated
$source = Join-Path $PSScriptRoot '..\app\static\img'
$dest = Join-Path $PSScriptRoot 'static\img'
if (-Not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest | Out-Null }
Get-ChildItem -Path $source -File | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $dest -Force
}
Write-Host "Copied images from $source to $dest"
