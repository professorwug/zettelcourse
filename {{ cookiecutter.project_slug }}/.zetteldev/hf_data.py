#!/usr/bin/env python3
"""
Hugging Face data synchronization for lecture processed_data folders.

This script manages versioned snapshots of lecture data on Hugging Face,
replacing Git LFS for large file storage.

Usage:
    python hf_data.py init                    - Initialize HF repo connection
    python hf_data.py status                  - Show sync status for all lectures
    python hf_data.py push <lecture>          - Push lecture to HF (versioned snapshot)
    python hf_data.py pull <path>             - Pull from HF (supports subdirs)
    python hf_data.py pull --all              - Pull all lectures
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
REPO_ROOT = Path(__file__).parent.parent
LECTURES_DIR = REPO_ROOT / "lectures"
MANIFEST_FILENAME = ".hf_manifest.json"
HF_CONFIG_FILE = REPO_ROOT / ".hf"
ENV_VAR_NAME = "HF_DATA_REPO"  # Legacy fallback


def get_hf_repo() -> str:
    """Get the HF repo ID from .hf config file (preferred) or environment (fallback)."""
    # First, check .hf config file (git-tracked)
    if HF_CONFIG_FILE.exists():
        repo = HF_CONFIG_FILE.read_text().strip()
        if repo:
            return repo

    # Fallback to environment variable
    repo = os.getenv(ENV_VAR_NAME)
    if repo:
        return repo

    print("Error: HF data repo not configured.")
    print("Run 'just hugdata init' to configure.")
    sys.exit(1)


def get_lectures() -> list[str]:
    """Get list of lecture directories that have processed_data folders."""
    lectures = []
    if not LECTURES_DIR.exists():
        return lectures

    for lec_dir in sorted(LECTURES_DIR.iterdir()):
        if lec_dir.is_dir():
            processed_data = lec_dir / "processed_data"
            if processed_data.exists() and any(processed_data.iterdir()):
                lectures.append(lec_dir.name)

    return lectures


def compute_dir_hash(directory: Path) -> str:
    """Compute a hash of directory contents for change detection."""
    hasher = hashlib.sha256()

    for file_path in sorted(directory.rglob("*")):
        if file_path.is_file() and not file_path.name.startswith("."):
            hasher.update(str(file_path.relative_to(directory)).encode())
            hasher.update(str(file_path.stat().st_size).encode())
            hasher.update(str(int(file_path.stat().st_mtime)).encode())

    return hasher.hexdigest()[:16]


def get_local_manifest(lecture: str) -> Optional[dict]:
    """Get local manifest for a lecture if it exists."""
    manifest_path = LECTURES_DIR / lecture / "processed_data" / MANIFEST_FILENAME
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return None


def save_local_manifest(lecture: str, manifest: dict) -> None:
    """Save local manifest for a lecture."""
    manifest_path = LECTURES_DIR / lecture / "processed_data" / MANIFEST_FILENAME
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def get_dir_size(directory: Path) -> int:
    """Get total size of directory in bytes (excludes dotfiles for consistency with hash)."""
    total = 0
    for file_path in directory.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith("."):
            total += file_path.stat().st_size
    return total


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# =============================================================================
# Commands
# =============================================================================


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize the HF repo connection."""
    try:
        from huggingface_hub import HfApi, login
    except ImportError:
        print("Error: huggingface_hub not installed.")
        print("Run: uv add huggingface_hub")
        sys.exit(1)

    # Check if already configured
    existing_repo = None
    if HF_CONFIG_FILE.exists():
        existing_repo = HF_CONFIG_FILE.read_text().strip()
    if not existing_repo:
        existing_repo = os.getenv(ENV_VAR_NAME)

    if existing_repo:
        print(f"Current HF repo: {existing_repo}")
        response = input("Reconfigure? [y/N]: ").strip().lower()
        if response != "y":
            print("Keeping existing configuration.")
            return

    # Login to HF
    print("\n1. Logging into Hugging Face...")
    print("   (This will open a browser or prompt for a token)")
    login()

    # Get or create repo
    print("\n2. Configure dataset repository...")
    repo_id = input("   Enter HF repo ID (e.g., 'username/systems_ml_data'): ").strip()

    if not repo_id or "/" not in repo_id:
        print("Error: Invalid repo ID. Format should be 'username/repo_name'")
        sys.exit(1)

    api = HfApi()

    # Check if repo exists, create if not
    try:
        api.repo_info(repo_id, repo_type="dataset")
        print(f"   Found existing dataset: {repo_id}")
    except Exception:
        print(f"   Creating new dataset: {repo_id}")
        try:
            api.create_repo(repo_id, repo_type="dataset", private=True)
            print(f"   Created private dataset: {repo_id}")
        except Exception as e:
            print(f"Error creating repo: {e}")
            sys.exit(1)

    # Save to .hf (git-tracked config file)
    HF_CONFIG_FILE.write_text(repo_id + "\n")

    print(f"\n3. Saved repo ID to .hf")
    print("   (This file is git-tracked so collaborators know where to find data)")
    print("\nSetup complete! You can now use:")
    print("  just hugdata status   - view sync status")
    print("  just hugdata push <lecture>   - push data")
    print("  just hugdata pull <path>      - pull data")


