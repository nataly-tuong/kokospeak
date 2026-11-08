param(
    [switch]$Repair,
    [switch]$NoLaunch,
    [switch]$AllLanguages
)
$ErrorActionPreference = 'Stop'
$rootPath = $PSScriptRoot
$uvDirectory = Join-Path $rootPath '.runtime\uv'
$uvPath = Join-Path $uvDirectory 'uv.exe'
try {
    if (-not (Test-Path $uvPath)) {
        $installed = Get-Command uv -ErrorAction SilentlyContinue
        if ($installed) {
            $uvPath = $installed.Source
        } else {
            New-Item -ItemType Directory -Force $uvDirectory | Out-Null
            $bootstrap = Join-Path ([IO.Path]::GetTempPath()) ([IO.Path]::GetRandomFileName() + '.ps1')
            try {
                Write-Host "Installing KokoSpeak's private Python installer..."
                [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
                Invoke-WebRequest 'https://astral.sh/uv/install.ps1' -OutFile $bootstrap -UseBasicParsing -TimeoutSec 120
                $env:UV_UNMANAGED_INSTALL = $uvDirectory
                & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $bootstrap
                if ($LASTEXITCODE -ne 0) { throw 'The Python installer download failed.' }
            } finally {
                Remove-Item $bootstrap -ErrorAction SilentlyContinue
                Remove-Item Env:UV_UNMANAGED_INSTALL -ErrorAction SilentlyContinue
            }
        }
    }
    $env:UV_HTTP_TIMEOUT = '120'
    $env:UV_HTTP_RETRIES = '5'
    Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
    $setupArgs = @('run', '--no-project', '--no-config', '--python', '3.12', (Join-Path $rootPath 'scripts\setup.py'), '--uv', $uvPath)
    if ($Repair) { $setupArgs += '--repair' }
    if ($NoLaunch) { $setupArgs += '--no-launch' }
    if ($AllLanguages) { $setupArgs += '--all-languages' }
    & $uvPath @setupArgs
    exit $LASTEXITCODE
} catch {
    Write-Host "KokoSpeak setup stopped: $_" -ForegroundColor Red
    exit 1
}
