# janes_backup
Quick file/folder backup &amp; verify program

backup - Instructions.txt
============================

backup — A timestamped, local-backup utility that stores backups *right next to* the original file or folder. Fast, reliable, tamper-evident, and perfect for daily protection.

------------------------------------------------------------
🗂 Overview
------------------------------------------------------------
This tool creates:

• Timestamped backups stored in a local `Backups/` folder  
• Automatic daily log files  
• SHA256 proof-verification (optional)  
• File OR folder backups  
• Recursive hashing for full-folder integrity checks  

Every backup is cleanly timestamped:
    MMDDYYYY-HH-MM-SS

And every action is logged in:
    Backups/logs/YYYY-MM-DD.log

------------------------------------------------------------
🚀 Basic Commands
------------------------------------------------------------

Backup a single file:
    backup myfile.txt

Backup a file *with SHA256 verification*:
    backup -p myfile.txt
    backup --proof myfile.txt

Backup a full folder recursively:
    backup -r myfolder/

Backup a folder *with full SHA256 checks*:
    backup -r -p myfolder/
    backup --recursive --proof myfolder/

Show help or version:
    backup --help
    backup --version

Install manpage (Linux):
    backup --install-man

------------------------------------------------------------
🎯 What It Does
------------------------------------------------------------

✔ File Backups  
Creates a timestamped copy of your file in:
    <same directory>/Backups/<name>-<timestamp>.ext

✔ Folder Backups  
Copies an entire folder into:
    <parent directory>/Backups/<folder>-<timestamp>/

✔ SHA256 Verification (optional: -p)  
Ensures file/folder backup integrity:

• Computes full SHA256 hash of the original  
• Computes SHA256 hash of the backup  
• Compares them  
• Logs the outcome (MATCH or FAILED)

✔ Daily Log Files  
Every time the program runs, it logs:

• Original path  
• Backup path  
• SHA256 of both  
• Verification result  
• Timestamp  

Log location:
    Backups/logs/YYYY-MM-DD.log

------------------------------------------------------------
📦 Directory Structure Example
------------------------------------------------------------

If you backup:

    /home/user/project/config.ini

The backup is stored here:

    /home/user/project/Backups/config-02122025-14-32-10.ini

And logs go here:

    /home/user/project/Backups/logs/2025-02-12.log

For folders:

    /home/user/project/

Backups are stored in:

    /home/user/Backups/project-02122025-14-33-00/

------------------------------------------------------------
🧪 Proof Verification Details
------------------------------------------------------------

File mode:
    Computes SHA256 for both original and backup files.

Folder mode:
    Computes SHA256 for *every file* inside the folder tree:
        compute_sha256_folder(<folder>)

Hashes are compared:
    MATCH  → Backup is trustworthy  
    FAILED → Something went wrong  

Results are logged automatically.

------------------------------------------------------------
⚙ Notes & Behavior
------------------------------------------------------------

• If a file/folder does not exist → backup exits with error  
• Backups NEVER overwrite each other — timestamps keep them unique  
• Log files are appended automatically  
• SHA256 hashing displays progress with a spinner  

------------------------------------------------------------
🏷 Version
------------------------------------------------------------
backup v8.0

------------------------------------------------------------
☕ Philosophy
------------------------------------------------------------

Your data deserves reliable, timestamped snapshots that don’t rely on cloud sync, daemons, or external tools.

This program exists to give you:
• Local control  
• Clean backups  
• Verifiable integrity  
• Zero nonsense  

A backup system should be simple, predictable, and trustworthy — this one is.

------------------------------------------------------------
End of Instructions
------------------------------------------------------------