def cmd_status(args: argparse.Namespace) -> None:
    """Show sync status for all lectures."""
    try:
        from huggingface_hub import HfApi, list_repo_tree
    except ImportError:
        print("Error: huggingface_hub not installed. Run: uv add huggingface_hub")
        sys.exit(1)

    repo_id = get_hf_repo()
    api = HfApi()

    # Get remote lectures (top-level directories only)
    remote_lectures = set()
    try:
        for item in list_repo_tree(repo_id, repo_type="dataset"):
            # Only include top-level directories (not files like .gitattributes)
            if item.path and "/" not in item.path and not item.path.startswith("."):
                # Check if it's a directory by looking for the type attribute
                if hasattr(item, "type") and item.type == "directory":
                    remote_lectures.add(item.path)
                elif not hasattr(item, "type"):
                    # Fallback: assume directories don't have extensions
                    if "." not in item.path:
                        remote_lectures.add(item.path)
    except Exception as e:
        print(f"Warning: Could not fetch remote info: {e}")
        remote_lectures = set()

    # Get local lectures
    local_lectures = get_lectures()
    all_lectures = sorted(set(local_lectures) | remote_lectures)

    if not all_lectures:
        print("No lectures found locally or on HF.")
        return

    # Print header
    print(f"\nHF Repo: {repo_id}")
    print("=" * 70)
    print(f"{'Lecture':<40} {'Local':<10} {'Remote':<10} {'Status':<10}")
    print("-" * 70)

    for lec in all_lectures:
        local_size = "—"
        remote_size = "—"
        status = "unknown"

        # Check local
        local_path = LECTURES_DIR / lec / "processed_data"
        has_local = local_path.exists() and any(local_path.iterdir())
        if has_local:
            local_size = format_size(get_dir_size(local_path))
            local_hash = compute_dir_hash(local_path)

        # Check remote
        has_remote = lec in remote_lectures
        if has_remote:
            # Get remote manifest if exists
            try:
                from huggingface_hub import hf_hub_download
                manifest_path = hf_hub_download(
                    repo_id,
                    f"{lec}/{MANIFEST_FILENAME}",
                    repo_type="dataset",
                    local_dir=REPO_ROOT / ".hf_cache",
                    force_download=True,  # Always fetch latest to avoid stale cache
                )
                with open(manifest_path) as f:
                    remote_manifest = json.load(f)
                remote_size = format_size(remote_manifest.get("size_bytes", 0))
                remote_hash = remote_manifest.get("hash", "")
            except Exception:
                remote_size = "?"
                remote_hash = ""

        # Determine status
        if has_local and has_remote:
            local_manifest = get_local_manifest(lec)
            if local_manifest and local_manifest.get("hash") == local_hash:
                # Local matches what we last pushed
                if local_hash == remote_hash:
                    status = "synced"
                else:
                    status = "behind"
            else:
                status = "ahead"
        elif has_local:
            status = "local only"
        elif has_remote:
            status = "remote only"

        # Truncate lecture name if needed
        lec_display = lec[:38] + ".." if len(lec) > 40 else lec
        print(f"{lec_display:<40} {local_size:<10} {remote_size:<10} {status:<10}")

    print("-" * 70)


