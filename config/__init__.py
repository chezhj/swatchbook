# Single source of truth for the deployed version. The installer greps this file
# (VERSION_FILE in swatchbook_config.sh) and refuses to deploy a tag that doesn't
# match, so `cz bump` keeps it in step with the git tag (v<version>) and pyproject.
__version__ = "0.3.0"
