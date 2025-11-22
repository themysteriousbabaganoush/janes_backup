#!/usr/bin/env python3
"""
backup - Timestamped backup utility that stores backups beside the original.

Version: 8.0
"""

import sys
import shutil
import os
from datetime import datetime
import hashlib

VERSION = "8.0"

MANPAGE = r"""
.TH BACKUP 1 "February 2025" "backup 8.0" "User Commands"
.SH NAME
backup \- Timestamped file backup utility with local directory storage and daily logs
.SH DESCRIPTION
This version stores the Backups/ folder in the SAME DIRECTORY as the original file or folder.
"""

def show_help():
    print(f"""backup - File & Folder Backup Utility (v{VERSION})

Usage:
  backup <file>
      Backup a single file.

  backup -p <file>
      Backup a file with SHA256 proof check.

  backup -r <folder>
      Backup a folder recursively.

  backup -r -p <folder>
      Backup a folder AND verify all file hashes.

Options:
  --help
  --version
  --install-man
""")


def show_version():
    print(f"backup version {VERSION}")


def install_manpage(path="/usr/local/share/man/man1/backup.1"):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(MANPAGE.strip() + "\n")
        print("Man page installed.")
    except Exception as e:
        print(f"Error installing man page: {e}")
        sys.exit(1)


def ensure_dirs(base_dir):
    backup_dir = os.path.join(base_dir, "Backups")
    log_dir = os.path.join(backup_dir, "logs")

    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    return backup_dir, log_dir


def log_transaction(log_dir, original, backup_path, orig_hash, backup_hash, result):
    log_name = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(log_dir, log_name)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
        f.write(f"Original: {original}\n")
        f.write(f"Backup:   {backup_path}\n")
        f.write(f"SHA256 original: {orig_hash}\n")
        f.write(f"SHA256 backup:   {backup_hash}\n")
        f.write(f"Result: {result}\n")
        f.write("-" * 50 + "\n")


def compute_sha256(path):
    hasher = hashlib.sha256()
    total = os.path.getsize(path)
    read_bytes = 0
    spinner = "|/-\\"
    s = 0

    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
            read_bytes += len(chunk)
            percent = (read_bytes / total * 100) if total else 100
            sys.stdout.write(f"\rHashing {path} [{spinner[s % 4]}] {percent:6.2f}%")
            sys.stdout.flush()
            s += 1

    sys.stdout.write("\n")
    sys.stdout.flush()
    return hasher.hexdigest()


def compute_sha256_folder(root):
    hashes = {}
    for dirpath, _, files in os.walk(root):
        for f in files:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root)
            hashes[rel] = compute_sha256(full)
    return hashes


def create_backup(source, proof=False):
    if not os.path.isfile(source):
        print(f"Error: '{source}' does not exist or is not a file.")
        sys.exit(1)

    original_dir = os.path.dirname(os.path.abspath(source))
    backup_dir, log_dir = ensure_dirs(original_dir)

    filename = os.path.basename(source)
    name, ext = os.path.splitext(filename)

    timestamp = datetime.now().strftime("%m%d%Y-%H-%M-%S")
    backup_name = f"{name}-{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_name)

    try:
        shutil.copy2(source, backup_path)
        print(f"Backup created: {backup_path}")
    except Exception as e:
        print(f"Error copying file: {e}")
        sys.exit(1)

    sha_orig = "SKIPPED"
    sha_copy = "SKIPPED"
    result = "NOT VERIFIED"

    if proof:
        print("Running SHA256 proof verification...")
        sha_orig = compute_sha256(source)
        sha_copy = compute_sha256(backup_path)

        if sha_orig == sha_copy:
            print("SHA256 match: BACKUP VERIFIED.")
            result = "MATCH"
        else:
            print("SHA256 mismatch: BACKUP FAILED.")
            result = "FAILED"

    log_transaction(log_dir, source, backup_path, sha_orig, sha_copy, result)


def create_backup_folder(source, proof=False):
    if not os.path.isdir(source):
        print(f"Error: '{source}' is not a folder.")
        sys.exit(1)

    original_dir = os.path.abspath(source)
    parent_dir = os.path.dirname(original_dir)
    folder_name = os.path.basename(original_dir)

    backup_dir, log_dir = ensure_dirs(parent_dir)

    timestamp = datetime.now().strftime("%m%d%Y-%H-%M-%S")
    backup_name = f"{folder_name}-{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)

    try:
        shutil.copytree(original_dir, backup_path)
        print(f"Folder backup created: {backup_path}")
    except Exception as e:
        print(f"Error copying folder: {e}")
        sys.exit(1)

    sha_orig = "SKIPPED"
    sha_copy = "SKIPPED"
    result = "NOT VERIFIED"

    if proof:
        print("Running recursive SHA256 proof verification...")

        sha_orig = compute_sha256_folder(original_dir)
        sha_copy = compute_sha256_folder(backup_path)

        if sha_orig == sha_copy:
            print("SHA256 match: FOLDER VERIFIED.")
            result = "MATCH"
        else:
            print("SHA256 mismatch: FOLDER BACKUP FAILED.")
            result = "FAILED"

    log_transaction(log_dir, source, backup_path, sha_orig, sha_copy, result)


def main():
    args = sys.argv[1:]

    if not args:
        show_help()
        sys.exit(1)

    if args[0] in ("--help", "-h"):
        show_help()
        sys.exit(0)

    if args[0] == "--version":
        show_version()
        sys.exit(0)

    if args[0] == "--install-man":
        install_manpage()
        sys.exit(0)

    proof = False
    recursive = False
    source = None

    # Parse flags and find the one non-flag argument as source
    for a in args:
        if a in ("-p", "--proof"):
            proof = True
        elif a in ("-r", "--recursive"):
            recursive = True
        elif a.startswith("-"):
            print(f"Unknown option: {a}")
            sys.exit(1)
        else:
            source = a

    if not source:
        print("Error: No file or folder specified.")
        sys.exit(1)

    if recursive:
        create_backup_folder(source, proof)
    else:
        create_backup(source, proof)


if __name__ == "__main__":
    main()
