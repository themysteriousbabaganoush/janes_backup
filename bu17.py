#!/usr/bin/env python3
"""
backup - Timestamped backup utility with optional direct copy mode.

Version: 17.0
"""

import sys
import shutil
import os
from datetime import datetime
import hashlib

VERSION = "17.0"

MANPAGE = r"""
.TH BACKUP 1 "February 2025" "backup 17.0" "User Commands"
.SH NAME
backup \- Backup utility with timestamped backups and verified copy mode
.SH SYNOPSIS
backup [options] <file|folder>
backup cp [options] <file|folder> <destination>
.SH DESCRIPTION
Default mode creates timestamped backups in a Backups/ directory.
Copy mode performs direct copies with optional SHA256 verification, safe conflict handling, and copy logging.
"""

# ---------------- HELP / VERSION ---------------- #

def show_help():
    print(f"""backup - File & Folder Utility (v{VERSION})

USAGE:
  backup <file>
      Create a timestamped backup.

  backup -r <folder>
      Backup a folder recursively.

  backup -v <file|folder>
      Verify backup integrity using SHA256.

COPY MODE (transport):
  backup cp <file> <destination_dir>
  backup cp -v <file> <destination_dir>
  backup cp -r <folder> <destination_dir>
  backup cp -r -v <folder> <destination_dir>

COPY MODE CONFLICTS:
  - If destination directory doesn't exist, you will be asked to create it.
  - If a file exists, you can:
      [o] overwrite, [k] keep both (timestamp), [s] skip
    and optionally apply the choice to all remaining conflicts.
  - If a folder exists (folder copy), you can:
      [m] merge, [o] overwrite, [a] abort

COPY MODE LOGGING:
  - Copy operations are logged to:
      <destination_dir>/.backup_cp_logs/YYYY-MM-DD.log
  - If -v is used, hashes and verification results are included.

OPTIONS:
  -r, --recursive     Recursive operation
  -v, --verify        SHA256 verification
  -d, --destination   Override BACKUP destination (backup mode only)
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

# ---------------- HASHING ---------------- #

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
    return hasher.hexdigest()


def compute_sha256_folder(root):
    hashes = {}
    for dirpath, _, files in os.walk(root):
        for f in files:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root)
            hashes[rel] = compute_sha256(full)
    return hashes

# ---------------- BACKUP MODE ---------------- #

def ensure_dirs(base_dir, dest_override=None):
    if dest_override:
        backup_dir = os.path.join(os.path.abspath(dest_override), "Backups")
    else:
        backup_dir = os.path.join(base_dir, "Backups")

    log_dir = os.path.join(backup_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return backup_dir, log_dir


def log_transaction(log_dir, original, target, sha_o, sha_t, result):
    log_name = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(log_dir, log_name)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"Backup version: {VERSION}\n")
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
        f.write(f"Original: {original}\n")
        f.write(f"Target:   {target}\n")
        f.write(f"SHA256 original: {sha_o}\n")
        f.write(f"SHA256 target:   {sha_t}\n")
        f.write(f"Result: {result}\n")
        f.write("-" * 50 + "\n")


def create_backup(source, verify=False, dest_override=None):
    if not os.path.isfile(source):
        print("Error: source is not a file.")
        sys.exit(1)

    base = os.path.dirname(os.path.abspath(source))
    backup_dir, log_dir = ensure_dirs(base, dest_override)

    name, ext = os.path.splitext(os.path.basename(source))
    ts = datetime.now().strftime("%m%d%Y-%H-%M-%S")
    target = os.path.join(backup_dir, f"{name}-{ts}{ext}")

    shutil.copy2(source, target)
    print(f"Backup created: {target}")

    sha_o = sha_t = "SKIPPED"
    result = "NOT VERIFIED"

    if verify:
        sha_o = compute_sha256(source)
        sha_t = compute_sha256(target)

        if sha_o == sha_t:
            print("Backup VERIFIED.")
            result = "MATCH"
        else:
            print("Backup FAILED.")
            result = "FAILED"

    log_transaction(log_dir, source, target, sha_o, sha_t, result)


def create_backup_folder(source, verify=False, dest_override=None):
    if not os.path.isdir(source):
        print("Error: source is not a folder.")
        sys.exit(1)

    parent = os.path.dirname(os.path.abspath(source))
    backup_dir, log_dir = ensure_dirs(parent, dest_override)

    ts = datetime.now().strftime("%m%d%Y-%H-%M-%S")
    target = os.path.join(backup_dir, os.path.basename(source) + "-" + ts)

    shutil.copytree(source, target)
    print(f"Folder backup created: {target}")

    sha_o = sha_t = "SKIPPED"
    result = "NOT VERIFIED"

    if verify:
        sha_o = compute_sha256_folder(source)
        sha_t = compute_sha256_folder(target)

        if sha_o == sha_t:
            print("Backup VERIFIED.")
            result = "MATCH"
        else:
            print("Backup FAILED.")
            result = "FAILED"

    log_transaction(log_dir, source, target, sha_o, sha_t, result)

# ---------------- COPY MODE LOGGING ---------------- #

def ensure_cp_log_dir(dest_dir):
    log_dir = os.path.join(dest_dir, ".backup_cp_logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def log_copy_event(cp_log_dir, source, target, action, result,
                   sha_src=None, sha_dst=None, note=None):
    log_name = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(cp_log_dir, log_name)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"Backup version: {VERSION}\n")
        f.write("Mode: COPY\n")
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
        f.write(f"Source: {source}\n")
        f.write(f"Target: {target}\n")
        f.write(f"Action: {action}\n")
        if sha_src is not None:
            f.write(f"SHA256 source: {sha_src}\n")
        if sha_dst is not None:
            f.write(f"SHA256 target: {sha_dst}\n")
        if note:
            f.write(f"Note: {note}\n")
        f.write(f"Result: {result}\n")
        f.write("-" * 50 + "\n")


def log_copy_summary(cp_log_dir, source, destination_dir, recursive, verify, counts, result):
    log_name = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(cp_log_dir, log_name)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"Backup version: {VERSION}\n")
        f.write("Mode: COPY-SUMMARY\n")
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
        f.write(f"Source: {source}\n")
        f.write(f"Destination base: {destination_dir}\n")
        f.write(f"Recursive: {recursive}\n")
        f.write(f"Verify: {verify}\n")
        f.write(f"Counts: copied={counts['copied']}, overwritten={counts['overwritten']}, "
                f"kept_both={counts['kept_both']}, skipped={counts['skipped']}, merged_files={counts['merged_files']}\n")
        f.write(f"Result: {result}\n")
        f.write("=" * 50 + "\n")

# ---------------- COPY MODE HELPERS ---------------- #

def prompt_choice(prompt, valid, default=None):
    valid_set = {v.lower() for v in valid}
    while True:
        suffix = f" [{default}]" if default else ""
        ans = input(f"{prompt}{suffix}: ").strip().lower()
        if not ans and default:
            ans = default.lower()
        if ans in valid_set:
            return ans
        print(f"Please enter one of: {', '.join(valid)}")


def ensure_destination_dir(dest_dir):
    dest_dir = os.path.abspath(dest_dir)

    if os.path.exists(dest_dir):
        if not os.path.isdir(dest_dir):
            print(f"Error: destination exists but is not a directory: {dest_dir}")
            sys.exit(1)
        return dest_dir

    print(f"Destination does not exist: {dest_dir}")
    choice = prompt_choice("Create it? (y/n)", ["y", "n"], default="y")
    if choice == "y":
        try:
            os.makedirs(dest_dir, exist_ok=True)
            print(f"Created directory: {dest_dir}")
            return dest_dir
        except Exception as e:
            print(f"Failed to create destination: {e}")
            sys.exit(1)

    print("Copy aborted.")
    sys.exit(1)


def timestamped_name(existing_dest_path):
    base = os.path.basename(existing_dest_path)
    name, ext = os.path.splitext(base)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{name}-{ts}{ext}"


def resolve_file_conflict(dest_path, conflict_policy):
    """
    Returns (action, final_dest_path, new_policy, action_label)

    action: 'overwrite' | 'keep' | 'skip'
    action_label: human label for logging ("copied", "overwritten", "kept_both", "skipped")
    """
    if not os.path.exists(dest_path):
        return "overwrite", dest_path, conflict_policy, "copied"

    # If policy already chosen en-masse, apply it
    if conflict_policy in ("overwrite", "keep", "skip"):
        if conflict_policy == "keep":
            new_path = os.path.join(os.path.dirname(dest_path), timestamped_name(dest_path))
            return "keep", new_path, conflict_policy, "kept_both"
        if conflict_policy == "skip":
            return "skip", dest_path, conflict_policy, "skipped"
        return "overwrite", dest_path, conflict_policy, "overwritten"

    print(f"\nFile exists: {dest_path}")
    choice = prompt_choice(
        "Choose action: [o] overwrite, [k] keep both (timestamp), [s] skip",
        ["o", "k", "s"]
    )
    action = {"o": "overwrite", "k": "keep", "s": "skip"}[choice]

    apply_all = prompt_choice("Apply this choice to ALL remaining file conflicts? (y/n)", ["y", "n"], default="y")
    new_policy = action if apply_all == "y" else None

    if action == "keep":
        new_path = os.path.join(os.path.dirname(dest_path), timestamped_name(dest_path))
        return action, new_path, new_policy, "kept_both"
    if action == "skip":
        return action, dest_path, new_policy, "skipped"

    return action, dest_path, new_policy, "overwritten"

# ---------------- COPY MODE ---------------- #

def verify_pair_and_report(src, dst, cp_log_dir, action_label, counts):
    sha_src = compute_sha256(src)
    sha_dst = compute_sha256(dst)
    if sha_src == sha_dst:
        log_copy_event(cp_log_dir, src, dst, action_label, "MATCH", sha_src=sha_src, sha_dst=sha_dst)
        return True
    log_copy_event(cp_log_dir, src, dst, action_label, "FAILED", sha_src=sha_src, sha_dst=sha_dst)
    return False


def copy_file(source, dest_dir, verify=False, conflict_policy=None, cp_log_dir=None, counts=None):
    if not os.path.isfile(source):
        print(f"Error: source is not a file: {source}")
        sys.exit(1)

    dest_path = os.path.join(dest_dir, os.path.basename(source))

    action, final_path, conflict_policy, action_label = resolve_file_conflict(dest_path, conflict_policy)
    if action == "skip":
        print(f"Skipped: {dest_path}")
        counts["skipped"] += 1
        log_copy_event(cp_log_dir, source, dest_path, action_label, "SKIPPED")
        return conflict_policy

    try:
        shutil.copy2(source, final_path)
    except Exception as e:
        log_copy_event(cp_log_dir, source, final_path, action_label, "FAILED", note=str(e))
        print(f"Copy failed: {e}")
        sys.exit(1)

    if action_label == "overwritten":
        counts["overwritten"] += 1
    elif action_label == "kept_both":
        counts["kept_both"] += 1
    else:
        counts["copied"] += 1

    if verify:
        ok = verify_pair_and_report(source, final_path, cp_log_dir, action_label, counts)
        if not ok:
            print("Copy FAILED.")
            sys.exit(2)

    # If not verifying, still log the event
    if not verify:
        log_copy_event(cp_log_dir, source, final_path, action_label, "COPIED")

    print(f"Copied: {final_path}")
    return conflict_policy


def merge_folder(source_dir, dest_dir, verify=False, conflict_policy=None, cp_log_dir=None, counts=None):
    """
    Merge contents of source_dir into dest_dir.
    - Creates missing directories
    - File conflicts handled via resolve_file_conflict
    """
    for dirpath, dirnames, filenames in os.walk(source_dir):
        rel = os.path.relpath(dirpath, source_dir)
        target_dir = dest_dir if rel == "." else os.path.join(dest_dir, rel)
        os.makedirs(target_dir, exist_ok=True)

        # Ensure subdirs exist (merge semantics)
        for d in dirnames:
            os.makedirs(os.path.join(target_dir, d), exist_ok=True)

        for fn in filenames:
            src_file = os.path.join(dirpath, fn)
            dst_file = os.path.join(target_dir, fn)

            action, final_path, conflict_policy, action_label = resolve_file_conflict(dst_file, conflict_policy)
            if action == "skip":
                print(f"Skipped: {dst_file}")
                counts["skipped"] += 1
                log_copy_event(cp_log_dir, src_file, dst_file, action_label, "SKIPPED", note="merge")
                continue

            try:
                shutil.copy2(src_file, final_path)
            except Exception as e:
                log_copy_event(cp_log_dir, src_file, final_path, action_label, "FAILED", note=f"merge: {e}")
                print(f"Copy failed: {e}")
                sys.exit(1)

            counts["merged_files"] += 1
            if action_label == "overwritten":
                counts["overwritten"] += 1
            elif action_label == "kept_both":
                counts["kept_both"] += 1
            else:
                counts["copied"] += 1

            if verify:
                ok = verify_pair_and_report(src_file, final_path, cp_log_dir, f"{action_label} (merge)", counts)
                if not ok:
                    print("Copy FAILED.")
                    sys.exit(2)
            else:
                log_copy_event(cp_log_dir, src_file, final_path, f"{action_label} (merge)", "COPIED")

            print(f"Copied: {final_path}")

    return conflict_policy


def copy_folder(source, dest_dir, verify=False, conflict_policy=None, cp_log_dir=None, counts=None):
    if not os.path.isdir(source):
        print(f"Error: source is not a folder: {source}")
        sys.exit(1)

    target = os.path.join(dest_dir, os.path.basename(os.path.abspath(source)))

    if os.path.exists(target):
        if not os.path.isdir(target):
            print(f"Error: destination path exists but is not a folder: {target}")
            sys.exit(1)

        print(f"\nFolder exists: {target}")
        mode = prompt_choice("Choose action: [m] merge, [o] overwrite, [a] abort", ["m", "o", "a"], default="m")

        if mode == "a":
            log_copy_event(cp_log_dir, source, target, "folder_exists", "ABORTED")
            print("Copy aborted.")
            sys.exit(1)

        if mode == "o":
            try:
                shutil.rmtree(target)
            except Exception as e:
                log_copy_event(cp_log_dir, source, target, "overwrite_folder", "FAILED", note=str(e))
                print(f"Failed to remove existing folder: {e}")
                sys.exit(1)

            try:
                shutil.copytree(source, target)
            except Exception as e:
                log_copy_event(cp_log_dir, source, target, "overwrite_folder", "FAILED", note=str(e))
                print(f"Folder copy failed: {e}")
                sys.exit(1)

            # Folder-level verify (full tree)
            if verify:
                sha_o = compute_sha256_folder(source)
                sha_t = compute_sha256_folder(target)
                if sha_o == sha_t:
                    log_copy_event(cp_log_dir, source, target, "overwrite_folder", "MATCH", note="folder verify")
                else:
                    log_copy_event(cp_log_dir, source, target, "overwrite_folder", "FAILED", note="folder verify")
                    print("Copy FAILED.")
                    sys.exit(2)

            if not verify:
                log_copy_event(cp_log_dir, source, target, "overwrite_folder", "COPIED")

            print(f"Copied folder: {target}")
            return conflict_policy

        # mode == "m" merge
        log_copy_event(cp_log_dir, source, target, "merge_folder", "STARTED")
        conflict_policy = merge_folder(source, target, verify, conflict_policy, cp_log_dir, counts)
        log_copy_event(cp_log_dir, source, target, "merge_folder", "COMPLETED")
        print(f"Merged folder into: {target}")
        return conflict_policy

    # No existing target: normal copytree
    try:
        shutil.copytree(source, target)
    except Exception as e:
        log_copy_event(cp_log_dir, source, target, "copy_folder", "FAILED", note=str(e))
        print(f"Folder copy failed: {e}")
        sys.exit(1)

    # Folder-level verify (full tree) for copytree path
    if verify:
        sha_o = compute_sha256_folder(source)
        sha_t = compute_sha256_folder(target)
        if sha_o == sha_t:
            log_copy_event(cp_log_dir, source, target, "copy_folder", "MATCH", note="folder verify")
        else:
            log_copy_event(cp_log_dir, source, target, "copy_folder", "FAILED", note="folder verify")
            print("Copy FAILED.")
            sys.exit(2)
    else:
        log_copy_event(cp_log_dir, source, target, "copy_folder", "COPIED")

    print(f"Copied folder: {target}")
    return conflict_policy

# ---------------- MAIN ---------------- #

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

    mode = "backup"
    if args[0] in ("cp", "copy"):
        mode = "copy"
        args = args[1:]

    verify = False
    recursive = False
    source = None
    destination = None
    backup_dest_override = None

    # Parse flags and positional args
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-v", "--verify"):
            verify = True
        elif a in ("-r", "--recursive"):
            recursive = True
        elif a in ("-d", "--destination"):
            # destination override for BACKUP MODE only
            try:
                backup_dest_override = args[i + 1]
                i += 1
            except IndexError:
                print("Error: -d/--destination requires a folder path.")
                sys.exit(1)
        elif not source:
            source = a
        elif not destination:
            destination = a
        else:
            print(f"Unexpected argument: {a}")
            sys.exit(1)
        i += 1

    if not source:
        print("Error: no source specified.")
        sys.exit(1)

    if mode == "copy":
        if not destination:
            print("Error: copy mode requires a destination.")
            sys.exit(1)

        destination = ensure_destination_dir(destination)
        cp_log_dir = ensure_cp_log_dir(destination)

        counts = {"copied": 0, "overwritten": 0, "kept_both": 0, "skipped": 0, "merged_files": 0}
        log_copy_event(cp_log_dir, source, destination, "copy_mode", "STARTED",
                       note=f"recursive={recursive}, verify={verify}")

        conflict_policy = None  # en-masse file conflict choice (overwrite/keep/skip)

        if recursive:
            conflict_policy = copy_folder(source, destination, verify, conflict_policy, cp_log_dir, counts)
        else:
            conflict_policy = copy_file(source, destination, verify, conflict_policy, cp_log_dir, counts)

        # If verify was requested and we got here, verification succeeded (we exit immediately on failure).
        if verify:
            print("Copy VERIFIED.")

        log_copy_summary(cp_log_dir, source, destination, recursive, verify, counts, "SUCCESS")
        sys.exit(0)

    # BACKUP MODE
    if recursive:
        create_backup_folder(source, verify, backup_dest_override)
    else:
        create_backup(source, verify, backup_dest_override)


if __name__ == "__main__":
    main()
