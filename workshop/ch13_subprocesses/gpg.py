"""Helper: encrypt text with the `gpg` CLI (listings 13.7 and 13.8)."""

import asyncio
import shutil
from asyncio.subprocess import Process

GPG = ["gpg", "-c", "--batch", "--passphrase", "3ncryptm3", "--cipher-algo", "TWOFISH"]


def require_gpg() -> None:
    if shutil.which("gpg") is None:
        raise SystemExit("gpg is not installed (apt install gnupg / brew install gnupg)")


async def encrypt(text: str) -> bytes:
    process: Process = await asyncio.create_subprocess_exec(
        *GPG, stdout=asyncio.subprocess.PIPE, stdin=asyncio.subprocess.PIPE
    )
    stdout, _stderr = await process.communicate(text.encode())
    return stdout
