param([Parameter(Mandatory = $true)][string]$SpecPath)
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion -lt [version]'7.3') {
    throw 'npm shim invocation requires PowerShell 7.3+ to preserve empty CLI arguments.'
}
$PSNativeCommandArgumentPassing = 'Standard'
$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$spec = Get-Content -LiteralPath $SpecPath -Raw -Encoding utf8 | ConvertFrom-Json
Set-Location -LiteralPath $spec.cwd
$cliArguments = @($spec.arguments | ForEach-Object { [string]$_ })
if ($spec.stdin_file) {
    $taskText = [System.IO.File]::ReadAllText($spec.stdin_file, $utf8)
    $taskText | & $spec.executable @cliArguments
} else {
    & $spec.executable @cliArguments
}
exit $LASTEXITCODE
