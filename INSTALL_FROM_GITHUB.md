# Install From GitHub

This repository can be used in two ways.

## Codex Skill

Clone the repository into your Codex skills directory:

```powershell
git clone https://github.com/<your-name>/graduation-thesis-writer.git $env:USERPROFILE\.codex\skills\graduation-thesis-writer
```

Restart or refresh Codex, then ask Codex to use `graduation-thesis-writer`.

## Standalone CLI

```powershell
git clone https://github.com/<your-name>/graduation-thesis-writer.git
cd graduation-thesis-writer
py -m pip install -r requirements.txt
py -m graduation_thesis_writer --help
```

The Codex skill also bundles a copy of the CLI under `scripts/thesis_tool`.
