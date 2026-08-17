## PHASE 0 — Prerequisite: gentle-ai

> **IMPORTANT**: gentle-ai is the fundamental requirement of this workflow. Without it, the
> SDD orchestrator, Engram (persistent memory), curated skills, and multi-IDE
> routing remain inactive. The wizard CANNOT complete correctly without gentle-ai.
> This phase installs or verifies it automatically — never skip it.

### Step 0.1 — Verify if gentle-ai is installed

```bash
which gentle-ai 2>/dev/null && gentle-ai --version 2>/dev/null
```

**Path A — gentle-ai is NOT installed** (the previous command fails or returns no output):

Tell the user:

```
gentle-ai is not installed on this machine.

gentle-ai is a mandatory requirement of this workflow. Without it:
- The SDD orchestrator does not work (no automatic phases).
- Engram (persistent memory between sessions) is not available.
- Curated skills for React, TypeScript, Tailwind, etc. are not loaded.
- Multi-IDE routing (Claude Code, Cursor, Windsurf, Kiro, etc.) is not configured.

The workflow can run partially without gentle-ai, but it will be incomplete
and some blocks (SDD, Block 3, Block 4) will not work as documented.

I am going to install it now. Shall I continue with the automatic installation? [yes / no / later]

- "yes" → install now and continue with the wizard.
- "no" → stop the wizard. You can install gentle-ai manually using
          the commands in section 4.3 of the master document, or re-run /wf-init later.
- "later" → mark the wizard as incomplete and continue without gentle-ai.
             Blocks that depend on it will be marked as pending.
```

**Wait for user response.**

If they respond "yes", run the installation (Step 0.2).
If they respond "no", terminate the wizard with a clear message.
If they respond "later", continue to Phase 1 but add a visible warning at the
end of the generated AGENTS.md:
```
<!-- WF-WARNING: gentle-ai not installed. SDD, Engram and skills unavailable.
     Install with: brew install gentle-ai && gentle-ai install
     Then run /wf-refresh to complete the configuration. -->
```

**Path B — gentle-ai IS installed**: continue directly to Step 0.3.

---

### Step 0.2 — Automatic installation of gentle-ai

Detect the operating system:

```bash
uname -s 2>/dev/null || echo "unknown"
```

**On macOS / Linux (Homebrew available)**:

Verify if Homebrew is installed:
```bash
which brew 2>/dev/null
```

If Homebrew is available, install with:
```bash
brew tap Gentleman-Programming/homebrew-tap
brew trust --formula gentleman-programming/tap/gentle-ai
brew install gentle-ai
```

If Homebrew is NOT available, inform:
```
Homebrew is not installed. Options:
1. Install Homebrew first: https://brew.sh — then re-run /wf-init.
2. Install gentle-ai with Go (if you have Go installed):
   go install github.com/gentleman-programming/gentle-ai/cmd/gentle-ai@latest
3. Install manually by downloading the binary from:
   https://github.com/Gentleman-Programming/gentle-ai/releases
```
Stop the wizard and ask the user to choose an option.

**On Windows (Scoop)**:

Verify if Scoop is available:
```bash
where scoop 2>/dev/null || powershell -Command "Get-Command scoop" 2>/dev/null
```

If available:
```bash
scoop bucket add gentleman https://github.com/Gentleman-Programming/scoop-bucket
scoop install gentle-ai
```

If Scoop is NOT available:
```
Scoop is not installed. Options on Windows:
1. Install Scoop first: https://scoop.sh — then re-run /wf-init.
2. Download the .exe binary from:
   https://github.com/Gentleman-Programming/gentle-ai/releases
   and place it in a folder that is in your PATH.
```

**After installing the binary**, run the agent setup:

```bash
gentle-ai install
```

