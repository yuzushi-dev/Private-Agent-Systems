# Governed second-brain starter

This directory is the runnable companion to
[`Building a Governed LLM Wiki as a Second Brain`](https://github.com/yuzushi-dev/Private-Agent-Systems/blob/main/chapters/building-a-governed-llm-wiki.md).
Copy `starter-kit/` to a private location, initialize your own version history,
and replace the placeholder notes with your own sources and operational records.

Markdown files are canonical. Obsidian is an optional interface. Claude Code
reads [`CLAUDE.md`](CLAUDE.md), Codex reads [`AGENTS.md`](AGENTS.md), and both
entry files point to the same operating specification.

## Start on Linux or macOS

```bash
git clone https://github.com/yuzushi-dev/Private-Agent-Systems /tmp/private-agent-systems
cp -R /tmp/private-agent-systems/starter-kit ~/second-brain
cd ~/second-brain
git init
git config --get user.name
git config --get user.email
git add .
git commit -m "initialize governed second brain"
```

If either identity check returns no value, set a real repository-local identity
before the commit:

```bash
git config user.name "Your Name"
git config user.email "you@example.com"
```

## Start on Windows PowerShell

```powershell
git clone https://github.com/yuzushi-dev/Private-Agent-Systems "$env:TEMP\private-agent-systems"
Copy-Item -Recurse "$env:TEMP\private-agent-systems\starter-kit" "$HOME\second-brain"
Set-Location "$HOME\second-brain"
git init
git config --get user.name
git config --get user.email
git add .
git commit -m "initialize governed second brain"
```

Set a repository-local Git identity first if either identity check returns no
value.

Start `claude` or `codex` from the vault root. The starter disables Claude auto
memory and Codex memories for vault work. Keep those settings disabled unless a
separate review approves client-generated state outside the vault.

Direct vault-root access is the default. Treat cross-repository filesystem MCP
as an advanced route: current server releases can replace configured paths with
client-provided roots. Follow the chapter's root-verification and OS-isolation
requirements before enabling it.

Keep credentials, tokens, cookies, private keys, and unrelated personal data
outside the vault.
