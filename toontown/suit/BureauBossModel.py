"""Director General art, fitted to the original animated Cog boss skeleton."""
from direct.actor.Actor import Actor
from panda3d.core import NodePath, Texture, PNMImage, TextureAttrib
from .BureaubotModels import _prism, _box, _disc, _stroke, _ellipsoid, build_logo

_palettes = {}


def recolor_suit(actor, model_loader):
    # Edit the native atlas in-place in memory, retaining its UVs, painted
    # shadows, cuffs, tie and lapels. Only the green fabric becomes copper.
    torso = actor.getPart('torso')
    head = actor.getPart('head')
    for node in torso.findAllMatches('**/+GeomNode'):
        if head.isAncestorOf(node):
            continue
        for i in range(node.node().getNumGeoms()):
            state=node.node().getGeomState(i)
            attr=state.getAttrib(TextureAttrib)
            if not attr: continue
            newattr=attr
            for stage in attr.getOnStages():
                tex=attr.getOnTexture(stage)
                key=tex.getFullpath().getFullpath() or tex.getName()
                if key not in _palettes:
                    pixels=PNMImage()
                    if not tex.store(pixels): continue
                    for y in range(pixels.getYSize()):
                        for x in range(pixels.getXSize()):
                            r,g,b=pixels.getXel(x,y)
                            if g>r*1.08 and g>b*.99 and g>.008:
                                # Remove the donor's dollar motif in its fabric
                                # atlas region; retain shirt, lapel and cuff art.
                                fabric='cashbotHQ_palette_3cmla_2' in key and (y<128 or x<47 and y<190)
                                v=(.62+.08*(1-y/128)) if fabric else min(.85,g*1.65)
                                stripe=.72 if x%12<2 else 1
                                pixels.setXel(x,y,v*stripe,v*.46*stripe,v*.19*stripe)
                    out=Texture('director-copper-'+tex.getName());out.load(pixels)
                    out.setMinfilter(Texture.FTLinearMipmapLinear)
                    _palettes[key]=out
                newattr=newattr.addOnStage(stage,_palettes[key])
            node.node().setGeomState(i,state.setAttrib(newattr))


def dress(actor, model_loader):
    from toontown.expansion.BureauHQScene import native,texture
    recolor_suit(actor,model_loader)
    # Keep the animated native head joints while replacing the CFO geometry.
    head=actor.getPart('head')
    for node in head.findAllMatches('**/+GeomNode'):node.hide()
    mount=actor.exposeJoint(None,'head','joint34')
    if mount.isEmpty(): mount=head
    root=mount.attachNewNode('director-filing-head')
    root.setHpr(actor,0,0,0)
    # Head part origin is at the native neck. Use a distinctly faceted cabinet.
    steel=(.62,.66,.65,1);dark=(.11,.14,.14,1);ivory=(.88,.87,.77,1)
    shell=_prism(root,'filing-head',[(-2.7,.3),(2.7,.3),(2.9,4.4),(2.2,6),(-2.1,6.4),(-2.9,4.5)],4.1,steel)
    texture(shell,'phase_4/maps/stomperMetal.jpg',32).setColorScale(2,2,2,1)
    _box(root,'drawer-handle',(0,-2.2,5.65),(1.9,.35,.22),steel)
    for x in (-2.45,2.45):
        _box(root,'cabinet-edge',(x,-2.1,3.1),(.22,.25,4.5),steel)
    for side in (-1,1):
        x=side*1.12
        _ellipsoid(root,'eye',(x,-2.5,4.2),(.92,.32,.62),ivory)
        _disc(root,'pupil',x-side*.15,-2.86,4.16,.19,.29,dark,.08)
        _prism(root,'drawer-brow',[(x-.99,4.65+side*.28),(x+.99,4.65-side*.28),
                                  (x+.99,5.25-side*.28),(x-.99,5.25+side*.28)],.6,dark,y=-2.2)
    _prism(root,'angular-nose',[(-.38,3.55),(.35,3.55),(.25,4.2),(-.22,4.45)],1.8,steel,y=-2.5)
    _prism(root,'hinged-jaw',[(-2.6,.55),(2.5,.55),(2.8,2.55),(-2.6,2.6)],4.4,steel)
    _prism(root,'grin',[(-2.2,2.1),(2.2,2.1),(1.9,.95),(-1.9,1.05)],.2,dark,y=-2.28)
    _prism(root,'teeth',[(-2.05,2.0),(2.06,2.0),(1.8,1.17),(-1.78,1.23)],.06,ivory,y=-2.41)
    for x in (-1.25,-.63,0,.63,1.25):
        _stroke(root,'tooth',[(x,1.2),(x,2.0)],-2.46,.065,dark)
    for i in range(6):
        sheet=_prism(root,'paper-hair',[(-2.6,5.6),(2.4,5.6),(2.2-i*.08,6.5+i*.16),(-2.0,6.65+i*.14)],.18,ivory,y=.4+i*.27)
        texture(sheet,'phase_11/maps/LB_paper_stacks.jpg',8)
    _prism(root,'binder-clip',[(-1.0,6),(1.0,6),(.8,7.1),(-.7,7.1)],1.2,dark,y=.6)
    for y in (.0,1.2):
        _stroke(root,'clip-wire',[(-.7,6.8),(-.9,7.7),(-.55,8.1),(.55,8.1),(.9,7.7),(.7,6.8)],y,.15,steel)
    badge=build_logo();badge.reparentTo(actor.find('**/joint_lifeMeter'))
    badge.setPos(0,-.22,0);badge.setScale(3.6)
    badge.find('**/cast-clipboard').setHpr(0,0,0)
    # Native file drawers dress the existing tread chassis without replacing
    # its curved tracks, hydraulics or original moving skeleton.
    chassis=actor.find('**/joint_axle')
    for x in (-3.5,3.5):
        native(chassis,'phase_11/models/lawbotHQ/LB_filing_cabA',
               (x,-5.9,2.4),size=(5.7,2.2,3.0)).setColorScale(.68,.69,.68,1)
    hand=actor.exposeJoint(None,'torso','joint11').attachNewNode('director-stamp-hand')
    hand.setHpr(actor,0,0,0)
    native(hand,'phase_5/models/props/rubber-stamp',(0,-1,-2),height=5,pitch=90)
    forms=actor.exposeJoint(None,'torso','joint55').attachNewNode('director-forms-hand')
    forms.setHpr(actor,0,0,0)
    for i in range(5):
        sheet=_box(forms,'accordion-form',(0,-.6-i*.24,-i*.55),(2.5,1.7,.08),ivory)
        sheet.setP(32 if i%2 else -32)
        texture(sheet,'phase_11/maps/LB_paper_stacks_top.jpg',4)
    return root


def make_preview(model_loader):
    actor=Actor()
    for part,path in (('legs','phase_9/models/char/bossCog-legs-zero'),
                      ('torso','phase_10/models/char/cashbotBoss-torso-zero'),
                      ('head','phase_10/models/char/cashbotBoss-head-zero')):
        actor.loadModel(path,part)
        actor.loadAnims({a:'phase_9/models/char/bossCog-%s-%s'%(part,a)
                         for a in ('Ff_neutral','Fb_downHit','Fb_DownThrow')},part)
    actor.attach('head','torso','joint34');actor.attach('torso','legs','joint_pelvis')
    treads=model_loader.loadModel('phase_9/models/char/bossCog-treads')
    treads.reparentTo(actor.find('**/joint_axle'))
    actor.pose('Ff_neutral',0);actor.update(force=True)
    dress(actor,model_loader)
    actor.setName('director-general-native-rig')
    return actor