Tell the user:
```
gentle-ai installed successfully. I will now configure the AI agents
detected on your machine with the "full-gentleman" preset.

The `gentle-ai install` command will show you a list of detected agents.
Mark the ones you commonly use. You can add more later with:
  gentle-ai install --agent <name> --preset full-gentleman

Proceed with the interactive agent installation and let me know when it finishes.
```

**Wait for user confirmation that `gentle-ai install` finished.**

---

### Step 0.2.1 — If installation was blocked by corporate policy

> **Why this step exists**: some IT teams block the installation of
> unsigned/unapproved third-party binaries at the OS or endpoint management
> level (MDM/EDR — e.g. Intune, Automox, Jamf, or corporate antivirus).
> This looks different from "Homebrew is not installed" —
> it is a deliberate block, not a missing tool. Confusing the two cases
> leads the developer to try solutions that will not work.

**Signs that it is a policy block, not a missing tool**:

- The installation command runs but ends with `Permission denied`,
  `Operation not permitted`, or an exit code other than "command not
  found".
- macOS blocks execution with a Gatekeeper dialog ("cannot be opened
  because the developer could not be verified") that does not go away
  even with `xattr -d com.apple.quarantine`.
- A corporate antivirus/EDR (CrowdStrike, Defender for Endpoint, SentinelOne,
  etc.) reports the binary as blocked or quarantined immediately after
  download.
- The AI IDE/CLI itself (Claude Code, Cursor, etc.) refuses to run the
  install command citing an organizational security rule.

**If you detect any of these signs**, clearly inform the developer
that this is NOT a technical problem they can resolve on their own, and offer
the step-by-step manual installation workaround as an alternative while they
resolve the block with their IT team:

```
⚠ gentle-ai installation appears to be blocked by your organization's
security policy (not a missing Homebrew/Scoop issue).

This typically means your IT team restricts unapproved third-party
binaries. The correct course of action is to request an exception or
approval for gentle-ai from your IT team — I cannot and should not attempt
to bypass that policy.

In the meantime, here are the steps to install gentle-ai manually from
terminal, in case your policy allows binaries downloaded directly
(as opposed to package managers like Homebrew/Scoop, which some policies
do specifically block):

1. Download the binary for your operating system directly
   from the releases page:
   https://github.com/Gentleman-Programming/gentle-ai/releases

   Choose the file that matches your OS and architecture, for example:
     gentle-ai_darwin_arm64.tar.gz   (macOS Apple Silicon)
     gentle-ai_darwin_amd64.tar.gz   (macOS Intel)
     gentle-ai_linux_amd64.tar.gz    (Linux)
     gentle-ai_windows_amd64.zip     (Windows)

2. Extract the downloaded archive:
     tar -xzf gentle-ai_<your-os>_<your-arch>.tar.gz
   (On Windows, extract the .zip with File Explorer or `Expand-Archive`.)

3. Move the binary to a folder already in your PATH, or add the folder
   where you extracted it to your PATH. Example on macOS/Linux:
     mkdir -p ~/bin
     mv gentle-ai ~/bin/
     echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc   # or ~/.bashrc depending on your shell
     source ~/.zshrc

4. If macOS blocks the binary via Gatekeeper ("unverified developer"
   dialog), and your security policy allows you to do it yourself:
     xattr -d com.apple.quarantine ~/bin/gentle-ai
   If your organization manages this via MDM and you do not have permission
   to run this command, this is exactly the point where you need IT
   approval — there is no legitimate workaround beyond this.

5. Verify it was installed:
     which gentle-ai && gentle-ai --version

6. If step 5 works, continue with `gentle-ai install` normally
   (Step 0.2 of this wizard). If it is still blocked at this point,
   the block is at the general binary execution policy level, not specific
   to Homebrew — you need the IT exception to continue, no way around it.

Were you able to complete these steps, or should I note this as pending
and continue without gentle-ai for now? [completed / pending — continue without gentle-ai]
```

**PAUSE — Wait for developer response.**

- If `completed`: verify with `which gentle-ai && gentle-ai --version` and
  continue the wizard normally from where it stopped.
- If `pending`: continue the wizard as in the "gentle-ai not
  available, continue without it" case already documented in this Step 0 (the AGENTS.md
  is generated with the `WF-WARNING: gentle-ai not installed` warning).

