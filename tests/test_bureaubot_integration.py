"""Server/data regressions; run without the optional OTP native extension.

Compile production methods into narrow harnesses where their network bases
cannot load. Test behavior, not duplicated implementations.
"""
import ast
from pathlib import Path
import random
from types import SimpleNamespace
import unittest
from toontown.suit import SuitDNA, BureaubotGlobals as BG
from toontown.shtiker.CogPageGlobals import *
from toontown.shtiker.CogPageManagerAI import CogPageManagerAI
from toontown.suit.SuitInvasionManagerAI import SuitInvasionManagerAI

ROOT=Path(__file__).resolve().parents[1]


def production_methods(path, class_name, names, namespace):
    tree=ast.parse((ROOT/path).read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name)
    methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(methods)==len(names)
    exec(compile(ast.Module(body=methods,type_ignores=[]),str(path),'exec'),namespace)
    return {name:namespace[name] for name in names}


def battle_catalog():
    path=ROOT/'toontown/battle/SuitBattleGlobals.py'
    tree=ast.parse(path.read_text())
    tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and n.module=='BattleBase')]
    ns={'__name__':'toontown.battle.SuitBattleGlobals', 'ATK_TGT_SINGLE':0,'ATK_TGT_GROUP':1,
        'simbase':SimpleNamespace(config=SimpleNamespace(GetString=lambda *_:'random'))}
    exec(compile(tree,str(path),'exec'),ns)
    return SimpleNamespace(**ns)


class ToonHarness:
    doId=7
    def __init__(self):
        self.fields={'CogStatus':[1]*32,'CogCount':[0]*32,'CogRadar':[0]*4,
                     'BuildingRadar':[0]*4,'CogSummonsEarned':[0]*32}
    def __getattr__(self,name):
        if name.startswith('get'):
            return lambda:list(self.fields[name[3:]])
        if name.startswith('b_set'):
            return lambda value:self.fields.__setitem__(name[5:],list(value))
        raise AttributeError(name)


