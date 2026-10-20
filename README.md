# Personal AI assets

Shared instructions and language conventions for AI coding tools.

- `AGENTS.md`: global agent guidance.
- `conventions/cpp.md`: C++ naming, layout, and composition preferences.
- `workspace/AGENTS.md`: guidance for the home development workspace.
- `skills/`: fourteen shared pstack skills for simpler code, automation, and verification.
- `install.sh`: links these assets into the locations agents discover.

## Restore or install

Clone this repository into `~/ai`, then run:

```sh
git clone https://github.com/breakbadsp/ai-assets.git ~/ai
cd ~/ai
./install.sh
```

The installer creates these links:

- `~/.codex/AGENTS.md` → `~/ai/AGENTS.md`
- `~/AGENTS.md` → `~/ai/workspace/AGENTS.md`
- `~/.codex/conventions/cpp.md` → `~/ai/conventions/cpp.md`
- `~/.agents/skills/<skill-name>` → matching directories in `~/ai/skills/`
- `~/.claude/skills/<skill-name>` → matching directories in `~/ai/skills/`

The `cpp.md` link preserves compatibility with older project references.
The installer refuses to overwrite existing files or unrelated links.
The repository must be installed at `~/ai` because the guidance uses that path.

## Shared skills

The fourteen skills come from [Poteto's pstack](https://github.com/cursor/plugins/tree/a66a8931c2dd71f1ed6abf6a52b1898a9f389ae4/pstack),
at commit `a66a8931c2dd71f1ed6abf6a52b1898a9f389ae4`. Their instructions
are unchanged. The [upstream MIT license](skills/LICENSE) applies to these skills.

The global links make the skills available to Codex and Claude Code in existing
and future projects. These skills are manual-only (`disable-model-invocation`),
so Claude reads them through the rules in `~/.claude/CLAUDE.md`. Codex users can
select one with `/skills`. Full instructions load when a skill is
used. Run `./install.sh` after adding another shared skill.
Use `./install.sh --skills-only` to install skills while preserving existing
guidance links.

## Maintain

Edit the files in this repository; the linked paths reflect changes immediately.
Add conventions for other languages under `conventions/`, then reference them
from `AGENTS.md`. Keep project-specific rules in their project repositories.
Commit and push updates to keep the GitHub backup current:

```sh
git add AGENTS.md conventions workspace skills README.md install.sh
git commit -m "Update AI guidance"
git push
```
