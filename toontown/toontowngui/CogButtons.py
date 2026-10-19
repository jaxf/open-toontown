"""Standard game button art for battle controls."""
from direct.gui.DirectGui import DirectButton


def fast_forward_button(parent, command):
    gui = loader.loadModel('phase_3/models/gui/quit_button')
    button = DirectButton(parent=parent, relief=None,
        image=tuple(gui.find('**/'+name) for name in
                    ('QuitBtn_UP', 'QuitBtn_DN', 'QuitBtn_RLVR')),
        image_scale=(1.40, 1, 1.05), image3_color=(.65,.65,.65,1),
        text='Fast forward >>', text_scale=.045, text_pos=(0,-.015),
        pos=(-.34,0,.16), command=command)
    gui.removeNode()
    return button
