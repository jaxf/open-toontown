import ast
import types
import unittest
from pathlib import Path
from toontown.expansion import ExpansionGlobals as E
from toontown.expansion.AdminPolicy import validate_request

ROOT = Path(__file__).resolve().parents[1]


def load_zone_functions():
    # Execute the actual routing functions without bootstrapping the legacy
    # game engine; only their global constants are supplied by this harness.
    tree = ast.parse((ROOT/'toontown/hood/ZoneUtil.py').read_text())
    body = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    namespace = dict(ExpansionGlobals=E, tutorialDict=None, DynamicZonesBegin=65000,
                     DynamicZonesEnd=1 << 20, WelcomeValleyToken=0,
                     WelcomeValleyBegin=22000, WelcomeValleyEnd=61000,
                     ToontownCentral=2000, GoofySpeedway=8000,
                     SellbotHQ=11000, CashbotHQ=12000, LawbotHQ=13000, BossbotHQ=10000)
    exec(compile(ast.Module(body=body, type_ignores=[]), 'ZoneUtil.py', 'exec'), namespace)
    return namespace


class WorldTests(unittest.TestCase):
    def test_every_tunnel_has_a_return(self):
        zones = E.ALL_ZONES | set(E.SOURCE_GATES)
        for zone in zones:
            self.assertEqual(len(E.connections(zone)), len(E.gate_transforms(zone)))
            for target in E.connections(zone):
                self.assertIn(zone, E.connections(target), (zone, target))

    def test_all_new_locations_reachable_from_existing_world(self):
        reached=set(E.SOURCE_GATES)
        pending=list(reached)
        while pending:
            for target in E.connections(pending.pop()):
                if target not in reached:
                    reached.add(target)
                    pending.append(target)
        self.assertTrue(E.ALL_ZONES <= reached)
        self.assertEqual(len(E.NEIGHBORHOODS),5)
        self.assertEqual(len(E.STREETS),8)

    def test_static_ids_do_not_overlap_instances_or_welcome_valley(self):
        for zone in E.ALL_ZONES:
            self.assertLess(zone, E.DYNAMIC_ZONE_BEGIN)
            self.assertFalse(22000 <= zone < 61000)
            self.assertLess(zone,65536)  # persisted teleport-access uint16
        for zone,(_,hood,_,_) in E.STREETS.items():
            self.assertEqual(zone-zone%1000,hood)

    def test_actual_routing_and_legacy_boundaries(self):
        f=load_zone_functions()
        for zone in E.ALL_ZONES:
            self.assertEqual(f['getLoaderName'](zone),'safeZoneLoader')
            self.assertEqual(f['getWhereName'](zone,True),'playground')
            self.assertFalse(f['isDynamicZone'](zone))
            self.assertFalse(f['isWelcomeValley'](zone))
            self.assertEqual(f['getCanonicalZoneId'](zone),zone)
            self.assertEqual(f['getHoodId'](zone),E.hood_id(zone))
        self.assertTrue(f['isDynamicZone'](65000))
        self.assertEqual(f['getCanonicalZoneId'](22000),2000)
        self.assertEqual(f['getCanonicalZoneId'](23000),8000)
        self.assertEqual(f['getLoaderName'](2101),'townLoader')
        self.assertEqual(f['getWhereName'](2101,True),'street')
        self.assertEqual(f['getLoaderName'](11000),'cogHQLoader')

    def test_map_matches_physical_connections(self):
        self.assertEqual(set(E.MAP_POSITIONS),set(E.NEIGHBORHOODS)|set(E.SOURCE_GATES))
        for _,_,start,end in E.STREETS.values():
            self.assertIn(start,E.MAP_POSITIONS)
            self.assertIn(end,E.MAP_POSITIONS)

    def test_permission_and_destination_allowlist(self):
        for rank in (0,100,200,299):
            toon=types.SimpleNamespace(getAccessLevel=lambda r=rank:r)
            self.assertIsNotNone(validate_request(toon,'max',0))
            self.assertIsNotNone(validate_request(toon,'teleport',E.ACORN))
        admin=types.SimpleNamespace(getAccessLevel=lambda:300)
        self.assertIsNone(validate_request(admin,'max',0))
        for zone in E.destinations():
            self.assertIsNone(validate_request(admin,'teleport',zone))
        for zone in (0,1,15000,16000,22000,65000,999999):
            self.assertIsNotNone(validate_request(admin,'teleport',zone))
        self.assertIsNotNone(validate_request(admin,'setRank',400))
        self.assertIsNotNone(validate_request(None,'max',0))


if __name__ == '__main__':
    unittest.main()
