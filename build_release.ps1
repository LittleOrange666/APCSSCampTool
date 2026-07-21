param(
    [string]$Version
)
if ($Version -eq "") {
  Write-Host "Please provide a version number"
  exit 1
}
$imageName = "littleorange666/apcs_tool"

Write-Host "Building version $Version"
docker build . -t "${imageName}:$Version"
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Pushing version $Version"
docker push "${imageName}:$Version"
if ($LASTEXITCODE -ne 0) { exit 1 }
