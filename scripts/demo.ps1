param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$UrlToIngest = "https://vi.wikipedia.org/wiki/Tr%C3%AD_tu%E1%BB%87_nh%C3%A2n_t%E1%BA%A1o",
    [string]$SessionId = "team-a"
)

$ingestBody = @{
    url = $UrlToIngest
} | ConvertTo-Json

Write-Host "==> Ingest URL"
Invoke-RestMethod -Method Post -Uri "$BaseUrl/ingest-url" -ContentType "application/json" -Body $ingestBody

$chatBody = @{
    session_id = $SessionId
    message    = "Tom tat 3 y chinh cua tai lieu vua nap"
} | ConvertTo-Json

Write-Host "==> Chat voi Agent"
Invoke-RestMethod -Method Post -Uri "$BaseUrl/chat" -ContentType "application/json" -Body $chatBody
