"""Synthetic fixtures exercise mechanical gates, never product evidence."""
import argparse,base64,copy,hashlib,json,subprocess,sys,tempfile,unittest,shutil,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import kit,install_skill
class GateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.project=self.base/'project'
 def cmd(self,*args):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/kit.py'),*map(str,args)],capture_output=True,text=True,timeout=15);return r,json.loads(r.stdout)
 def init(self):
  r,d=self.cmd('init','--name','测试实验室','--slug','test-lab','--output',self.project);self.assertEqual(r.returncode,0,r.stdout);return d
 def rec(self,name,data=b'SYNTHETIC UNIT FIXTURE ONLY'):
  p=self.project/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return{'path':name,'sha256':hashlib.sha256(data).hexdigest()}
 def save(self,c,e):
  for n,d in [('project-contract.json',c),('evidence.json',e)]:(self.project/n).write_text(json.dumps(d))
 def validate(self,stage='release'):return self.cmd('validate','--project',self.project,'--stage',stage)
 def fixture(self):
  self.init();c=json.loads((self.project/'project-contract.json').read_text());e=json.loads((self.project/'evidence.json').read_text());log=self.rec('unit/log.txt');source=self.rec('site/index.html',b'<html>UNIT FIXTURE</html>');review={'status':'reviewed','reviewer':'unit-fixture-not-a-human','record':log['path']};scene=c['scenes'][0];url='https://example.invalid/unit/';rev='synthetic-revision'
  for k in ['title','learning_goal','student_action','causal_chain','observable_feedback']:scene[k]='unit-fixture '+k
  scene['replay']={'reset':'fixture reset','cancel':'fixture cancel','repeat_changes_state':'fixture change'};scene['sources']=[{'identity':'synthetic','url':'https://example.invalid/ref','license':'unit-only','type':'scientific-reference','status':'verified'}];scene['model_boundaries']={k:'unit-fixture'for k in ['representation','units','limits','not_claimed']};scene['science_review']=copy.deepcopy(review);scene['safety_review']=copy.deepcopy(review);scene['narration'].update(status='reviewed',script='完整的测试句子。',implementation='prerecorded',implementation_detail='unit-fixture-only')
  c.update(subjects=['unit'],product_intent='unit-fixture',design_review=review,exploration_map=[{'area':'unit','question':'unit question','scene_ids':['scene-1'],'depth':'unit depth','boundary':'unit scope'}],preservation={'approved_features':[],'production_targets':[],'change_scope':'unit-only','non_goals':['not-real-evidence']},representative_scene={'id':'scene-1','why_representative':'unit-only','status':'reviewed','reviewer':'unit-fixture','record':log['path']},deployment={'url':url,'immutable_release':'unit-only','status':'verified'})
  e.update(status='collected',browser={'kind':'real','engine':'SYNTHETIC FIXTURE','version':'unit-only','session_record':log['path']},origin={'url':url,'source_revision':rev,'source_files':[source]},files=[log],captures=[])
  png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j+XcAAAAASUVORK5CYII=')
  for v in kit.VIEWPORTS:
   r={'scene_id':'scene-1','viewport':v,'origin_url':url,'source_revision':rev,'screenshot':self.rec('unit/'+v+'.png',png)}
   for k in ['runtime','mouse','touch','sound','pause_motion','narration','layout']:r[k]={'status':'passed','observation':'synthetic unit observation only','record':copy.deepcopy(log)}
   r['sound'].update(voice_audible=True,effects_independent=True);r['pause_motion'].update(changed_while_running=True,stable_while_paused=True);r['narration'].update(automatic_on_scene=True,complete_sentences=True,same_page_no_repeat=True,stop_previous_on_switch=True);r['layout'].update(minimum_primary_touch_px=44,navigation_centered=True,unobstructed_scene=True);e['captures'].append(r)
  e['deployment'].update(status='verified',http_checks=[{'url':url,'status_code':200,'record':log}],hash_checks=[{'url':url+'site/index.html','local_path':source['path'],'status_code':200,'expected_sha256':source['sha256'],'actual_sha256':source['sha256'],'record':log}]);self.save(c,e);return c,e
 def assertRejected(self,c,e):self.save(c,e);self.assertNotEqual(self.validate()[0].returncode,0)
 def test_pending_is_not_release(self):
  self.assertFalse(self.init()['release_passed']);r,d=self.validate('design');self.assertEqual(r.returncode,0);self.assertEqual(d['review_status'],'pending');self.assertGreater(d['unresolved_contract_fields'],0);self.assertFalse(d['release_passed']);self.assertNotEqual(self.validate()[0].returncode,0)
 def test_no_overwrite(self):
  self.init();r,_=self.cmd('init','--name','x','--slug','x','--output',self.project);self.assertNotEqual(r.returncode,0)
 def test_bad_slugs(self):
  for slug in ['../escape','con','nul','has space','a--b','']:
   r,_=self.cmd('init','--name','x','--slug',slug,'--output',self.project);self.assertNotEqual(r.returncode,0)
 def test_symlink_init_refused(self):
  real=self.base/'real';real.mkdir();link=self.base/'link';link.symlink_to(real,target_is_directory=True);r,_=self.cmd('init','--name','x','--slug','x','--output',link/'new');self.assertNotEqual(r.returncode,0);self.assertFalse((real/'new').exists())
 def test_structure_pass_does_not_certify_truth(self):
  self.fixture();r,d=self.validate();self.assertEqual(r.returncode,0,r.stdout);self.assertTrue(d['release_passed']);self.assertEqual(d['scientific_approval'],'not-certified-by-cli')
 def test_missing_capture(self):
  c,e=self.fixture();e['captures'].pop();self.assertRejected(c,e)
 def test_missing_screenshot(self):
  c,e=self.fixture();(self.project/e['captures'][0]['screenshot']['path']).unlink();self.assertRejected(c,e)
 def test_changed_source(self):
  c,e=self.fixture();(self.project/'site/index.html').write_text('changed');self.assertRejected(c,e)
 def test_nonimage_capture(self):
  c,e=self.fixture();e['captures'][0]['screenshot']=self.rec('unit/fake.png',b'not-image');self.assertRejected(c,e)
 def test_duplicate_scenes(self):
  c,e=self.fixture();c['scenes'].append(copy.deepcopy(c['scenes'][0]));self.assertRejected(c,e)
 def test_reused_screenshot(self):
  c,e=self.fixture();e['captures'][1]['screenshot']=copy.deepcopy(e['captures'][0]['screenshot']);self.assertRejected(c,e)
 def test_fake_live_fallback(self):
  c,e=self.fixture();c['scenes'][0]['narration'].update(implementation='live',fallback='fixed-answer');self.assertRejected(c,e)
 def test_dead_video_button(self):
  c,e=self.fixture();c['scenes'][0]['video'].update(status='pending',student_button=True);self.assertRejected(c,e)
 def test_unverified_source(self):
  c,e=self.fixture();c['scenes'][0]['sources'][0]['status']='pending';self.assertRejected(c,e)
 def test_no_real_browser(self):
  c,e=self.fixture();e['browser']['kind']='mock';self.assertRejected(c,e)
 def test_wrong_revision(self):
  c,e=self.fixture();e['captures'][0]['source_revision']='wrong';self.assertRejected(c,e)
 def test_exploration_map_and_representative(self):
  c,e=self.fixture();c['exploration_map'][0]['scene_ids']=['absent'];c['representative_scene']['status']='pending';self.assertRejected(c,e)
 def test_touch_size(self):
  c,e=self.fixture();c['ui']['primary_touch_target_px']=32;self.assertRejected(c,e)
 def test_iteration_needs_protected_target(self):
  c,e=self.fixture();c['mode']='iterate';self.assertRejected(c,e)
 def test_static_reference_exemption_is_explicit(self):
  c,e=self.fixture();c['scenes'][0]['dynamic_behavior']=False;self.assertRejected(c,e);c['scenes'][0]['static_reference_reason']='Source original remains unchanged; manual inspection only.'
  for r in e['captures']:r['pause_motion'].update(status='not-applicable',observation='Static source reference is not animated.')
  self.save(c,e);r,d=self.validate();self.assertEqual(r.returncode,0,r.stdout)
 def test_narrow_rail_requires_reachability(self):
  c,e=self.fixture()
  for r in e['captures']:
   if r['viewport'].startswith(('390x','360x')):r['layout'].update(navigation_centered=False,navigation_overflow_scroll=True,navigation_first_last_reachable=True)
  self.save(c,e);self.assertEqual(self.validate()[0].returncode,0);e['captures'][3]['layout']['navigation_first_last_reachable']=False;self.assertRejected(c,e)
 def test_path_escape(self):
  c,e=self.fixture();e['captures'][0]['screenshot']['path']='../outside.png';self.assertRejected(c,e)
 def test_duplicate_json_key_and_nan(self):
  self.init()
  for data in ['{"x":1,"x":2}','{"x":NaN}']:(self.project/'evidence.json').write_text(data);self.assertNotEqual(self.validate()[0].returncode,0)
 def test_hash_cli(self):
  self.fixture();r,d=self.cmd('verify-file-hashes','--project',self.project);self.assertEqual(r.returncode,0,r.stdout)
 def test_scan_redacts_secret(self):
  self.project.mkdir();secret='gh'+'p_'+'Z'*30;(self.project/'unit.txt').write_text(secret);r,d=self.cmd('scan','--root',self.project);self.assertNotEqual(r.returncode,0);self.assertNotIn(secret,r.stdout)
class InstallerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.project=Path(self.tmp.name)/'project';self.project.mkdir()
 def dest(self,agent='codex'):return self.project/('.agents'if agent=='codex'else'.claude')/'skills/science-lab-production'
 def install(self,*extra,agent='codex',source=ROOT):
  r=subprocess.run([sys.executable,str(source/'scripts/install_skill.py'),'--agent',agent,'--project',str(self.project),*extra],capture_output=True,text=True,timeout=20);return r,json.loads(r.stdout)
 def test_check_then_install_readback(self):
  r,d=self.install('--check');self.assertEqual(r.returncode,0);self.assertFalse(self.dest().exists());r,d=self.install();self.assertEqual(r.returncode,0,r.stdout);self.assertFalse(d['agent_cli_verified']);self.assertEqual((self.dest()/'SKILL.md').read_bytes(),(ROOT/'SKILL.md').read_bytes());self.assertTrue((self.dest()/'tests/test_kit.py').exists());r,d=self.install('--check');self.assertEqual(d['would_write'],0)
 def test_claude(self):
  r,d=self.install(agent='claude');self.assertEqual(r.returncode,0,r.stdout);self.assertTrue((self.dest('claude')/'SKILL.md').exists())
 def test_unmanaged_file_preserved(self):
  self.install();p=self.dest()/'my-note.md';p.write_text('keep');r,d=self.install();self.assertEqual(r.returncode,0);self.assertEqual(p.read_text(),'keep');self.assertEqual(d['status'],'unchanged')
 def test_modified_managed_conflict(self):
  self.install();p=self.dest()/'SKILL.md';p.write_text('custom');r,d=self.install();self.assertNotEqual(r.returncode,0);self.assertEqual(p.read_text(),'custom')
 def test_unmanaged_collision(self):
  self.dest().mkdir(parents=True);p=self.dest()/'SKILL.md';p.write_text('existing');r,d=self.install();self.assertNotEqual(r.returncode,0);self.assertEqual(p.read_text(),'existing')
 def test_symlink_target(self):
  (self.project/'.agents').symlink_to(self.project,target_is_directory=True);r,d=self.install();self.assertNotEqual(r.returncode,0);self.assertFalse(d['written'])
 def test_malicious_managed_path(self):
  self.install();p=self.dest()/install_skill.MANIFEST;m=json.loads(p.read_text());m['files']['../escape']='0'*64;p.write_text(json.dumps(m));self.assertNotEqual(self.install()[0].returncode,0)
 def test_installed_links(self):
  self.install()
  for f in [self.dest()/'SKILL.md',self.dest()/'README.md']:
   for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',f.read_text()):
    if not link.startswith(('http:','https:','#')):self.assertTrue((f.parent/link).exists(),link)
 def test_installed_cli(self):
  self.install();r=subprocess.run([sys.executable,str(self.dest()/'scripts/kit.py'),'--version'],capture_output=True,text=True);self.assertEqual(r.returncode,0);self.assertIn('1.0.0',r.stdout)
 def test_payload_upgrade_keeps_user_files(self):
  src=Path(self.tmp.name)/'source';shutil.copytree(ROOT,src,ignore=shutil.ignore_patterns('.git','.local','__pycache__'));self.assertEqual(self.install(source=src)[0].returncode,0);note=self.dest()/'user.md';note.write_text('keep');p=src/'SKILL.md';p.write_text(p.read_text()+'\nSynthetic installer update only.\n');r,d=self.install(source=src);self.assertEqual(r.returncode,0,r.stdout);self.assertEqual((self.dest()/'SKILL.md').read_bytes(),p.read_bytes());self.assertEqual(note.read_text(),'keep')
 def test_partial_write_reports_mutation(self):
  from unittest.mock import patch
  args=argparse.Namespace(project=str(self.project),agent='codex',check=False);real=install_skill.atomic_write;count=0
  def broken(path,data):
   nonlocal count
   count+=1
   if count==2:raise OSError('synthetic failure')
   real(path,data)
  with patch.object(install_skill,'atomic_write',broken):
   with self.assertRaises(OSError):install_skill.install(args)
  self.assertEqual(args._written_files,1)
if __name__=='__main__':unittest.main()
