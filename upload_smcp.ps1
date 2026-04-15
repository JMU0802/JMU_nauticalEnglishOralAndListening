$smcpMd = Get-Content "F:\AI_CODING\JMU_nauticalEnglishOralAndListening\SMCP_DATA\SMCP.md" -Raw -Encoding UTF8
$body = @{ text = $smcpMd; description = "SMCP Standard Marine Communication Phrases" } | ConvertTo-Json -Depth 3 -Compress
$resp = Invoke-RestMethod -Uri "http://localhost:9621/documents/text" -Method POST -Body $body -ContentType "application/json; charset=utf-8"
Write-Host ($resp | ConvertTo-Json -Depth 2)
