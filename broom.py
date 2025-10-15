import os
import sys
import tempfile
from pathlib import Path


def candidate_paths():
    """
    Build a list of OS-appropriate folders that commonly contain
    temporary files, caches, and crash reports.
    """
    home = Path.home()
    paths = [tempfile.gettempdir()]

    if sys.platform == "darwin":  # macOS
        paths += [
            "/tmp",
            str(home / ".cache"),
            str(home / "Library" / "Caches"),
            str(home / "Library" / "Logs"),
            str(home / "Library" / "Logs" / "DiagnosticReports"),
            "/Library/Logs",
            "/Library/Logs/DiagnosticReports",
        ]
    elif os.name == "nt":  # Windows
        paths += [
            str(home / "AppData" / "Local" / "Temp"),
            str(home / "AppData" / "Local" / "CrashDumps"),
        ]
    else:  # Linux/Unix
        paths += [
            "/tmp",
            str(home / ".cache"),
            "/var/log",
        ]

    # De-duplicate while preserving order
    seen = set()
    deduped = []
    for p in paths:
        if p and p not in seen:
            seen.add(p)
            deduped.append(p)
    return deduped


# Include common extensions across platforms
PATTERNS = (".tmp", ".temp", ".dmp", ".crash", ".ips", ".log", ".bak")


def find_temp_and_crash_files(max_files=10000):
    """
    Recursively search candidate paths for files ending with PATTERNS.
    Returns a list of absolute file paths. Stops early if max_files reached.
    """
    found = []
    for base in candidate_paths():
        if not os.path.isdir(base):
            continue

        try:
            for root, _, files in os.walk(base):
                for fname in files:
                    if fname.lower().endswith(PATTERNS):
                        full_path = os.path.join(root, fname)
                        found.append(full_path)
                        if len(found) >= max_files:
                            return found
        except (PermissionError, FileNotFoundError):
            # Skip paths we can't read or that vanish during traversal
            continue

    return found


def delete_files(file_list , dry_run=False):
    """
    Delete files form file list .
    if dry_run = True , only delete files would be deleted.
    """
    deleted = 0
    failed = 0
    for fpath in file_list :
        try:
            if dry_run:
                print("[Dry Run]", fpath)
            else:
                os.remove(fpath)
                deleted += 1
        except PermissionError:
            print("[Permission Error]", fpath)
            failed += 1
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"[SKIP - {e}", fpath)
            failed += 1
    if dry_run:
        print(f"\nDry run complete. {len(file_list)} files would be deleted.")
    else:
        print(f"\nDeleted {deleted} files. {failed} skipped due to errors.")




if __name__ == "__main__":
    results = find_temp_and_crash_files()
    print(f"\nFound {len(results)} matching files.")

    # Preview what would be deleted
    delete_files(results, dry_run=True)

    # When you're ready to actually delete, set dry_run=False
    # delete_files(results, dry_run=False)

