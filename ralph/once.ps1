# Get all issues content
$issues = Get-Content -Path "issues/*.md" -ErrorAction SilentlyContinue | Out-String
if ([string]::IsNullOrWhiteSpace($issues)) {
    $issues = "No issues found"
}

# Get recent commits
$commits = git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>$null | Out-String
if ([string]::IsNullOrWhiteSpace($commits)) {
    $commits = "No commits found"
}

# Get prompt content
$prompt = Get-Content -Path "ralph/prompt.md" -ErrorAction SilentlyContinue | Out-String

# Call agy
agy --prompt "Previous commits: $commits Issues: $issues $prompt"
