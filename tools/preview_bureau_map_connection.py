"""Annotated placement proposal over the existing world map; no travel edits."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from panda3d.core import loadPrcFileData, LineSegs, TextNode
loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\n'
    'win-size 2000 1240\naudio-library-name null\nmodel-path resources\n'
    'default-model-extension .bam')
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectFrame, DirectLabel, DGG
from tools.preview_bureaubots import capture
from toontown.expansion.WorldMapData import PINS
from toontown.expansion.ExpansionGlobals import ACORN


def main():
    app = ShowBase()
    app.disableMouse()
    app.setBackgroundColor(.065, .095, .12, 1)
    parent = app.pixel2d
    ink = (.12, .18, .20, 1)
    cream = (.98, .95, .85, 1)
    accent = (1, .65, .20, 1)
    font = app.loader.loadFont('phase_3/models/fonts/CourierBold')

    def label(text, x, y, size=26, color=cream, centered=False):
        return DirectLabel(parent=parent, relief=None, text=text, text_font=font,
            text_scale=size, text_fg=color,
            text_align=TextNode.ACenter if centered else TextNode.ALeft,
            pos=(x, 0, -y))

    def card(x, y, w, h, color):
        return DirectFrame(parent=parent, relief=DGG.FLAT, frameColor=color,
            frameSize=(0, w, -h, 0), pos=(x, 0, -y))

    def picture(path, x, y, w, h):
        return DirectFrame(parent=parent, relief=None,
            image=app.loader.loadTexture(path), image_scale=(w/2, 1, h/2),
            pos=(x+w/2, 0, -y-h/2))

    def line(points, color, width):
        seg = LineSegs(); seg.setColor(*color); seg.setThickness(width)
        seg.moveTo(points[0][0], 0, -points[0][1])
        for x, y in points[1:]: seg.drawTo(x, 0, -y)
        parent.attachNewNode(seg.create())

    label('RECOMMENDED CONNECTION', 35, 57, 36)
    label('Acorn Acreside  >  Gray Cog HQ tunnel  >  Ministry Plaza', 35, 103, 27)
    label('Placement proposal on the current world map', 1965, 102, 20, (.69,.76,.79,1), True).setX(1600)
    card(30, 150, 420, 1030, cream)
    picture('assets/expansion/maps/toontown_world.png', 490, 150, 1480, 987)

    label('BUREAUBOT HQ', 240, 206, 34, ink, True)
    label('Proposed map addition', 240, 244, 22, ink, True)
    picture('docs/previews/bureau-14000-r10-overview.png', 50, 274, 380, 238)
    label('MINISTRY PLAZA', 240, 557, 28, ink, True)
    label('The front door to HQ', 240, 594, 22, ink, True)
    label('Keep the entrance on the', 55, 730, 23, ink)
    label('outer edge of Acorn.', 55, 766, 23, ink)
    label('A winding approach leads', 55, 827, 23, ink)
    label('into the gray Cog tunnel.', 55, 863, 23, ink)
    label('Inside Ministry Plaza:', 55, 951, 23, ink)
    label('Left: Endless Archives', 55, 995, 23, ink)
    label('Right: Approval Works', 55, 1031, 23, ink)
    label('Ahead: future boss door', 55, 1067, 23, ink)
    label('HQ shown as an inset;', 55, 1130, 19, ink)
    label('final map artwork comes later.', 55, 1158, 19, ink)

    x = 490 + PINS[ACORN][0]*1480
    y = 150 + PINS[ACORN][1]*987
    route = [(x-31,y),(610,y),(525,625),(430,625),(430,538)]
    line(route, ink, 15)
    line(route, accent, 8)
    line([(415,557),(430,538),(445,557)], ink, 15)
    line([(415,557),(430,538),(445,557)], accent, 7)
    ring = [(x+29*math.cos(t*math.tau/64), y+29*math.sin(t*math.tau/64)) for t in range(65)]
    line(ring, ink, 15); line(ring, accent, 8)
    card(x-98,y+43,265,49,ink)
    label('ACORN ACRESIDE',x+35,y+77,25,cream,True)
    card(495,760,310,84,ink)
    label('Recommended entrance',650,793,22,cream,True)
    label('along Acorn\'s outer edge',650,824,20,cream,True)
    label('Existing nearby connections: Root Route to Daisy Gardens / Bramble Bend to Hush Hollow',
          500,1173,21)
    label('Proposal only - existing world-map artwork and actual HQ scene render',35,1220,20,(.69,.76,.79,1))
    capture(app,Path('docs/previews/bureau-map-connection-proposal.png'))
    app.destroy()


if __name__ == '__main__':
    main()
