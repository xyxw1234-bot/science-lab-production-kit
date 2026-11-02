import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('repository_audit',ROOT/'scripts/audit_repository.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class RepositoryTests(unittest.TestCase):
 def test_repository_is_self_contained(self):
  result=mod.audit(ROOT);self.assertEqual(result['errors'],[],result['errors'])
 def test_examples_have_clear_boundaries(self):
  text=(ROOT/'examples/energy-play/README.md').read_text();self.assertIn('不是完整能源实验室',text);self.assertIn('没有实时AI服务',text)
 def test_cross_agent_entry_is_not_a_second_spec(self):
  self.assertIn('SKILL.md',(ROOT/'AGENTS.md').read_text());self.assertIn('AGENTS.md',(ROOT/'CLAUDE.md').read_text());self.assertLess(len((ROOT/'CLAUDE.md').read_text()),1000)
if __name__=='__main__':unittest.main()