**Rule for the executing agent**: never suggest disabling or bypassing an
IT-managed security control (for example, never suggest disabling
a corporate antivirus or modifying an MDM policy). The manual installation
workaround is valid only up to the point where the block is at the
developer's own OS level (Gatekeeper without MDM management) — beyond
that, the only correct path is IT approval.

---

### Step 0.3 — Check if gentle-ai needs an update

With gentle-ai installed, get the local version:

```bash
gentle-ai --version
```

Then try to get the latest remote version. First check if there is network access:

```bash
curl -s --max-time 5 "https://api.github.com/repos/Gentleman-Programming/gentle-ai/releases/latest" 2>/dev/null | grep '"tag_name"' | head -1
```

If there is network access and a response:

Compare local vs remote version. Decide if the update is critical using this heuristic:

- **MAJOR update** (e.g. v1.x.x → v2.x.x): **mandatory for the wizard**. SDD phases and sub-agents may have breaking changes. Strongly recommend updating before continuing.
- **MINOR update** (e.g. v1.2.x → v1.3.x): suggested. There may be improvements to the SDD orchestrator or skills. The wizard works with the current version.
- **PATCH update** (e.g. v1.2.3 → v1.2.4): optional. Bug fixes. Does not block anything.

Present the result to the user with a clear recommendation:

```
gentle-ai installed: v<LOCAL>
gentle-ai available: v<REMOTE>

<If there is a major version difference>:
  RECOMMENDATION: Major update available. This wizard was designed for v<REMOTE>.
  Updating before continuing is HIGHLY recommended to ensure compatibility.
  Update now? [yes / no, continue with current version]

<If there is a minor version difference>:
  RECOMMENDATION: Minor update available with improvements to the SDD orchestrator.
  It is not blocking, but updating is recommended.
  Update now? [yes / no, continue with current version]

<If there is a patch version difference>:
  A patch is available (bug fixes). Not required for this wizard.
  Update anyway? [yes / no]

<If they are on the same version>:
  gentle-ai is up to date. ✓
```

If the user confirms update, run:

```bash
brew upgrade gentle-ai   # macOS/Linux with Homebrew
# or
scoop update gentle-ai   # Windows

gentle-ai upgrade   # updates internal components (skills, sub-agents, configs)
```

If there is no network access, inform that the remote version could not be verified and continue.

### Step 0.3.1 — Compatibility detection (release notes analysis)

> **Why this step exists**: comparing version numbers (Step 0.3) tells you there
> is a new version, but it does not tell you if that version changed something this wizard
> takes for granted — command names (`gentle-orchestrator`, `gentle-ai doctor`,
> `gentle-ai sync`), config paths, or flags. This step is lightweight: it does not execute anything
> from gentle-ai, it only analyzes text from the release notes you already obtained in
> Step 0.3, looking for risk signals near the terms the wizard hardcodes.

Reuse the GitHub API response from Step 0.3 (the `body` field from
`/releases/latest` already contains the full release text — no additional
network call is needed):

```bash
curl -s --max-time 5 "https://api.github.com/repos/Gentleman-Programming/gentle-ai/releases/latest" 2>/dev/null | grep -A 200 '"body"'
```

Terms hardcoded by this wizard that warrant monitoring (keep this list updated in each wizard version):

```
gentle-orchestrator, sdd-orchestrator, gentle-ai doctor, gentle-ai sync,
gentle-ai install, gentle-ai upgrade, gentle-ai skill-registry, engram,
sdd-init, sdd-propose, sdd-tasks, sdd-design, sdd-apply, sdd-verify
```

