#!/usr/bin/env python3
"""Install this repository as a project-scoped Codex or Claude Code skill.

--check is a no-write preflight, not proof either agent CLI is installed.
Only manifest-managed, unmodified files may be upgraded. Unmanaged files are
never removed. Symlink components are rejected on both sides of the copy.
"""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile

from kit import ROOT, SHA, VERSION, digest, emit, read_json, safe_path

MANIFEST = '.science-lab-production-managed.json'
INCLUDE_DIRS = {'scripts', 'tests', 'templates', 'references', 'examples', 'resources', 'assets', 'adapters', 'verification'}
INCLUDE_FILES = {'SKILL.md', 'README.md', 'AGENTS.md', 'LICENSE', 'LICENSE.md', 'CHANGELOG.md'}
EXCLUDE = {'.git', '__pycache__', '.cache', 'cache', 'evidence', 'reports', 'node_modules', '.venv', '.pytest_cache'}


def relative_name(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('unsafe manifest entry')
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '.' in path.parts or name == MANIFEST:
        raise ValueError('unsafe manifest entry')
    return path


def package_files():
    files = {}
    for node in sorted(ROOT.iterdir()):
        if node.name not in INCLUDE_DIRS | INCLUDE_FILES and not (node.is_file() and node.suffix.lower() in ('.md', '.json')):
            continue
        if node.is_symlink():
            raise ValueError('symlink in source package')
        if node.is_file():
            files[node.name] = node
        elif node.is_dir():
            for directory, dirs, names in os.walk(node, followlinks=False):
                base = Path(directory)
                for name in list(dirs):
                    if name in EXCLUDE:
                        dirs.remove(name)
                    elif (base / name).is_symlink():
                        raise ValueError('symlink in source package')
                for name in sorted(names):
                    source = base / name
                    if source.is_symlink():
                        raise ValueError('symlink in source package')
                    if name.endswith(('.pyc', '.pyo')):
                        continue
                    files[source.relative_to(ROOT).as_posix()] = source
    if 'SKILL.md' not in files or 'scripts/kit.py' not in files:
        raise ValueError('incomplete source package')
    return files


def atomic_write(path, payload):
    safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.science-lab-install-', delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        safe_path(path)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def install(args):
    project = safe_path(args.project, must_exist=True)
    agent_root = '.agents' if args.agent == 'codex' else '.claude'
    destination = safe_path(project / agent_root / 'skills' / 'science-lab-production')
    manifest_path = safe_path(destination / MANIFEST)
    previous = {}
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if not isinstance(manifest, dict) or manifest.get('owner') != 'science-lab-production-kit' or not isinstance(manifest.get('files'), dict):
            raise ValueError('invalid managed manifest')
        previous = manifest['files']
        for name, sha in previous.items():
            relative_name(name)
            if not isinstance(sha, str) or not SHA.fullmatch(sha):
                raise ValueError('invalid manifest hash')
            safe_path(destination / name)
    sources = package_files()
    hashes = {name: digest(source) for name, source in sources.items()}
    changes, conflicts = [], []
    for name in sorted(sources):
        relative_name(name)
        target = safe_path(destination / name)
        if target.exists():
            if not target.is_file():
                conflicts.append(name)
                continue
            actual = digest(target)
            if actual == hashes[name]:
                continue
            if name not in previous or actual != previous[name]:
                conflicts.append(name)
                continue
        changes.append(name)
    if conflicts:
        # No filenames or content are printed: filenames too may contain secrets.
        emit({'status': 'conflict', 'conflict_count': len(conflicts), 'written': False,
              'reason': 'User-owned or user-modified files would be overwritten.'})
        return 1
    if args.check:
        emit({'status': 'check-ok', 'would_write': len(changes), 'written': False, 'agent': args.agent,
              'agent_cli_verified': False})
        return 0
    # Preflight is complete before the first mutation. Keep old entries for files
    # removed from a future package; never delete them or claim ownership of extras.
    for name in changes:
        atomic_write(destination / name, sources[name].read_bytes())
        args._written_files = getattr(args, '_written_files', 0) + 1
    managed = dict(previous)
    managed.update(hashes)
    payload = (json.dumps({'owner': 'science-lab-production-kit', 'version': VERSION, 'files': managed}, indent=2, sort_keys=True) + '\n').encode()
    atomic_write(manifest_path, payload)
    args._written_files = getattr(args, '_written_files', 0) + 1
    # Read exact targets back before reporting an installed external state.
    if any(digest(destination / name) != sha for name, sha in hashes.items()) or read_json(manifest_path)['files'] != managed:
        raise ValueError('installation read-back failed')
    emit({'status': 'installed' if changes else 'unchanged', 'written_files': len(changes), 'managed_files': len(managed),
          'agent': args.agent, 'agent_cli_verified': False})
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=('codex', 'claude'), required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        return install(args)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        emit({'status': 'error', 'category': type(exc).__name__, 'written': bool(getattr(args, '_written_files', 0)), 'written_files': getattr(args, '_written_files', 0),
              'reason': 'Unsafe path, symlink, incomplete package or inaccessible input; inspect managed targets if writes were reported.'})
        return 2


if __name__ == '__main__':
    sys.exit(main())