class DataAndBattleTests(unittest.TestCase):
    def test_dna_roundtrip_and_legacy_indices(self):
        self.assertEqual(SuitDNA.suitHeadTypes[:8],['f','p','ym','mm','ds','hh','cr','tbc'])
        self.assertEqual(SuitDNA.suitHeadTypes[24:32],['cc','tm','nd','gh','ms','tf','m','mh'])
        for rank,code in enumerate(BG.CODES,1):
            dna=SuitDNA.SuitDNA();dna.newSuit(code)
            decoded=SuitDNA.SuitDNA(dna.makeNetString())
            self.assertEqual((decoded.name,decoded.dept,decoded.body),(code,'u',BG.BY_CODE[code][2]))
            randomDNA=SuitDNA.SuitDNA();randomDNA.newSuitRandom(rank,'u')
            self.assertEqual(randomDNA.name,code)
        self.assertEqual(SuitDNA.hqDepts,['c','l','m','s'])

    def test_weighted_scaled_moves_and_existing_assets(self):
        battle=battle_catalog()
        movies=ast.parse((ROOT/'toontown/battle/MovieSuitAttacks.py').read_text())
        dispatch=next(n for n in movies.body if isinstance(n,ast.FunctionDef) and n.name=='doSuitAttack')
        implemented=set()
        for branch in ast.walk(dispatch):
            if isinstance(branch,ast.If) and isinstance(branch.test,ast.Compare):
                constant=branch.test.comparators[0]
                if isinstance(constant,ast.Name):
                    calls=[n.func.id for statement in branch.body for n in ast.walk(statement)
                           if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
                    if 'doDefault' not in calls:
                        implemented.add(getattr(battle,constant.id))
        for code in BG.CODES:
            body=BG.BY_CODE[code][2]
            animations={name:(file,phase) for name,file,phase in BG.ANIMATIONS[body]}
            stats=battle.SuitAttributes[code]
            self.assertEqual(len(stats['attacks']),3)
            for level in range(5):
                self.assertEqual(sum(a[3][level] for a in stats['attacks']),100)
                selected={battle.pickSuitAttack(stats['attacks'],level) for _ in range(300)}
                self.assertEqual(selected,{0,1,2})
                for i in selected:
                    move=battle.getSuitAttack(code,level,i)
                    self.assertIn(move['id'],implemented)
                    file,phase=animations[move['animName']]
                    self.assertTrue((ROOT/('resources/phase_%s/models/char/suit%s-%s.bam' %
                                          (phase,body.upper(),file))).exists())
                    self.assertGreater(move['hp'],0)
            for move in stats['attacks']:
                self.assertEqual(sorted(move[1]),list(move[1]))

    def test_every_street_has_normalized_bureau_chance(self):
        tree=ast.parse((ROOT/'toontown/suit/SuitPlannerBase.py').read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        rows=ast.literal_eval(next(n.value for n in cls.body if isinstance(n,ast.Assign)
            and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='SuitHoodInfo'))
        from toontown.expansion.CogPatrols import hood_rows
        rows+=hood_rows()
        for row in rows:
            weights=BG.street_weights(row[8])
            self.assertEqual(sum(weights),100)
            self.assertEqual(weights[4],20)
            for old,new in zip(row[8],weights):
                if old==0:self.assertEqual(new,0)


    def test_live_planner_weights_spawn_ranks_and_takeovers(self):
        from direct.directnotify import DirectNotifyGlobal
        tree=ast.parse((ROOT/'toontown/suit/DistributedSuitPlannerAI.py').read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        cls.bases=[]
        building=ast.parse((ROOT/'toontown/building/SuitBuildingGlobals.py').read_text())
        info=ast.literal_eval(next(n.value for n in building.body if isinstance(n,ast.Assign)
            and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='SuitBuildingInfo'))
        config=SimpleNamespace(GetFloat=lambda name,value:value,GetBool=lambda name,value:value,
                               GetString=lambda name,value:value)
        ns={'__name__':'toontown.suit.DistributedSuitPlannerAI','__package__':'toontown.suit','config':config,
            'simbase':SimpleNamespace(config=config),'SuitDNA':SuitDNA,'random':random,
            'DirectNotifyGlobal':DirectNotifyGlobal,'SuitBattleGlobals':battle_catalog(),
            'SuitBuildingGlobals':SimpleNamespace(SuitBuildingInfo=info)}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),'live-planner','exec'),ns)
        plannerClass=ns['DistributedSuitPlannerAI']
        self.assertGreater(plannerClass.TOTAL_BWEIGHT_PER_TRACK[4],0)
        self.assertTrue(all(len(row[8])==5 for row in plannerClass.SuitHoodInfo))
        sp=plannerClass.__new__(plannerClass)
        sp.hoodInfoIdx=0
        ranks={sp.pickLevelTypeAndTrack(10,track='u')[1] for _ in range(200)}
        self.assertEqual(ranks,{6,7,8})
        row=list(plannerClass.SuitHoodInfo[0])
        row[8]=(0,0,0,0,100)
        sp.SuitHoodInfo=[row]
        sp.TOTAL_BWEIGHT_PER_TRACK=[0,0,0,0,100]
        sp.TOTAL_BWEIGHT_PER_HEIGHT=[1,0,0,0,0]
        sp.TOTAL_BWEIGHT=row[5]
        sp.pendingBuildingTracks=[];sp.pendingBuildingHeights=[]
        sp.targetNumCogdos=0;sp.targetNumSuitBuildings=0
        sp.frontdoorPointList=[1,2,3];sp.suitList=[]
        sp.buildingMgr=None
        sp.air=SimpleNamespace(suitPlanners={2100:sp})
        sp.assignSuitBuildings(1)
        self.assertEqual(sp.pendingBuildingTracks,['u'])
        self.assertEqual(sp.targetNumSuitBuildings,1)
        # Saturated streets must terminate instead of leaving stale bureau weight.
        sp.targetNumSuitBuildings=3
        sp.assignSuitBuildings(1)
        self.assertEqual(sp.targetNumSuitBuildings,3)


