# Developers Notes

## Setup

- Please use the `make git_hooks` to setup and run the pre-commit hooks.

## Linting

At the moment we are using PyRight pegged at version 1.1.294.

## VS Code

- Although we use PyRight for linting (see [.pre-commit-config.yaml](./.pre-commit-config.yaml)), [PyRight recommends that you use PyLance when using VS Code](https://microsoft.github.io/pyright/#/installation?id=vs-code).

### Extensions

| Extension | Author | Description | Recommended/Optional |
|-----------|--------|-------------|-------------------------------|
| [Black Formatter](https://github.com/) | Microsoft | | Optional |
| [Code Spell Checker](https://github.com/) | Street Side Software | | Recommended |
| [Makefile Tools](https://github.com/) | Microsoft | | Recommended |
| [markdownlint](https://github.com/) | David Anson | | Recommended |
| [Markdown All in One](https://github.com/) | Yu Zhang | | Optional |
| [PyLance](https://github.com/) | Microsoft | | Recommended |
| [YAML](https://github.com/) | Red Hat | | Optional |

### Recommended User Settings JSON

Here is a snippet of some recommended settings to add to your VS Code User Settings. To open the user settings file where you can paste in the snippet below, press Ctrl+Shift+P to open the VS Code command palette and type 'User Settings', and then select 'Preferences: Open User Settings (JSON) from the dropdown list.

```json
    "editor.renderWhitespace": "all",
    "python.languageServer": "Pylance",
    "python.analysis.autoImportCompletions": true,
    "python.analysis.completeFunctionParens": true,
    "[python]": {
        "editor.rulers": [
            72,
            88
        ],
        "editor.defaultFormatter": "ms-python.black-formatter"
    },
    "python.analysis.diagnosticMode": "workspace",
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.include": [
        "**/*.py"
    ],
    "workbench.colorCustomizations": {"editorRuler.foreground": "#63636331"},
    "cSpell.caseSensitive": true,
    "cSpell.language": "en-GB",
    "cSpell.showAutocompleteSuggestions": true,
    "cSpell.showSuggestionsLinkInEditorContextMenu": true,
    "[markdown]": {
        "editor.defaultFormatter": "DavidAnson.vscode-markdownlint"
    },
    "[yaml]": {
        "editor.defaultFormatter": "redhat.vscode-yaml"
    },
    "files.autoSave": "afterDelay",
```
