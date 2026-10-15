"""Exercise the actual AI RPC handler with fake transport/avatar state."""
import ast
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from test_expansion import load_zone_functions
from toontown.expansion import ExpansionGlobals as E


class AdminEndpointTests(unittest.TestCase):
    def setUp(self):
        source=Path('toontown/spellbook/ToontownMagicWordManagerAI.py').read_text()
        tree=ast.parse(source)
        klass=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='requestAdminAction')
        harness=ast.ClassDef(name='Harness',bases=[],keywords=[],body=[method],decorator_list=[])
        module=ast.fix_missing_locations(ast.Module(body=[harness],type_ignores=[]))
        self.maxed=[]
        word=types.SimpleNamespace(handleWord=lambda toon,avId,target:self.maxed.append(avId) or 'Maxed.')
        namespace={'MagicWordIndex':{'max':{'class':word}}}
        exec(compile(module,'admin-handler','exec'),namespace)
        self.handler=namespace['Harness']()
        self.responses=[];self.teleports=[];self.events=[];self.visited=[];self.access=[]
        self.rank=300
        self.toon=types.SimpleNamespace(getAccessLevel=lambda:self.rank,
            b_setHoodsVisited=lambda h:self.visited.extend(h),
            b_setTeleportAccess=lambda h:self.access.extend(h))
        self.handler.air=types.SimpleNamespace(getAvatarIdFromSender=lambda:42,
            doId2do={42:self.toon},tutorialManager=types.SimpleNamespace(playerDict={}),
            writeServerEvent=lambda *args:self.events.append(args))
        self.handler.generateResponse=lambda *args,**kw:self.responses.append((args,kw))
        self.handler.sendTeleportResponse=lambda *args:self.teleports.append(args)
        self.modules=patch.dict('sys.modules',{
            'toontown.hood.ZoneUtil':types.SimpleNamespace(**load_zone_functions()),
            'toontown.toonbase.ToontownGlobals':types.SimpleNamespace(HoodsForTeleportAll=tuple(E.NEIGHBORHOODS))})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def test_forged_regular_player_request_cannot_mutate_or_teleport(self):
        self.rank=0
        self.handler.requestAdminAction('max',0)
        self.handler.requestAdminAction('teleport',E.ACORN)
        self.assertEqual(self.maxed,[])
        self.assertEqual(self.teleports,[])
        self.assertEqual(self.access,[])
        self.assertEqual(len(self.responses),2)

    def test_max_is_self_only_and_grants_travel(self):
        self.handler.requestAdminAction('max',0)
        self.assertEqual(self.maxed,[42])
        self.assertEqual(set(self.access),set(E.NEIGHBORHOODS))
        self.assertEqual(self.visited,self.access)
        self.assertEqual(len(self.events),1)

    def test_invalid_or_tutorial_destinations_are_rejected(self):
        self.handler.requestAdminAction('teleport',65000)
        self.handler.requestAdminAction('teleport',15000)
        self.assertEqual(self.teleports,[])
        self.handler.air.tutorialManager.playerDict[42]={}
        self.handler.requestAdminAction('max',0)
        self.assertEqual(self.maxed,[])

    def test_expansion_and_stock_street_arrivals(self):
        self.handler.requestAdminAction('teleport',19100)
        self.assertEqual(self.teleports[-1],(42,'safeZoneLoader','playground','teleportIn',19000,19100,0))
        self.toon._lastAdminAction=-10
        self.handler.requestAdminAction('teleport',2132)
        self.assertEqual(self.teleports[-1],(42,'townLoader','street','adminStreet',2000,2132,0))

    def test_repeated_clicks_are_rate_limited(self):
        self.handler.requestAdminAction('max',0)
        self.handler.requestAdminAction('max',0)
        self.assertEqual(self.maxed,[42])


if __name__ == '__main__':
    unittest.main()
