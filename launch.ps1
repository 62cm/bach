# BWV 772a — 独立原生小窗 480×360
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$exe = Join-Path $Root "BWV772a.exe"
if (Test-Path $exe) {
  Start-Process -FilePath $exe -WorkingDirectory $Root
  exit 0
}

$pyw = (Get-Command pyw -ErrorAction SilentlyContinue).Source
if (-not $pyw) { $pyw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source }
if (-not $pyw) { $pyw = (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $pyw) {
  Write-Host "未找到 python / pythonw，也没有 BWV772a.exe"
  exit 1
}

Start-Process -FilePath $pyw -ArgumentList "window.py" -WorkingDirectory $Root -WindowStyle Hidden
