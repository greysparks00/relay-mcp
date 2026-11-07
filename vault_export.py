"""Export Relay's Markdown vault to stdout for a restricted OpenSSH key."""

import os
import stat
import sys
from tempfile import TemporaryFile
from shutil import copyfileobj
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from tools._vault import VAULT_FOLDERS, require_local, vault


MAX_BYTES = 128 * 1024 * 1024
MAX_NOTES = 10000


def export(destination):
    # Finish the complete ZIP before sending bytes to the client. A failed read
    # must never look like a successful partial export.
    with TemporaryFile() as snapshot:
        with vault() as root, ZipFile(snapshot, "w") as archive:
            files = []
            for folder in VAULT_FOLDERS:
                directory = root / folder
                require_local(directory)
                archive.writestr(ZipInfo(folder + "/"), b"")
                for path in directory.iterdir():
                    if path.suffix.casefold() == ".md" and not path.name.startswith("."):
                        files.append(path)
                        if len(files) > MAX_NOTES:
                            raise ValueError("Too many vault notes.")
            if (root / "Home.md").exists():
                files.append(root / "Home.md")
            total = 0
            names = set()
            for path in sorted(files):
                require_local(path.parent)
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or path.is_junction() or path.is_symlink():
                    continue
                name = path.relative_to(root).as_posix()
                if "\\" in name or ":" in name or name.casefold() in names:
                    raise ValueError("Vault contains conflicting or nonportable note names.")
                names.add(name.casefold())
                if total + info.st_size > MAX_BYTES:
                    raise ValueError("Vault exceeds the export size limit.")
                with path.open("rb") as source:
                    opened = os.fstat(source.fileno())
                    require_local(path)
                    if not os.path.samestat(info, opened) or opened.st_nlink != 1:
                        raise ValueError("Vault changed during export. Retry.")
                    entry = ZipInfo(name)  # Stable metadata makes unchanged pulls identical.
                    entry.compress_type = ZIP_DEFLATED
                    remaining = info.st_size
                    with archive.open(entry, "w") as member:
                        while remaining:
                            chunk = source.read(min(65536, remaining))
                            if not chunk:
                                raise ValueError("Note changed during export. Retry.")
                            member.write(chunk)
                            remaining -= len(chunk)
                    if source.read(1) or os.fstat(source.fileno()).st_mtime_ns != info.st_mtime_ns:
                        raise ValueError("Note changed during export. Retry.")
                total += info.st_size
        snapshot.seek(0)
        copyfileobj(snapshot, destination)


if __name__ == "__main__":
    # OpenSSH supplies this variable when an authorized_keys forced command runs.
    # Never evaluate its contents or let the caller select a path.
    if os.environ.get("SSH_ORIGINAL_COMMAND", "relay-vault-export") != "relay-vault-export":
        sys.exit("This key only permits relay-vault-export.")
    export(sys.stdout.buffer)
