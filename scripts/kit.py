#!/usr/bin/env python3
"""Deterministic, offline gates. A validator checks evidence, never manufactures it.

Exit codes: 0 gate satisfied, 1 gate failed, 2 input/IO error. JSON output never
includes source text or secret values. No network requests are made by this CLI.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.0.0'
VIEWPORTS = ('1440x1000', '1024x768', '820x1180', '390x844', '360x640', '844x390')
RESERVED = {'.git', '.', '..', 'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)), *(f'lpt{i}' for i in range(1, 10))}
PENDING = {'', 'pending', 'todo', 'tbd', 'unknown', 'unverified'}
SHA = re.compile(r'^[0-9a-f]{64}$')
SLUG = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')


def emit(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def read_json(path):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=no_duplicates,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('non-finite JSON number')))


def template(name):
    return read_json(ROOT / 'templates' / name)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_path(value, must_exist=False):
    """Reject traversal, portable reserved names and symlink components."""
    p = Path(value).expanduser()
    for part in p.parts:
        if part in (p.anchor, ''):
            continue
        if part.lower().split('.')[0] in RESERVED or part in RESERVED or part.endswith((' ', '.')) or '\\' in part or ':' in part:
            raise ValueError('unsafe path component')
    absolute = Path(os.path.abspath(p))
    for node in [absolute, *absolute.parents]:
        if node.is_symlink():
            raise ValueError('symlink paths are not allowed')
    if must_exist and not absolute.is_dir():
        raise ValueError('project directory does not exist')
    return absolute


def contained(root, value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('file path must be a relative POSIX path')
    relative = PurePosixPath(value)
    if relative.is_absolute() or any(p in ('..', '.') for p in relative.parts) or ':' in value:
        raise ValueError('file path escapes project')
    target = safe_path(root / relative)
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError('file missing or outside project')
    if target.stat().st_size == 0:
        raise ValueError('empty evidence file')
    return target


def valid_slug(value):
    return isinstance(value, str) and bool(SLUG.fullmatch(value)) and value not in RESERVED and len(value) <= 80


def init_project(args):
    if not valid_slug(args.slug) or not args.name.strip() or any(ord(c) < 32 for c in args.name):
        raise ValueError('invalid name or slug')
    output = safe_path(args.output)
    if output.exists():
        raise ValueError('refusing to overwrite an existing path')
    if not output.parent.is_dir():
        raise ValueError('output parent directory must already exist')
    contract = template('project-contract.json')
    contract.update(name=args.name, slug=args.slug)
    contract['scenes'] = [template('scene-contract.json')]
    files = {
        'project-contract.json': json.dumps(contract, ensure_ascii=False, indent=2) + '\n',
        'evidence.json': json.dumps(template('evidence.json'), ensure_ascii=False, indent=2) + '\n',
        'PROJECT.md': '# ' + args.name + '\n\nStatus: pending. No scientific review, browser evidence or deployment is implied.\n\nComplete project-contract.json and collect genuine evidence.json records.\n',
        'AGENTS.md': '# Science laboratory project\n\nUse the science-lab-production suite that invoked init (cloned repository or installed skill root). Set SCIENCE_LAB_KIT_ROOT to that root on this machine; never copy a maintainer’s private absolute path.\n\nRead "$SCIENCE_LAB_KIT_ROOT/SKILL.md" and its references before editing.\n\n```sh\npython3 "$SCIENCE_LAB_KIT_ROOT/scripts/kit.py" validate --project . --stage design\npython3 "$SCIENCE_LAB_KIT_ROOT/scripts/kit.py" validate --project . --stage release\n```\n\nNever invent scientific sources, screenshots, browser logs, voice execution or deployment success. A pending design is not a reviewed scientific design.\n'
    }
    output.mkdir()
    for name, content in files.items():
        (output / name).write_text(content, encoding='utf-8')
    emit({'created': sorted(files), 'status': 'pending', 'release_passed': False})
    return 0


def structure(value, expected, prefix, errors):
    if isinstance(expected, dict):
        if not isinstance(value, dict):
            errors.append(prefix + ': expected object')
            return
        for key, child in expected.items():
            if key not in value:
                errors.append(prefix + '.' + key + ': missing')
            else:
                structure(value[key], child, prefix + '.' + key, errors)
    elif isinstance(expected, list):
        if not isinstance(value, list):
            errors.append(prefix + ': expected array')
        elif expected:
            if not value:
                errors.append(prefix + ': empty array')
            for i, child in enumerate(value):
                structure(child, expected[0], f'{prefix}[{i}]', errors)
    elif type(value) is not type(expected):
        errors.append(prefix + ': incorrect type')


def text(value):
    return isinstance(value, str) and value.strip().lower() not in PENDING


def http_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return parsed.scheme in ('http', 'https') and bool(parsed.hostname) and not parsed.username and not parsed.password


def check_pending(value, prefix, errors):
    if isinstance(value, dict):
        for key, child in value.items():
            check_pending(child, prefix + '.' + key, errors)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            check_pending(child, f'{prefix}[{i}]', errors)
    elif isinstance(value, str) and not text(value):
        errors.append(prefix + ': unresolved pending value')


def file_record(root, item, prefix, errors):
    if not isinstance(item, dict) or not SHA.fullmatch(str(item.get('sha256', ''))):
        errors.append(prefix + ': expected path and lowercase SHA-256')
        return False
    try:
        path = contained(root, item.get('path'))
        if digest(path) != item['sha256']:
            errors.append(prefix + ': SHA-256 mismatch')
            return False
        return True
    except (ValueError, OSError):
        errors.append(prefix + ': unsafe, empty or missing file')
        return False


def all_file_records(value, prefix='evidence'):
    if isinstance(value, dict):
        if 'path' in value or ('sha256' in value and 'url' not in value):
            yield prefix, value
        for key, child in value.items():
            yield from all_file_records(child, prefix + '.' + key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from all_file_records(child, f'{prefix}[{i}]')


def hash_errors(root, evidence):
    errors = []
    records = list(all_file_records(evidence))
    if not records:
        errors.append('evidence: no file hash records')
    for prefix, item in records:
        file_record(root, item, prefix, errors)
    return errors, len(records)


def reviewed(root, review, prefix, errors):
    if not isinstance(review, dict) or review.get('status') != 'reviewed' or not text(review.get('reviewer')):
        errors.append(prefix + ': named reviewer and review record required')
        return
    try:
        contained(root, review.get('record'))
    except (ValueError, OSError):
        errors.append(prefix + ': review record file required')


def release_contract(root, c, errors):
    required = copy.deepcopy(c)
    for scene in required['scenes']:
        if scene['video']['status'] in ('none', 'pending'):
            scene.pop('video')
    check_pending(required, 'contract', errors)
    if c.get('mode') not in ('new', 'iterate'):
        errors.append('contract.mode: expected new or iterate')
    audience = c.get('audience', {})
    lo, hi = audience.get('min_grade'), audience.get('max_grade')
    if type(lo) is not int or type(hi) is not int or not (1 <= lo <= hi <= 4):
        errors.append('contract.audience: grades must be within 1–4')
    if not c.get('subjects') or not all(text(v) for v in c['subjects']):
        errors.append('contract.subjects: real subjects required')
    reviewed(root, c.get('design_review'), 'contract.design_review', errors)
    scene_ids = {s['id'] for s in c['scenes']}
    if not c.get('exploration_map'):
        errors.append('contract.exploration_map: a theme map is required')
    for area in c.get('exploration_map', []):
        if not area['scene_ids'] or any(sid not in scene_ids for sid in area['scene_ids']):
            errors.append('contract.exploration_map: all scene references must exist')
    representative = c['representative_scene']
    reviewed(root, representative, 'contract.representative_scene', errors)
    if representative['id'] not in scene_ids:
        errors.append('contract.representative_scene.id: scene must exist')
    ui = c['ui']
    if type(ui['primary_touch_target_px']) is not int or ui['primary_touch_target_px'] < 44:
        errors.append('contract.ui.primary_touch_target_px: minimum 44 CSS px')
    for key in ('few_large_buttons', 'centered_top_navigation', 'compact_vertical_layout', 'portrait_recomposition'):
        if ui[key] is not True:
            errors.append('contract.ui.' + key + ': required')
    ids = []
    for index, scene in enumerate(c['scenes']):
        p = f'contract.scenes[{index}]'
        ids.append(scene['id'])
        if not valid_slug(scene['id']):
            errors.append(p + '.id: invalid slug')
        for key in ('title', 'learning_goal', 'student_action', 'causal_chain', 'observable_feedback'):
            if not text(scene[key]):
                errors.append(p + '.' + key + ': substantive reviewed content required')
        if not scene['sources']:
            errors.append(p + '.sources: at least one verified source required')
        for i, source in enumerate(scene['sources']):
            if not http_url(source['url']) or source['status'] != 'verified' or not all(text(source[k]) for k in ('identity', 'license', 'type')):
                errors.append(p + f'.sources[{i}]: verified identity/URL/license/type required')
        for key in ('science_review', 'safety_review'):
            reviewed(root, scene[key], p + '.' + key, errors)
        narration = scene['narration']
        if narration['status'] != 'reviewed' or narration['implementation'] not in ('prerecorded', 'tts', 'live'):
            errors.append(p + '.narration: reviewed script and explicit voice implementation required')
        if not text(narration['script']) or not text(narration['implementation_detail']):
            errors.append(p + '.narration: complete script and implementation detail required')
        if narration['implementation'] == 'live' and narration['fallback'] not in ('none', 'explicit-unavailable'):
            errors.append(p + '.narration.fallback: live must not impersonate AI using fixed speech')
        for key in ('automatic_on_scene', 'complete_sentences', 'same_page_no_repeat', 'stop_previous_on_switch', 'effects_independent'):
            if narration[key] is not True:
                errors.append(p + '.narration.' + key + ': required')
        if scene['dynamic_behavior'] is False and (not text(scene['static_reference_reason']) or scene['static_reference_reason'] == 'not-applicable'):
            errors.append(p + '.static_reference_reason: static reference requires a reviewed scientific reason, not a missing animation excuse')
        video = scene['video']
        if video['status'] not in ('none', 'pending', 'ready'):
            errors.append(p + '.video.status: invalid')
        if video['status'] != 'ready' and video['student_button'] is not False:
            errors.append(p + '.video: absent/pending video cannot expose a dead student button')
        if video['replaces_core_interaction'] is not False:
            errors.append(p + '.video: cannot replace causal interaction')
        if video['status'] == 'ready' and not text(video['placement']):
            errors.append(p + '.video.placement: required')
    if len(ids) != len(set(ids)) or not ids:
        errors.append('contract.scenes: nonempty unique scene IDs required')
    if not http_url(c['deployment']['url']) or c['deployment']['status'] != 'verified':
        errors.append('contract.deployment: verified HTTP(S) deployment required')


def passed_result(root, result, prefix, errors):
    if not isinstance(result, dict) or result.get('status') != 'passed' or not text(result.get('observation')):
        errors.append(prefix + ': observed passed result required')
        return
    file_record(root, result.get('record'), prefix + '.record', errors)


def release_evidence(root, c, e, errors):
    if e.get('status') != 'collected':
        errors.append('evidence.status: expected collected, not an invented passed flag')
    browser = e['browser']
    if browser['kind'] != 'real' or not text(browser['engine']) or not text(browser['version']):
        errors.append('evidence.browser: real browser identity required; local/unit tests are insufficient')
    try:
        contained(root, browser['session_record'])
    except (ValueError, OSError):
        errors.append('evidence.browser.session_record: real browser session log required')
    origin = e['origin']
    if not http_url(origin['url']) or not text(origin['source_revision']) or not origin['source_files']:
        errors.append('evidence.origin: HTTP URL, revision and source file hashes required')
    if origin['url'] != c['deployment']['url']:
        errors.append('evidence.origin.url: must match deployment URL')
    for i, item in enumerate(origin['source_files']):
        file_record(root, item, f'evidence.origin.source_files[{i}]', errors)
    expected = {(s['id'], viewport) for s in c['scenes'] for viewport in VIEWPORTS}
    seen, screenshots = set(), set()
    for i, capture in enumerate(e['captures']):
        p = f'evidence.captures[{i}]'
        if not isinstance(capture, dict):
            errors.append(p + ': expected object')
            continue
        key = (capture.get('scene_id'), capture.get('viewport'))
        if key not in expected or key in seen:
            errors.append(p + ': duplicate or unknown scene × viewport')
        seen.add(key)
        if capture.get('origin_url') != origin['url'] or capture.get('source_revision') != origin['source_revision']:
            errors.append(p + ': origin and source revision must match')
        shot = capture.get('screenshot')
        if file_record(root, shot, p + '.screenshot', errors):
            path = contained(root, shot['path'])
            header = path.read_bytes()[:16]
            if not (header.startswith(b'\x89PNG\r\n\x1a\n') or header.startswith(b'\xff\xd8\xff') or (header.startswith(b'RIFF') and header[8:12] == b'WEBP')):
                errors.append(p + '.screenshot: expected PNG/JPEG/WebP image bytes')
            if shot['path'] in screenshots:
                errors.append(p + '.screenshot: reused path across scene/viewports')
            screenshots.add(shot['path'])
        scene = next((s for s in c['scenes'] if s['id'] == capture.get('scene_id')), None)
        for kind in ('runtime', 'mouse', 'touch', 'sound', 'narration', 'layout'):
            passed_result(root, capture.get(kind), p + '.' + kind, errors)
        sound = capture.get('sound', {})
        for key in ('voice_audible', 'effects_independent'):
            if sound.get(key) is not True:
                errors.append(p + '.sound.' + key + ': actual audio execution required')
        narration = capture.get('narration', {})
        for key in ('automatic_on_scene', 'complete_sentences', 'same_page_no_repeat', 'stop_previous_on_switch'):
            if narration.get(key) is not True:
                errors.append(p + '.narration.' + key + ': observed behavior required')
        motion = capture.get('pause_motion', {})
        if scene and scene.get('dynamic_behavior') is False:
            if motion.get('status') != 'not-applicable' or not text(motion.get('observation')):
                errors.append(p + '.pause_motion: static reference must explicitly explain non-applicability')
            file_record(root, motion.get('record'), p + '.pause_motion.record', errors)
        else:
            passed_result(root, motion, p + '.pause_motion', errors)
            if motion.get('changed_while_running') is not True or motion.get('stable_while_paused') is not True:
                errors.append(p + '.pause_motion: actual running/paused motion observations required')
        layout = capture.get('layout', {})
        narrow = str(capture.get('viewport', '')).split('x')[0] in ('390', '360')
        nav_ok = layout.get('navigation_centered') is True or (narrow and layout.get('navigation_overflow_scroll') is True and layout.get('navigation_first_last_reachable') is True)
        if type(layout.get('minimum_primary_touch_px')) not in (int, float) or layout['minimum_primary_touch_px'] < 44 or not nav_ok or layout.get('unobstructed_scene') is not True:
            errors.append(p + '.layout: measured 44px targets/centered or reachable narrow rail/unobstructed scene required')
    if seen != expected:
        errors.append('evidence.captures: missing complete scenes × six viewports coverage')
    deployment = e['deployment']
    if deployment['status'] != 'verified' or not deployment['http_checks'] or not deployment['hash_checks']:
        errors.append('evidence.deployment: verified HTTP and served-byte hash checks required')
    urls = set()
    for i, check in enumerate(deployment['http_checks']):
        p = f'evidence.deployment.http_checks[{i}]'
        if not isinstance(check, dict) or not http_url(check.get('url')) or check.get('status_code') != 200:
            errors.append(p + ': HTTP 200 observation required')
            continue
        urls.add(check['url'])
        file_record(root, check.get('record'), p + '.record', errors)
    if c['deployment']['url'] not in urls:
        errors.append('evidence.deployment.http_checks: target URL not verified')
    served_paths = set()
    source_hashes = {v.get('path'): v.get('sha256') for v in origin['source_files'] if isinstance(v, dict)}
    for i, check in enumerate(deployment['hash_checks']):
        p = f'evidence.deployment.hash_checks[{i}]'
        if not isinstance(check, dict):
            errors.append(p + ': expected object')
            continue
        if not http_url(check.get('url')) or check.get('status_code') != 200 or check.get('expected_sha256') != check.get('actual_sha256') or not SHA.fullmatch(str(check.get('actual_sha256', ''))):
            errors.append(p + ': HTTP 200 and matching served-byte SHA-256 required')
        local = check.get('local_path')
        if local not in source_hashes or source_hashes.get(local) != check.get('actual_sha256'):
            errors.append(p + ': must bind served hash to a source file')
        served_paths.add(local)
        file_record(root, check.get('record'), p + '.record', errors)
    if set(source_hashes) - served_paths:
        errors.append('evidence.deployment.hash_checks: all source files require served-byte checks')
    if c['mode'] == 'iterate':
        old = deployment['old_site_unchanged']
        if old['status'] != 'verified' or not old['before'] or not old['after']:
            errors.append('evidence.deployment.old_site_unchanged: verified before/after hashes required for iterate')
        before = {x.get('url'): x.get('sha256') for x in old['before'] if isinstance(x, dict)}
        after = {x.get('url'): x.get('sha256') for x in old['after'] if isinstance(x, dict)}
        if not before or before != after or any(not http_url(u) or not SHA.fullmatch(str(h)) for u, h in before.items()):
            errors.append('evidence.deployment.old_site_unchanged: protected HTTP URL hashes must be unchanged')
        try:
            contained(root, old['record'])
        except (ValueError, OSError):
            errors.append('evidence.deployment.old_site_unchanged.record: required')
    hashes, _ = hash_errors(root, e)
    errors.extend(hashes)


def validate(args):
    root = safe_path(args.project, must_exist=True)
    c = read_json(contained(root, 'project-contract.json'))
    e = read_json(contained(root, 'evidence.json'))
    errors = []
    contract_template = template('project-contract.json')
    contract_template['scenes'] = [template('scene-contract.json')]
    structure(c, contract_template, 'contract', errors)
    structure(e, template('evidence.json'), 'evidence', errors)
    if isinstance(c, dict) and c.get('schema_version') != VERSION:
        errors.append('contract.schema_version: unsupported')
    if isinstance(e, dict) and e.get('schema_version') != VERSION:
        errors.append('evidence.schema_version: unsupported')
    complete = not errors
    if complete:
        if not valid_slug(c['slug']):
            errors.append('contract.slug: invalid')
        if args.stage == 'release':
            release_contract(root, c, errors)
            release_evidence(root, c, e, errors)
    unresolved = []
    if complete:
        check_pending(c, 'contract', unresolved)
    emit({'stage': args.stage, 'structure_complete': complete, 'unresolved_contract_fields': len(unresolved), 'review_status': 'reviewed' if complete and c['design_review']['status'] == 'reviewed' else 'pending', 'scientific_approval': 'not-certified-by-cli', 'release_passed': args.stage == 'release' and not errors, 'errors': sorted(set(errors)), 'limitations': ['Evidence provenance and scientific correctness require human audit; hashes do not prove truth.', 'Viewport emulation is not physical-device certification.']})
    return 1 if errors else 0


def verify_hashes(args):
    root = safe_path(args.project, must_exist=True)
    errors, count = hash_errors(root, read_json(contained(root, 'evidence.json')))
    emit({'checked_records': count, 'errors': errors, 'release_passed': False})
    return 1 if errors else 0


# Values are never returned: only relative path, line and finding category.
SECRET = re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*[\"\x27]?[^\s\"\x27,;]{8,})', re.I)
PRIVATE = re.compile(r'(?:/home/[^\s/]+/|/opt/data/|/Users/[^\s/]+/|[A-Z]:\\Users\\)', re.I)
PROCESS = re.compile(r'作为\s*AI|我会继续执行|工具调用结果|OUT-OF-BAND USER MESSAGE|let me (?:think|check)|analysis channel', re.I)
SKIP = {'.git', '__pycache__', '.cache', 'node_modules', '.venv', 'venv'}


def scan(args):
    root = safe_path(args.root, must_exist=True)
    findings = []
    def add(path, line, kind):
        # Redact even a secret accidentally used as a filename.
        name = str(path.relative_to(root))
        if SECRET.search(name):
            name = '[redacted-filename]'
        findings.append({'file': name, 'line': line, 'kind': kind})
    for directory, dirs, files in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in list(dirs):
            if name in SKIP:
                dirs.remove(name)
            elif (base / name).is_symlink():
                add(base / name, 0, 'symlink')
                dirs.remove(name)
        for name in sorted(files):
            path = base / name
            if path.is_symlink():
                add(path, 0, 'symlink')
                continue
            try:
                content = path.read_text(encoding='utf-8')
            except UnicodeError:
                continue
            for number, line in enumerate(content.splitlines(), 1):
                for pattern, kind in ((SECRET, 'credential'), (PRIVATE, 'private-path'), (PROCESS, 'process-text')):
                    if pattern.search(line):
                        add(path, number, kind)
                if re.search(r'[\"\x27]sources[\"\x27]\s*:\s*\[\s*\]', line):
                    add(path, number, 'empty-source')
            if path.suffix.lower() in ('.md', '.html'):
                pattern = r'\]\(([^\s)]+)(?:\s+[^)]*)?\)' if path.suffix.lower() == '.md' else r'(?:href|src)=[\"\x27]([^\"\x27]+)'
                for match in re.finditer(pattern, content):
                    value = unquote(match.group(1).split('#')[0].split('?')[0])
                    if not value or value.startswith(('#', '/', '$')) or urlsplit(value).scheme:
                        continue
                    target = path.parent / value
                    try:
                        okay = target.resolve().is_relative_to(root) and target.exists() and not target.is_symlink()
                    except OSError:
                        okay = False
                    if not okay:
                        add(path, content.count('\n', 0, match.start()) + 1, 'broken-link')
            if path.suffix.lower() == '.json':
                try:
                    value = read_json(path)
                    def source_scan(node):
                        if isinstance(node, dict):
                            if 'sources' in node:
                                sources = node['sources']
                                if not isinstance(sources, list) or not sources or any(not isinstance(s, dict) or not http_url(s.get('url')) or s.get('status') != 'verified' for s in sources):
                                    add(path, 0, 'empty-source')
                            for child in node.values():
                                source_scan(child)
                        elif isinstance(node, list):
                            for child in node:
                                source_scan(child)
                    source_scan(value)
                except (ValueError, OSError):
                    add(path, 0, 'invalid-json')
    unique = {(x['file'], x['line'], x['kind']): x for x in findings}
    findings = [unique[k] for k in sorted(unique)]
    emit({'findings': findings, 'count': len(findings), 'network_links': 'not-fetched; remote HTTP evidence required separately'})
    return 1 if findings else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('init')
    p.add_argument('--name', required=True)
    p.add_argument('--slug', required=True)
    p.add_argument('--output', required=True)
    p.set_defaults(handler=init_project)
    p = commands.add_parser('validate')
    p.add_argument('--project', required=True)
    p.add_argument('--stage', choices=('design', 'release'), required=True)
    p.set_defaults(handler=validate)
    p = commands.add_parser('verify-file-hashes')
    p.add_argument('--project', required=True)
    p.set_defaults(handler=verify_hashes)
    p = commands.add_parser('scan')
    p.add_argument('--root', required=True)
    p.set_defaults(handler=scan)
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (ValueError, OSError, TypeError, KeyError, AttributeError) as exc:
        # Never echo invalid input, parsed JSON values, or operating-system paths.
        emit({'error': 'Invalid input or inaccessible file', 'category': type(exc).__name__, 'release_passed': False})
        return 2


if __name__ == '__main__':
    sys.exit(main())