Search the release text, near those terms, for words indicating
disruptive change: `renamed`, `removed`, `breaking`, `deprecated`, `changed to`,
`migrated`, `no longer`, or the Spanish equivalents if the release is in
Spanish. This is text analysis by the agent, not command execution —
it does not trigger any smoke tests against the actual installation.

**If NO risk signals are detected**: continue normally, no additional message.

**If risk signals ARE detected**, inform the developer at that moment:

```
⚠ Possible compatibility change detected in gentle-ai v<REMOTE>

The release mentions the following near "<affected term>":
  "<brief excerpt from the release note, 1-2 lines max>"

This wizard uses "<affected term>" in several steps. It is possible that
something has been renamed, moved, or removed in the version you just detected.

What would you prefer?
  [continue]  — proceed with the wizard. If the affected term fails in any
                step, I will attempt the simplest adaptation I can infer
                from the release text (e.g. use the new name if the change
                is an obvious rename) and I will tell you explicitly
                at the moment it happens — I never do it silently.
  [stop]      — stop here. You can review the full changelog at
                https://github.com/Gentleman-Programming/gentle-ai/releases
                before continuing.
```

**PAUSE — Wait for developer response.**

Regardless of the response, write a local file with the finding
(never committed — it is wizard scratch, not project):

```bash
cat > /tmp/wf-compat-issue-$(date +%Y%m%d-%H%M%S).md << 'EOF'
# Possible incompatibility detected — wf-init vs gentle-ai

**Date**: <date>
**Detected gentle-ai version**: <REMOTE>
**Affected term**: <term>
**Release note fragment**:
> <fragment>

**Developer decision**: <continue | stop>
**Adaptation applied this session** (if continued): <describe or "none">

---

Command ready to report this to the wizard repo (you need your own
GitHub account authenticated with `gh auth login` — you don't need
write access to the repo, any account can open issues in
a public repo):

gh issue create \
  --repo hugoafj/ai-workflow-wizard \
  --title "Possible incompatibility: gentle-ai v<REMOTE> vs wf-init v<WIZARD_VERSION>" \
  --body "Affected term: <term>. Release note fragment: <fragment>. Automatically detected by wf-init during wizard execution."
EOF
```

Inform the developer where the file was saved and offer the action, without executing it yet:

```
I saved the details to /tmp/wf-compat-issue-<timestamp>.md, including the
`gh issue create` command already assembled to report it to the wizard repo.

Would you like me to report it right now with that command? [yes / no, I will do it later]
```

**If the developer responds "yes"**: run the `gh issue create` command as it
was assembled. If it fails due to missing authentication (`gh auth login` not configured)
or any other reason, show the error as-is and do not retry with another
strategy — the developer decides how to proceed.

**If the developer responds "no" or any "later" variant**: continue without
executing anything. The file in `/tmp/` remains available for later use.

**Rule for the executing agent**: never run `gh issue create` without the
developer explicitly asking for it in that session. Never assume the developer
has write permissions on the wizard repo — they do not need it to open
an issue on a public repo, but they do need their own active `gh auth login`
session. If they do not have it, the command fails on its own and that is the
correct behavior, not a bug you should solve through another path.

---

> **⛔ STOP HERE — do not execute anything else.**
> **Persistence (contract `wf-init/lib/state.md`)**: before advancing, `wf_state_init` if it doesn't exist, and save in `.wizard-state.json` → `gentle_ai` (`installed`, `version`, `install_choice`, `os`, and `warning_incomplete=true` if the user chose "later"). Mark `phases.phase0.status=done` and `phase_pointer="phase0b"` (`wf_phase_done phase0 phase0b`).
> Tell the user: *"Installation and version verified. Reply **continue** to run the gentle-ai health check."*
> Wait for the response. Only when they confirm, execute in bash:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"
wf_state_init
wf_phase_done phase0 phase0b
cat "$WF_DIR/phase0b.md"
```
