# Download a current vault ZIP through an approved SSH host alias (stdlib only).

import argparse
from hashlib import file_digest
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import NamedTemporaryFile
import time
from zipfile import ZipFile


def pull(host: str, output: Path) -> bool:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", host):
        raise ValueError("Use a host alias from your SSH config.")
    if output.suffix.lower() != ".zip":
        raise ValueError("Choose a .zip destination.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=output.parent, prefix=".relay-vault-", delete=False) as temp:
        path = Path(temp.name)
    try:
        with path.open("wb") as stream:
            subprocess.run(["ssh", "-T", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                            "-o", "ClearAllForwardings=yes", "-o", "ConnectTimeout=10",
                            host, "relay-vault-export"], stdin=subprocess.DEVNULL, stdout=stream,
                           check=True, timeout=120)
        with ZipFile(path) as archive:
            if not {"Inbox/", "Handoffs/"}.issubset(archive.namelist()):
                raise ValueError("Downloaded archive is missing Relay vault folders.")
            if sum(entry.file_size for entry in archive.infolist()) > 128 * 1024 * 1024:
                raise ValueError("Downloaded vault exceeds the size limit.")
            if archive.testzip() is not None:
                raise ValueError("Archive integrity check failed.")
        if output.exists():
            with output.open("rb") as old, path.open("rb") as new:
                if file_digest(old, "sha256").digest() == file_digest(new, "sha256").digest():
                    return False
        os.replace(path, output)
        return True
    finally:
        path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description='Download a current vault ZIP through an approved SSH host alias (stdlib only).')
    parser.add_argument("host", help="SSH host alias configured with the export-only key")
    parser.add_argument("output", type=Path, help="Local ZIP to refresh")
    parser.add_argument("--watch", type=int, metavar="SECONDS", help="Repeat while running")
    args = parser.parse_args()
    if args.watch is not None and args.watch < 10:
        parser.error("--watch must be at least 10 seconds")
    while True:
        try:
            if pull(args.host, args.output):
                print(f"Updated {args.output}", flush=True)
        except Exception as error:
            print(f"Vault download failed: {error}", file=sys.stderr, flush=True)
            if args.watch is None:
                return 1
        if args.watch is None:
            return 0
        time.sleep(args.watch)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
