# winget manifest for local windows install
winget install VirusTotal.vt-cli

# add vt.exe to system path for all future PS sessions--given vt.exe being located in C:\Users\username\Documents
$currentPath = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
$newPath = $currentPath + ";C:\Users\username\Documents"
[System.Environment]::SetEnvironmentVariable('Path', $newPath, 'Machine')
