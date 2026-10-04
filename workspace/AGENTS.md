# Repository Guidelines

## Project Structure & Module Organization

This directory (`/home/daksh`) is a development workspace, not a standalone Git repository. Work within the relevant project before making changes.

- `src/` contains projects including `modern_exchng_cpp/`, `sp/`, `triangulator/`, and `oss/tigerbeetle/`.
- `Projects/` contains additional project directories, including `js_src/` and `t3ccode/`.
- Tests and assets belong to their individual projects; there is no shared root-level layout. For example, `src/sp/tests/` contains its own Makefile.

Read the target project's README and any applicable nested `AGENTS.md` before editing. Keep changes scoped to that project.

## Build, Test, and Development Commands

There is no workspace-wide build, test, or development command. Run commands from the selected project's directory.

- `cd ~/src/sp` selects the `sp` project; consult `README.md` for setup and usage.
- `git status --short` checks local changes when run inside a valid repository.
- `git log -10 --oneline` shows that repository's recent commit conventions.

Inspect project build files before executing targets. Makefiles exist in `src/triangulator/` and several `src/sp/` subdirectories; do not assume they expose identical targets.

## Coding Style & Naming Conventions

Before writing, editing, or reviewing C++ code, read and apply the global C++ naming and style conventions in `$HOME/ai/conventions/cpp.md`. For other languages, match the surrounding code's indentation, naming, and language conventions. Use each project's configured formatter and linter where available. Avoid unrelated formatting changes and preserve existing file organization.

## Testing Guidelines

Use the selected project's documented test framework and commands. Follow nearby test naming patterns, and add regression coverage for changed behavior when practical. No workspace-wide coverage threshold is defined. Include the exact validation commands and results in your change description.

## Commit & Pull Request Guidelines

Root-level Git history is unavailable. Inspect the target repository's history and contribution instructions before committing. Keep commits focused and describe the concrete change. Pull requests should explain the problem, implementation, and validation; link relevant issues and include screenshots for visible interface changes.

## Security & Configuration

Keep personal configuration, credentials, shell history, and downloaded files outside project commits. Review staged changes from the target repository before committing.
