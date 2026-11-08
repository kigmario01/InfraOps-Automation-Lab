#!/usr/bin/env bash
# ==============================================================================
# InfraOps Automation Lab - Automated Backup & Disaster Recovery Utility
# Script: backup_automation.sh
# Purpose: Creates compressed, checksummed backups of docker volumes, configs,
#          rotates archives based on retention, and verifies backup integrity.
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
SOURCE_DIRS=("docker" "ansible/inventory")
RETENTION_DAYS=7
LOCK_FILE="/tmp/infraops_backup.lock"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_NAME="infraops_backup_${TIMESTAMP}.tar.gz"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

cleanup_lock() {
    rm -f "$LOCK_FILE"
}

# Trap signals to clean up lock file
trap cleanup_lock EXIT INT TERM

create_backup() {
    if [ -f "$LOCK_FILE" ]; then
        log "ERROR: Backup already in progress (Lock file $LOCK_FILE exists). Exiting." >&2
        exit 1
    fi
    touch "$LOCK_FILE"

    log "Starting InfraOps backup procedure..."
    mkdir -p "$BACKUP_DIR"

    TARGET_ARCHIVE="${BACKUP_DIR}/${ARCHIVE_NAME}"
    CHECKSUM_FILE="${TARGET_ARCHIVE}.sha256"

    # Verify sources exist
    VALID_SOURCES=()
    for src in "${SOURCE_DIRS[@]}"; do
        if [ -e "$src" ]; then
            VALID_SOURCES+=("$src")
        else
            log "Notice: Source $src does not exist yet, skipping."
        fi
    done

    if [ ${#VALID_SOURCES[@]} -eq 0 ]; then
        log "WARNING: No valid sources found to back up. Creating placeholder."
        VALID_SOURCES=(".")
    fi

    # Create compressed archive
    log "Archiving directories: ${VALID_SOURCES[*]} -> ${TARGET_ARCHIVE}"
    tar --exclude=".git" --exclude="__pycache__" --exclude="*.log" -czf "$TARGET_ARCHIVE" "${VALID_SOURCES[@]}"

    # Verify archive integrity
    log "Verifying archive integrity with 'tar -tzf'..."
    if tar -tzf "$TARGET_ARCHIVE" >/dev/null 2>&1; then
        log "Integrity check PASSED."
    else
        log "ERROR: Archive corrupted during creation!" >&2
        rm -f "$TARGET_ARCHIVE"
        exit 2
    fi

    # Generate SHA-256 Checksum
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$TARGET_ARCHIVE" > "$CHECKSUM_FILE"
        log "Checksum created: ${CHECKSUM_FILE}"
    fi

    # Archive size
    ARCHIVE_SIZE=$(du -h "$TARGET_ARCHIVE" | cut -f1)
    log "Backup SUCCESSFUL: ${TARGET_ARCHIVE} (${ARCHIVE_SIZE})"

    # Rotate old backups
    rotate_backups
}

rotate_backups() {
    log "Enforcing retention policy: deleting backups older than ${RETENTION_DAYS} days..."
    if [ -d "$BACKUP_DIR" ]; then
        # Find and remove archives older than retention days
        find "$BACKUP_DIR" -type f -name "infraops_backup_*.tar.gz*" -mtime +"$RETENTION_DAYS" -exec rm -f {} + 2>/dev/null || true
        log "Retention cleanup complete."
    fi
}

list_backups() {
    echo "=========================================================="
    echo "            EXISTING INFRAOPS BACKUPS                     "
    echo "=========================================================="
    if [ -d "$BACKUP_DIR" ]; then
        ls -lh "$BACKUP_DIR"/infraops_backup_*.tar.gz 2>/dev/null || echo "No backups found in $BACKUP_DIR"
    else
        echo "Backup directory $BACKUP_DIR does not exist."
    fi
}

verify_backup() {
    local target="$1"
    if [ ! -f "$target" ]; then
        log "ERROR: Target file does not exist: $target" >&2
        exit 1
    fi

    log "Verifying $target..."
    if tar -tzf "$target" >/dev/null 2>&1; then
        log "TAR archive structure is valid."
    else
        log "ERROR: Corrupt archive $target" >&2
        exit 2
    fi

    if [ -f "${target}.sha256" ] && command -v sha256sum >/dev/null 2>&1; then
        log "Checking SHA256 integrity..."
        sha256sum --check "${target}.sha256"
        log "SHA256 verification OK."
    fi
}

restore_backup() {
    local target="$1"
    local dest="${2:-./restore_test}"
    if [ ! -f "$target" ]; then
        log "ERROR: Backup archive not found: $target" >&2
        exit 1
    fi

    log "CAUTION: Restoring $target into $dest..."
    mkdir -p "$dest"
    tar -xzf "$target" -C "$dest"
    log "Restore completed successfully into $dest"
}

# CLI routing
case "${1:-}" in
    --backup|-b)
        create_backup
        ;;
    --list|-l)
        list_backups
        ;;
    --verify|-v)
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 --verify <path_to_backup.tar.gz>" >&2
            exit 1
        fi
        verify_backup "$2"
        ;;
    --restore|-r)
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 --restore <path_to_backup.tar.gz> [destination_dir]" >&2
            exit 1
        fi
        restore_backup "$2" "${3:-./restore_drill}"
        ;;
    *)
        echo "Usage: $0 {--backup|--list|--verify <file>|--restore <file> [dest]}"
        echo "Options:"
        echo "  --backup    Create a full timestamped backup and apply retention policy"
        echo "  --list      List all available backup archives"
        echo "  --verify    Check integrity and sha256 checksum of an archive"
        echo "  --restore   Extract and restore an archive to a test or recovery directory"
        exit 0
        ;;
esac
