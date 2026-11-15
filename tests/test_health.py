import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from pair_health import assess

class HealthTests(unittest.TestCase):
    def test_inactive_service_cannot_be_ready_despite_stale_browser_data(self):
        result=assess({'service':'inactive','browser':{'reachable':True,'connected':True,'extensionVersion':'0.3.1'}},'0.3.1')
        self.assertEqual(result['state'],'unavailable')
    def test_running_old_extension_requires_reload(self):
        result=assess({'bridgeService':{'ok':True},'browser':{'serviceReachable':True,'connected':True,'extensionVersion':'0.3.0','stagedExtensionVersion':'0.3.1'}},'0.3.0')
        self.assertEqual(result['state'],'reload extension')
    def test_disconnected_is_not_a_reload_or_ready(self):
        result=assess({'service':'active','browser':{'reachable':True,'connected':False,'extensionVersion':'0.3.1'}},'0.3.1')
        self.assertEqual(result['state'],'disconnected')
    def test_generic_worker_without_staged_version_uses_explicit_requirement(self):
        result=assess({'service':'active','browser':{'reachable':True,'connected':True,'extensionVersion':'0.3.1'}},'0.3.1')
        self.assertEqual(result['state'],'ready');self.assertIsNone(result['stagedVersion'])
