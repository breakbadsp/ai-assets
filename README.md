# Personal AI assets

Shared instructions and language conventions for AI coding tools.

- `AGENTS.md`: global agent guidance.
- `conventions/cpp.md`: C++ naming, layout, and composition preferences.
- `workspace/AGENTS.md`: guidance for the home development workspace.
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

The last link preserves compatibility with older project references.
The installer refuses to overwrite existing files or unrelated links.
The repository must be installed at `~/ai` because the guidance uses that path.

## Maintain

Edit the files in this repository; the linked paths reflect changes immediately.
Add conventions for other languages under `conventions/`, then reference them
from `AGENTS.md`. Keep project-specific rules in their project repositories.
Commit and push updates to keep the GitHub backup current:

```sh
git add AGENTS.md conventions workspace README.md install.sh
git commit -m "Update AI guidance"
git push
```