def cmd_push(args: argparse.Namespace) -> None:
    """Push a lecture's processed_data to HF."""
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("Error: huggingface_hub not installed. Run: uv add huggingface_hub")
        sys.exit(1)

    lecture = args.lecture
    repo_id = get_hf_repo()

    # Validate lecture exists
    local_path = LECTURES_DIR / lecture / "processed_data"
    if not local_path.exists():
        print(f"Error: No processed_data folder found for '{lecture}'")
        print(f"Expected: {local_path}")
        sys.exit(1)

    if not any(local_path.iterdir()):
        print(f"Error: processed_data folder is empty for '{lecture}'")
        sys.exit(1)

    # Compute hash and size
    local_hash = compute_dir_hash(local_path)
    local_size = get_dir_size(local_path)

    print(f"Pushing: {lecture}")
    print(f"  Size: {format_size(local_size)}")
    print(f"  Hash: {local_hash}")
    print(f"  To: {repo_id}/{lecture}")

    # Create manifest
    manifest = {
        "lecture": lecture,
        "hash": local_hash,
        "size_bytes": local_size,
        "pushed_at": datetime.now().isoformat(),
        "files": []
    }

    # List files for manifest
    for file_path in sorted(local_path.rglob("*")):
        if file_path.is_file() and not file_path.name.startswith("."):
            rel_path = file_path.relative_to(local_path)
            manifest["files"].append({
                "path": str(rel_path),
                "size": file_path.stat().st_size
            })

    # Save manifest locally first
    save_local_manifest(lecture, manifest)

    # Upload to HF
    api = HfApi()
    commit_message = f"{lecture} @ {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    print(f"\nUploading to Hugging Face...")
    try:
        api.upload_folder(
            folder_path=str(local_path),
            repo_id=repo_id,
            repo_type="dataset",
            path_in_repo=lecture,
            commit_message=commit_message,
        )
        print(f"\nSuccess! Commit: {commit_message}")
    except Exception as e:
        error_msg = str(e)
        if "timed out" in error_msg.lower():
            print(f"\nUpload timed out during finalization.")
            print("The data may have been uploaded. Check with: just hugdata status")
            print("If still showing 'local only', retry the push.")
        else:
            print(f"Error uploading: {e}")
        sys.exit(1)


def cmd_pull(args: argparse.Namespace) -> None:
    """Pull data from HF."""
    try:
        from huggingface_hub import hf_hub_download, snapshot_download
    except ImportError:
        print("Error: huggingface_hub not installed. Run: uv add huggingface_hub")
        sys.exit(1)

    repo_id = get_hf_repo()

    if args.all:
        # Pull all lectures
        print(f"Pulling all lectures from {repo_id}...")
        try:
            snapshot_download(
                repo_id,
                repo_type="dataset",
                local_dir=REPO_ROOT / ".hf_download_tmp",
            )
            # Move to proper locations
            tmp_dir = REPO_ROOT / ".hf_download_tmp"
            for lec_dir in tmp_dir.iterdir():
                if lec_dir.is_dir():
                    target = LECTURES_DIR / lec_dir.name / "processed_data"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        import shutil
                        shutil.rmtree(target)
                    lec_dir.rename(target)
                    print(f"  Pulled: {lec_dir.name}")
            # Cleanup
            if tmp_dir.exists():
                import shutil
                shutil.rmtree(tmp_dir)
            print("Done!")
        except Exception as e:
            print(f"Error pulling: {e}")
            sys.exit(1)
    else:
        # Pull specific path (lecture or subdir)
        path = args.path
        if not path:
            print("Error: Please specify a lecture or path to pull.")
            print("Usage: just hugdata pull <lecture>")
            print("       just hugdata pull <lecture>/<subdir>")
            print("       just hugdata pull --all")
            sys.exit(1)

        # Parse path - could be "lecture" or "lecture/subdir"
        parts = path.split("/", 1)
        lecture = parts[0]
        subpath = parts[1] if len(parts) > 1 else ""

        target_base = LECTURES_DIR / lecture / "processed_data"

        print(f"Pulling: {path} from {repo_id}")

        try:
            if subpath:
                # Pull specific subdirectory
                allow_patterns = f"{lecture}/{subpath}/**"
                local_dir = REPO_ROOT / ".hf_download_tmp"
                snapshot_download(
                    repo_id,
                    repo_type="dataset",
                    local_dir=local_dir,
                    allow_patterns=[allow_patterns],
                )
                # Move to proper location
                source = local_dir / lecture / subpath
                target = target_base / subpath
                if source.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        import shutil
                        shutil.rmtree(target)
                    source.rename(target)
                    print(f"  Pulled to: {target}")
                # Cleanup
                import shutil
                shutil.rmtree(local_dir, ignore_errors=True)
            else:
                # Pull entire lecture
                allow_patterns = f"{lecture}/**"
                local_dir = REPO_ROOT / ".hf_download_tmp"
                snapshot_download(
                    repo_id,
                    repo_type="dataset",
                    local_dir=local_dir,
                    allow_patterns=[allow_patterns],
                )
                # Move to proper location
                source = local_dir / lecture
                if source.exists():
                    target_base.parent.mkdir(parents=True, exist_ok=True)
                    if target_base.exists():
                        import shutil
                        shutil.rmtree(target_base)
                    source.rename(target_base)
                    print(f"  Pulled to: {target_base}")
                # Cleanup
                import shutil
                shutil.rmtree(local_dir, ignore_errors=True)

            print("Done!")
        except Exception as e:
            print(f"Error pulling: {e}")
            sys.exit(1)


