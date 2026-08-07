param(
    [string]$DockerUsername = "lokizhan",
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"
$image = "$DockerUsername/pcb-file-checker"

Write-Host "Checking Docker..."
docker version | Out-Null

Write-Host "Signing in to Docker Hub..."
docker login

Write-Host "Building $image..."
docker build -t "${image}:${Version}" -t "${image}:latest" .

Write-Host "Testing the image with the included sample files..."
$samplePath = (Resolve-Path ".\sample-gerber").Path
docker run --rm -v "${samplePath}:/data:ro" "${image}:${Version}" /data --assembly
if ($LASTEXITCODE -ne 0) {
    throw "The sample test failed. Do not push the image until the error is fixed."
}

Write-Host "Pushing version tag..."
docker push "${image}:${Version}"

Write-Host "Pushing latest tag..."
docker push "${image}:latest"

Write-Host "Done. Open Docker Hub and add the README.md text to the Repository overview."
