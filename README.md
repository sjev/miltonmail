# MiltonMailer



Set of IMAP tools to automate boring mail management tasks

## How it works

* configuration is stored at `~/.milton
* passwords are protected with a passphrase. Set `MILTON_PASS` env variable.



## Development


1. develop and test in devcontainer (VSCode)
2. use `invoke` for local devops actions

## Tooling

* Automation: `invoke` - run `invoke -l` to list available commands. (uses `tasks.py`)
* Verisoning : `setuptools_scm`
* Linting and formatting : `ruff`
* Typechecking: `mypy`