def cmd_pushall(args: argparse.Namespace) -> None:
    """Push all lectures that are local-only or ahead of remote."""
    try:
        from huggingface_hub import HfApi, hf_hub_download, list_repo_tree
    except ImportError:
        print("Error: huggingface_hub not installed. Run: uv add huggingface_hub")
        sys.exit(1)

    repo_id = get_hf_repo()

    # Get remote lectures
    remote_lectures = set()
    try:
        for item in list_repo_tree(repo_id, repo_type="dataset"):
            if item.path and "/" not in item.path and not item.path.startswith("."):
                if not hasattr(item, "type"):
                    if "." not in item.path:
                        remote_lectures.add(item.path)
    except Exception as e:
        print(f"Warning: Could not fetch remote info: {e}")

    # Find lectures that need pushing
    to_push = []
    local_lectures = get_lectures()

    for lec in local_lectures:
        local_path = LECTURES_DIR / lec / "processed_data"
        local_hash = compute_dir_hash(local_path)

        has_remote = lec in remote_lectures
        if not has_remote:
            to_push.append((lec, "local only"))
        else:
            # Check if ahead
            local_manifest = get_local_manifest(lec)
            if not local_manifest or local_manifest.get("hash") != local_hash:
                to_push.append((lec, "ahead"))
            else:
                # Check remote hash
                try:
                    manifest_path = hf_hub_download(
                        repo_id,
                        f"{lec}/{MANIFEST_FILENAME}",
                        repo_type="dataset",
                        local_dir=REPO_ROOT / ".hf_cache",
                        force_download=True,
                    )
                    with open(manifest_path) as f:
                        remote_manifest = json.load(f)
                    remote_hash = remote_manifest.get("hash", "")
                    if local_hash != remote_hash:
                        to_push.append((lec, "ahead"))
                except Exception:
                    pass  # If we can't check, skip

    if not to_push:
        print("All lectures are synced. Nothing to push.")
        return

    print(f"Found {len(to_push)} lecture(s) to push:")
    for lec, status in to_push:
        print(f"  - {lec} ({status})")
    print()

    # Push each lecture
    failed = []
    for lec, status in to_push:
        local_path = LECTURES_DIR / lec / "processed_data"
        local_hash = compute_dir_hash(local_path)
        local_size = get_dir_size(local_path)

        print(f"Pushing: {lec}")
        print(f"  Size: {format_size(local_size)}")

        # Create manifest
        manifest = {
            "lecture": lec,
            "hash": local_hash,
            "size_bytes": local_size,
            "pushed_at": datetime.now().isoformat(),
            "files": []
        }

        for file_path in sorted(local_path.rglob("*")):
            if file_path.is_file() and not file_path.name.startswith("."):
                rel_path = file_path.relative_to(local_path)
                manifest["files"].append({
                    "path": str(rel_path),
                    "size": file_path.stat().st_size
                })

        save_local_manifest(lec, manifest)

        api = HfApi()
        commit_message = f"{lec} @ {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        try:
            api.upload_folder(
                folder_path=str(local_path),
                repo_id=repo_id,
                repo_type="dataset",
                path_in_repo=lec,
                commit_message=commit_message,
            )
            print(f"  Done\n")
        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower():
                print(f"  ? Timed out (may have succeeded)\n")
            else:
                print(f"  Failed: {e}\n")
                failed.append(lec)

    if failed:
        print(f"\nFailed to push: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("All pushes completed successfully!")


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Manage lecture data on Hugging Face",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                          Show sync status
  %(prog)s push 03-neural-networks         Push lecture data
  %(prog)s pushall                         Push all local-only/ahead lectures
  %(prog)s pull 03-neural-networks         Pull lecture data
  %(prog)s pull 03-neural-networks/models  Pull subdirectory
  %(prog)s pull --all                      Pull all lectures
  %(prog)s init                            Initialize HF connection
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize HF repo connection")
    init_parser.set_defaults(func=cmd_init)

    # status
    status_parser = subparsers.add_parser("status", help="Show sync status")
    status_parser.set_defaults(func=cmd_status)

    # push
    push_parser = subparsers.add_parser("push", help="Push lecture to HF")
    push_parser.add_argument("lecture", help="Lecture name to push")
    push_parser.set_defaults(func=cmd_push)

    # pushall
    pushall_parser = subparsers.add_parser("pushall", help="Push all local-only and ahead lectures")
    pushall_parser.set_defaults(func=cmd_pushall)

    # pull
    pull_parser = subparsers.add_parser("pull", help="Pull from HF")
    pull_parser.add_argument("path", nargs="?", help="Lecture or subpath to pull")
    pull_parser.add_argument("--all", action="store_true", help="Pull all lectures")
    pull_parser.set_defaults(func=cmd_pull)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
