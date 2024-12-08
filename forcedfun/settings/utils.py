import os


def strtobool(val: str) -> bool:
    val = val.lower()
    return val in ("y", "yes", "t", "true", "on", "1", "True")


def getbool(
    var: str, default: bool = False, environ: dict[str, str] | None = None
) -> bool:
    _environ = environ or os.environ
    try:
        val = _environ[var]
    except KeyError:
        return default
    return strtobool(val)