class GalleryTests(unittest.TestCase):
    def test_migrate_both_avatar_setters_without_resetting(self):
        fields={'CogStatus':('cogs',1,40),'CogCount':('cogCounts',0,40),
                'CogRadar':('cogRadar',0,5),'BuildingRadar':('buildingRadar',0,5),
                'CogSummonsEarned':('cogSummonsEarned',0,40)}
        for filename in ('DistributedToon','DistributedToonAI'):
            ns={'SuitDNA':SuitDNA,'pad_collection':pad_collection}
            methods=production_methods('toontown/toon/'+filename+'.py',filename,
                        ['set'+field for field in fields],ns)
            cls=type('Avatar',(),methods)
            avatar=cls();avatar.notify=SimpleNamespace(debug=lambda *a:None)
            for field,(member,default,size) in fields.items():
                old=[3]*(size-8 if size==40 else 4)
                getattr(avatar,'set'+field)(old)
                self.assertEqual(getattr(avatar,member),old+[default]*(size-len(old)))
                self.assertEqual(len(old),32 if size==40 else 4)

    def test_credit_unlocks_radars_and_one_consumable_summon_set(self):
        toon=ToonHarness();manager=CogPageManagerAI(None)
        manager.toonEncounteredCogs(toon,[{'type':'ps','activeToons':[7]}],2100)
        self.assertEqual(toon.getCogStatus()[32],COG_BATTLED)
        for rank,code in enumerate(BG.CODES):
            record={'type':code,'activeToons':[7]}
            manager.toonKilledCogs(toon,[record]*COG_QUOTAS[1][rank],2100)
        self.assertEqual(toon.getCogStatus()[32:],[COG_COMPLETE2]*8)
        self.assertEqual(toon.getCogCount()[32:],list(COG_QUOTAS[1]))
        self.assertEqual(toon.getCogSummonsEarned()[32:],[7]*8)
        self.assertEqual(toon.getCogRadar(),[0,0,0,0,1])
        self.assertEqual(toon.getBuildingRadar(),[0,0,0,0,1])
        toon.fields['CogSummonsEarned'][32]=0
        manager.toonKilledCogs(toon,[{'type':'ps','activeToons':[7]}],2100)
        self.assertEqual(toon.getCogSummonsEarned()[32],0)
        self.assertEqual(toon.getCogCount()[32],45)

    def test_no_credit_for_other_toons_virtuals_or_bosses(self):
        toon=ToonHarness();manager=CogPageManagerAI(None)
        invalid=[{'type':'ps','activeToons':[8]},
                 {'type':'ps','activeToons':[7],'isVirtual':True},
                 {'type':None,'activeToons':[7],'isVP':True}]
        manager.toonKilledCogs(toon,invalid,2100)
        manager.toonEncounteredCogs(toon,invalid,2100)
        self.assertEqual(toon.getCogStatus(),[1]*32)
        self.assertEqual(toon.getCogCount(),[0]*32)

    def test_summon_dispatch_and_consumption(self):
        names=['reqCogSummons','hasCogSummons','removeCogSummonsEarned']
        ns={'SuitDNA':SuitDNA,'ZoneUtil':SimpleNamespace(isWelcomeValley=lambda zone:False),'ToontownGlobals':SimpleNamespace(WelcomeValleyBegin=22000,WelcomeValleyEnd=61000)}
        methods=production_methods('toontown/toon/DistributedToonAI.py','DistributedToonAI',names,ns)
        toon=type('Summoner',(ToonHarness,),methods)()
        toon.fields['CogSummonsEarned']=[7]*40
        toon.notify=SimpleNamespace(warning=lambda *a:None)
        toon.zoneId=2100;toon.doId=7
        toon.air=SimpleNamespace(writeServerEvent=lambda *a:None,getAvatarIdFromSender=lambda:7)
        replies=[];calls=[]
        toon.sendUpdate=lambda *args:replies.append(args)
        for method in ('doSummonSingleCog','doBuildingTakeover','doCogInvasion'):
            setattr(toon,method,lambda index,m=method:(calls.append((m,index)) or ['success',index,0]))
        for kind in ('single','building','invasion'):
            toon.reqCogSummons(kind,39)
        self.assertEqual(len(calls),3)
        self.assertEqual(toon.getCogSummonsEarned()[39],0)
        toon.reqCogSummons('single',39)
        toon.reqCogSummons('single',-1)
        toon.reqCogSummons('single',40)
        self.assertEqual(len(calls),3)


class InvasionTests(unittest.TestCase):
    def test_start_busy_progress_bulletin_and_completion(self):
        messages=[]
        news=SimpleNamespace(sendUpdate=lambda *a:messages.append(a),
            sendUpdateToAvatarId=lambda *a:messages.append(a))
        manager=SuitInvasionManagerAI(SimpleNamespace(newsManager=news))
        try:
            self.assertFalse(manager.startInvasion('missing',2))
            self.assertTrue(manager.startInvasion('hho',2))
            self.assertFalse(manager.startInvasion('f',2))
            self.assertEqual(manager.getInvadingCog(),('hho',0))
            manager.sendCurrentInvasion(SimpleNamespace(doId=7))
            manager.cogDefeated('f');self.assertEqual(manager.numRemaining,2)
            manager.cogDefeated('hho');self.assertTrue(manager.getInvading())
            manager.cogDefeated('hho');self.assertFalse(manager.getInvading())
            self.assertEqual(messages[-1][1][0],manager.END)
            self.assertTrue(manager.startInvasion('ps',20))
            manager._timeout(SimpleNamespace(done='done'))
            self.assertFalse(manager.getInvading())
        finally:manager.delete()


if __name__=='__main__':unittest.main()
