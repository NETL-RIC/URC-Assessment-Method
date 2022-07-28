from PyQt5.QtGui import QColor
from .._support import GradientRecord
import glm

def vecToQColor(c):

    return QColor.fromRgbF(c[0],c[1],c[2],c[3])

def QColorToVec(c):

    return glm.vec4(c.redF(),c.greenF(),c.blueF(),c.alphaF())

def GradRecToStops(gr):

    return [(wt,vecToQColor(color)) for wt,color in gr]

def StopsToGradRec(stps):

    ret = GradientRecord()
    for wt,color in stps:
        ret.addColorAnchor(wt,QColorToVec(color))
    return ret
