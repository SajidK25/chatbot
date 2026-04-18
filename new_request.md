# New Request From client to test the Bot

- Openclaw with Telegram or WhatsApp is good for now. Choose one instead of both. Also, we want it to work for Claude Code.
- Here are product list that you need to scalp : 
https://outopia.com/collections/men
 
https://outopia.com/collections/women


- After scalping , save product data using this standard:
https://developers.openai.com/commerce/specs/file-upload/products


- Also , We need documentation and instructions for openclaw use. See screenshot. And I post text here: 
Follow the documentation at https://raw.githubusercontent.com/reorc/kamay-cli-skill/refs/heads/main/references/INSTALL.md to install and configure Kamay CLI skill

# Kamay CLI Skill Installation Guide

## Installing the Skill

Install this repository into your Agent's skills directory to get complete usage guides and reference documentation.

### Method 1: Git Clone (Recommended, easy to update)

```bash
# For Claude Code
git clone https://github.com/reorc/kamay-cli-skill.git ~/.claude/skills/kamay-cli

# For OpenCode, OpenClaw, and other general Agents
git clone https://github.com/reorc/kamay-cli-skill.git ~/.agents/skills/kamay-cli
```

**Updating the Skill**:
```bash
cd ~/.claude/skills/kamay-cli  # or the corresponding agent directory
git pull
```

### Method 2: Download and Extract ZIP

```bash
# Download and extract to the corresponding directory
# For Claude Code
curl -L https://github.com/reorc/kamay-cli-skill/archive/refs/heads/main.zip -o /tmp/kamay-cli.zip
unzip /tmp/kamay-cli.zip -d ~/.claude/skills/
mv ~/.claude/skills/kamay-cli-skill-main ~/.claude/skills/kamay-cli

# For OpenCode, OpenClaw, and other general Agents
curl -L https://github.com/reorc/kamay-cli-skill/archive/refs/heads/main.zip -o /tmp/kamay-cli.zip
unzip /tmp/kamay-cli.zip -d ~/.agents/skills/
mv ~/.agents/skills/kamay-cli-skill-main ~/.agents/skills/kamay-cli
```

---

## Installing the CLI

### System Requirements

- **Operating System**: Linux, macOS, Windows (WSL2)
- **Network**: Requires connection to Kamay backend services
- **Authentication**: Requires a valid [Kamay](https://kamay.ai/) account

### Installation Methods

#### One-Click Install

Run the following Bash command for one-click installation:

```bash
OS=$(uname -s | tr '[:upper:]' '[:lower:]'); ARCH=$(uname -m | sed -e 's/x86_64/amd64/' -e 's/aarch64/arm64/'); curl -LO "https://github.com/reorc/kamay-cli-skill/releases/latest/download/kamay-${OS}-${ARCH}" && sudo install -m 755 "kamay-${OS}-${ARCH}" /usr/local/bin/kamay && rm "kamay-${OS}-${ARCH}" && kamay version
```

#### Manual Installation

Download the binary for your platform from [Releases](https://github.com/reorc/kamay-cli-skill/releases):

```bash
chmod +x ./kamay
mv ./kamay /usr/local/bin/kamay
```

### Verification

```bash
kamay --help
kamay version
```

You should see output similar to:

```
Kamay CLI is your data-driven marketing tools.
Discover market insights, create and manage creative contents.

Usage:
  kamay [command]

Available Commands:
  amazon      Amazon module commands
  auth        Authentication commands
  google      Google module commands
  meta        Meta module commands
  tiktok      Tiktok module commands
  version     Print the version number of Kamay CLI
```

## Authentication

When the user needs to authenticate, present these three options and let them choose:

1. **Email/Password** — "I have a Kamay account and know my credentials"
2. **API Key** — "I already have an API Key"
3. **Register a new key** — "Help me get a key" (opens a browser link for authorization)

### Option 1: Email/Password

```bash
kamay auth login --email "your@email.com" --password "yourpassword"
```

Ask the user for their email and password, then run the command.

### Option 2: I Already Have an API Key

```bash
kamay auth apikey --key <api-key>
```

Ask the user to provide their API Key, then run the command.

### Option 3: Register a New Key (Device Authorization)

For users who don't have an API Key yet, use the device authorization flow to generate one automatically.

**Step 1** — Initialize and get a verification link:

```bash
kamay auth device
```

The command prints a `VERIFICATION_URL`. Tell the user to open that link in their browser to log in and authorize.

**Step 2** — After the user confirms they have authorized, poll for the token:

```bash
kamay auth device --poll
```

If the output says `PENDING`, the user hasn't authorized yet — ask them to complete the browser step and run `--poll` again. The authorization expires after 5 minutes.

Once authorization succeeds, the API Key is automatically saved.

### Verify Login Status

```bash
kamay auth status
```

### Refresh Token

```bash
kamay auth refresh
```

### Logout

```bash
kamay auth logout
```

## Upgrade

### CLI Upgrade

Use the built-in update command:

```bash
kamay update
```

The command will automatically check for the latest version, download, and replace the current binary.

### Skill Upgrade

If you installed the skill via git clone:

```bash
cd ~/.claude/skills/kamay-cli  # or the corresponding agent directory
git pull
```

If you installed via ZIP download, re-download and extract the latest version.

## Uninstallation

### Uninstall Skill

```bash
# For Claude Code
rm -rf ~/.claude/skills/kamay-cli

# For OpenCode, OpenClaw, and other general Agents
rm -rf ~/.agents/skills/kamay-cli
```

### Uninstall CLI

```bash
# Delete binary file
sudo rm /usr/local/bin/kamay
# or
rm ~/.local/bin/kamay

# Delete configuration (optional)
rm -rf ~/.config/kamay
```

## FAQ

### Q: Getting "command not found"

A: Check:
1. Does the file have execute permission (Linux/macOS: `chmod +x`)
2. Is the file in your PATH
3. Has the terminal reloaded configuration (`source ~/.bashrc`)

### Q: Dynamic commands not loaded (only auth/version available)

A: Check:
1. Is network connection normal
2. Is the backend service available

### Q: Login failed

A: Check:
1. Is the email and password correct
2. Is network connection normal
3. Is the backend service available

### Q: How to view detailed logs

A: Set log level:

```bash
export KAMAY_LOG_LEVEL=debug
kamay --help
```

### Q: Kamay Team Contact

Email: kamay@reorc.ai

If you have any questions about usage, feel free to contact us.