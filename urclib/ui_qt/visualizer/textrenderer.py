
from ctypes import c_void_p

import numpy as np
from OpenGL.GL import *


class AtlasEntry(object):

    def __init__(self,glyph,offs):

        self.ax = glyph.advance.x >> 6
        self.ay = glyph.advance.y >> 6

        self.bw = glyph.bitmap.width
        self.bh = glyph.bitmap.rows

        self.bl = glyph.bitmap_left
        self.bt = glyph.bitmap_top

        self.tx = offs


class TxtRenderer(object):

    @staticmethod
    def PrepTextBuffer(vao,buff):
        glBindVertexArray(vao)
        recBytes = int(4 * 7)
        glBindBuffer(GL_ARRAY_BUFFER, buff)
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, recBytes, c_void_p(0))
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, recBytes, c_void_p(12))
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, recBytes, c_void_p(20))
        glBindVertexArray(0)

    # https://en.wikibooks.org/wiki/OpenGL_Programming/Modern_OpenGL_Tutorial_Text_Rendering_02
    def __init__(self,fontFile,fontSize=18,**kwargs):

        # import here so import is optional
        import freetype

        self._atlas = {}

        self._face = freetype.Face(fontFile)
        self._face.set_char_size(fontSize * 64)  # width,height)

        self._width = 0
        self._height = 0
        self.texName = 0

        ords = range(32,128)
        if 'charset' in kwargs:
            ords = (ord(c) for c in set(kwargs['charset']))
        self._ords = ords
        # for now, just grab the lower 128 minus the 32 control characters
        for i in ords:
            self._face.load_char(i)
            g = self._face.glyph

            self._width+=g.bitmap.width
            self._height = max(self._height,g.bitmap.rows)

        # the rest of the initialization will take place in openGL

    def initGL(self,vao,tex,activeTex):

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

        glBindVertexArray(vao)
        glActiveTexture(activeTex)
        glBindTexture(GL_TEXTURE_2D,tex)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)

        glTexImage2D(GL_TEXTURE_2D,0,GL_RED,self._width,self._height,0, GL_RED,GL_UNSIGNED_BYTE,np.zeros([self._width*self._height],dtype=np.float32))

        x = 0
        for i in self._ords:
            self._face.load_char(i)
            g = self._face.glyph

            self._atlas[chr(i)]= AtlasEntry(g, x ) # could also try just x if using texel fetch with integers, as long as float in shader
            buff = np.array(g.bitmap.buffer,dtype=np.uint8)
            glTexSubImage2D(GL_TEXTURE_2D, 0,x,0,g.bitmap.width,g.bitmap.rows, GL_RED,GL_UNSIGNED_BYTE,buff)

            x += g.bitmap.width

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindVertexArray(0)


    def loadStrings(self,vao,buff,strs,sx=1,sy=1):

        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER,buff)

        # find combined lengths
        chrCount=0
        for _, text,_ in strs:
           chrCount+=len(text)

        verts = np.empty([chrCount,6,7],dtype=np.float32)
        cp = 0
        for pt, text,anchor in strs:

            x,y,z = pt.x,pt.y,pt.z
            for c in text:

                entry = self._atlas.get(c,self._atlas[chr(127)])
                x2 = x + entry.bl*sx
                y2 = (-y - entry.bt * sy)*-1

                aw = entry.bw
                ah = entry.bh
                tx = entry.tx
                w = entry.bw * sx
                h = entry.bh * sy

                x+= entry.ax * sx
                y+= entry.ay * sy

                if w == 0 or h == 0:
                    continue

                p1 = (x2  , y2  , z, tx     ,0,anchor[0],anchor[1] )
                p2 = (x2+w, y2  , z, tx + aw,0,anchor[0],anchor[1] )
                p3 = (x2+w, y2-h, z, tx + aw,ah,anchor[0],anchor[1])
                p4 = (x2  , y2-h, z, tx ,ah,anchor[0],anchor[1])

                verts[cp]=(p1,p2,p3,p1,p4,p3)
                cp+=1

        glBufferData(GL_ARRAY_BUFFER,verts.nbytes,verts.ravel(),GL_STATIC_DRAW)

        return cp*6

    def renderSize(self,testStr,sx=1,sy=1):

        w,h = 0,0
        for c in testStr:

            entry = self._atlas.get(c, self._atlas[chr(127)])

            w += entry.ax * sx

            h = max(h,entry.bh * sy)

        return w,h

    @property
    def atlasWidth(self):
        return self._width

    @property
    def atlasHeight(self):
        return self._height