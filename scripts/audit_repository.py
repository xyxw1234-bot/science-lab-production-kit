#!/usr/bin/env python3
"""Repository quality checks, standard library only; not a product QA substitute."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
def audit(root=ROOT):
 errors=[];files=[p for p in root.rglob('*')if p.is_file()and not any(x in p.relative_to(root).parts for x in ['.git','__pycache__','.local','.test-output','node_modules'])]
 required=['SKILL.md','START-HERE.md','AGENTS.md','CLAUDE.md','README.md','LICENSE','manifest.json','VALIDATION.md','references/product-and-learning.md','references/scientific-modeling.md','references/child-ui-and-play.md','references/ai-mentor-and-media.md','references/engineering-and-release.md','references/review-rubric.md','references/topic-map.md','references/sources.md','templates/project-contract.json','templates/scene-contract.json','templates/evidence.json','templates/video-task.json','scripts/kit.py','scripts/install_skill.py','examples/energy-play/README.md']
 for f in required:
  if not(root/f).is_file():errors.append('missing required file: '+f)
 meta=json.loads((root/'manifest.json').read_text());skill=(root/'SKILL.md').read_text()
 if not skill.startswith('---\n')or '\n---\n'not in skill[4:]:errors.append('frontmatter missing')
 else:
  fm=skill.split('---',2)[1];name=re.search(r'^name:\s*(.+)$',fm,re.M);desc=re.search(r'^description:\s*(.+)$',fm,re.M)
  if not name or name.group(1)!=meta['name']:errors.append('skill name mismatch')
  if not desc or len(desc.group(1))>1024:errors.append('description invalid')
  if 'version: "'+meta['version']+'"'not in fm:errors.append('version mismatch')
  allowed={'name','description','license','compatibility','metadata','allowed-tools'}
  for key in re.findall(r'^([^ \n:]+):',fm,re.M):
   if key not in allowed:errors.append('nonstandard frontmatter field: '+key)
  if len(skill)>100000:errors.append('oversized skill')
 patterns=[('private-host-path',re.compile(r'/opt/data|/root/\.ssh|/home/[^ /]+/\.ssh')),('private-key',re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----')),('github-token',re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}')),('secret-assignment',re.compile(r'(?i)(?:api_key|access_token|password)\s*[:=]\s*[\"\'][^\"\'<>\s]{16,}[\"\']')),('conversation-marker',re.compile(r'OUT-OF-BAND USER MESSAGE|CONTEXT COMPACTION|ASYNC DELEGATION BATCH COMPLETE'))]
 text_ext={'.md','.json','.py','.mjs','.html','.css','.yml','.yaml','.txt'}
 for p in files:
  if p.suffix not in text_ext and p.name!='LICENSE':continue
  text=p.read_text(encoding='utf-8');rel=str(p.relative_to(root))
  if rel not in ['scripts/audit_repository.py','tests/test_repository.py']:
   scan_text=re.sub(r'^(?:SECRET|PRIVATE|PROCESS)\s*=.*$', '', text, flags=re.M) if rel=='scripts/kit.py' else text
   for label,pat in patterns:
    if pat.search(scan_text):errors.append(label+': '+rel)
  if p.suffix=='.md':
   for link in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)',text):
    if link.startswith(('http://','https://','mailto:','#')):continue
    target=(p.parent/link.split('#')[0]).resolve()
    if not target.is_relative_to(root.resolve())or not target.exists():errors.append('broken local link: '+rel+' -> '+link)
 for p in files:
  if p.suffix=='.json':
   try:json.loads(p.read_text())
   except Exception:errors.append('invalid JSON: '+str(p.relative_to(root)))
 audio=root/'examples/energy-play/audio';provenance=json.loads((audio/'provenance.json').read_text());scripts=json.loads((audio/'scripts.json').read_text())
 for row in provenance:
  f=audio/row['file']
  if not f.is_file()or hashlib.sha256(f.read_bytes()).hexdigest()!=row['sha256']:errors.append('audio hash mismatch: '+row['file'])
  if hashlib.sha256(scripts[row['scene']].encode()).hexdigest()!=row['textSha256']:errors.append('audio/subtitle source mismatch: '+row['scene'])
  if row['liveAI']is not False:errors.append('reference must not pretend live AI')
 summary_file=root/'verification/summary.json'
 if summary_file.is_file():
  summary=json.loads(summary_file.read_text())
  for rel,sha in summary.get('sourceFiles',{}).items():
   target=root/rel
   if not target.resolve().is_relative_to(root.resolve())or not target.is_file()or hashlib.sha256(target.read_bytes()).hexdigest()!=sha:errors.append('verification source hash mismatch: '+rel)
 return {'filesChecked':len(files),'errors':errors,'scope':'repository consistency and detectable hygiene; not proof of scientific truth, child enjoyment, real browser tests or physical-device performance'}
if __name__=='__main__':
 try:result=audit();print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(bool(result['errors']))
 except Exception as e:print(json.dumps({'errors':[str(e)]},ensure_ascii=False));sys.exit(1)
