""" Classes and functions for rendering text using the Freetype library and OpenGL
Author: P. Wingo

some useful links:
    * https://en.wikibooks.org/wiki/OpenGL_Programming/Modern_OpenGL_Tutorial_Text_Rendering_02
    * https://learnopengl.com/In-Practice/Text-Rendering
    * http://www.opengl-tutorial.org/intermediate-tutorials/billboards-particles/billboards/
"""
import os.path
from ctypes import c_void_p

import numpy as np
from OpenGL.GL import *


class AtlasEntry(object):
    """Convenience container for storing glyph attributes suitable for drawing.

    Most freetype examples (particularly OpenGL rendering) will utilize a similar structure.

    Args:
        glyph: The freetype glyph to document.
        offs: The pixel x-offset into the atlas texture storing the rendered glyph.

    Attributes:
        ax: Horizontal advance step, in pixels.
        ay: Vertical advance step, in pixels.
        bw: The glyph's bitmap width, in pixels.
        bh: The glyph's bitmap height, in pixels.
        bl: The glyph's left boundary offset, in pixels.
        bt: The glyph's top boundary offset, in pixels.
        tx: The horizontal/x offset into the atlas texture, in pixels.

    """
    def __init__(self,glyph,xOffs,yOffs=0):

        # NOTE: The freetype measurement unit is 1/64 pixel, and is integer.
        #       since 64 is 2^6, we can perform a bit rightshift (>>) to convert to whole pixels.
        #       we could instead integer divide (//) by 64, but bitshifting is a MUCH faster operation, when dealing
        #       with powers of 2, and most freetype examples you see will use bitshifting left and right to convert to
        #       and from 1/64, respectively

        self.ax = glyph.advance.x >> 6  # advance x
        self.ay = glyph.advance.y >> 6  # advance y

        # bitmap measurements are in full pixels.
        self.bw = glyph.bitmap.width # atlasTex Width
        self.bh = glyph.bitmap.rows # atlasTex rows

        self.bl = glyph.bitmap_left # atlasTex left
        self.bt = glyph.bitmap_top # atlasTex top

        self.tx = xOffs # glyph offset in atlas texture
        self.ty = yOffs  # glyph offset in atlas texture


class StringEntry(object):
    """Container for storing a string and some rendering information.

    Args:
        txt: The string to store; note that tabs will be converted to spaces.
        anchor: The point which "anchors" the string in Worldspace coordinates. The value should be a container with
                3 float values, corresponding to (x,y,z).
        color: The color to use for rendering the text; defaults to opaque black. The value should be a container with
               3 float values bounded to the range [0,1], corresponding to (red,green,blue,alpha).
        h_justify: String representing the horizontal justification relative to the anchor point. Valid values are:
                  * 'center': The string centers horizontally on the anchor point. This is the default value.
                  * 'left': The string positions itself so the anchor is to the left.
                  * 'right': The string positions itself so the anchor is to the right.
        v_justify: String representing the vertical justification relative to the anchor point. Valid values are:
                  * 'center': The string centers vertically on the anchor point. This is the default value.
                  * 'top': The string positions itself so the anchor is on top.
                  * 'bottom': The string positions itself so the anchor is below the bottom.
        tabspacing: The number of spaces to substitute for tab characters. The default is 4.

    Attributes:
        txt: The string to be rendered, with tab substitution applied.
        anchor: The (x,y,z) anchor point in worldspace.
        color: The color to apply to the string as (red,green,blue,alpha).
        h_justify: The string's horizontal justification.
        v_justify: The string's vertical justification.
    """

    def __init__(self,txt='',anchor=(0.,0.,0.),color=(0.,0.,0.,1.),h_justify="center",v_justify="center",tabspacing=4):

        self.txt = txt.replace('\t',' '*tabspacing)
        self.anchor = tuple(anchor)
        if len(self.anchor)<3:
            self.anchor=(*self.anchor,*([0.]*(3-len(self.anchor))))
        self.color = tuple(color)
        self.h_justify = h_justify.lower()
        self.v_justify = v_justify.lower()
        self.tex=0

    def __len__(self):
        return len(self.txt)

    @property
    def validCount(self):
        """int: The total number of characters in the string, minus the '\r' and '\n' control characters."""
        return len([c for c in self.txt if c not in '\r\n'])

class TxtRenderer(object):
    """Manages rendering text glyphs in freetype, and copying the results to OpenGL containers suitable for rendering

    Args:
        fontFile: Path to the font file to load. This can be any supported by freetype, as listed
                 [here](https://freetype.org/freetype2/docs/index.html)
        fontSize: The point size for the rendered font; defaults to 64.

    Keyword Args:
        charset: A string (or other iterable container of chars) to include in the atlas. By default, all ASCII characters
                 from 32 through 127 are included, which includes english alphanumerics, and most punctuation. Use a
                 custom set if you need chars outside of this range, or if you are using just a few chars and want to
                 keep memory requirements down. 127 (delete) is always included as a default `None` char.
    """

    # add some padding to avoid bleedover in atlas when scaling is applied.
    # since native interpolation only includes one neighbor, a pixel width
    # of one should be fine for now.
    MAX_WIDTH=512

    @staticmethod
    def PrepTextBuffer(vao,buff):
        """Prepare an OpenGL VAO and VBO for use with text rendering. It's possible that we may want to organize strings
        into different VAOs and/or VBOs, so keep this as an external behavior.

        Args:
            vao: The index of the VAO to modify.
            buff: The index of the array VBO which will be updated.

        """
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER,buff)

        # For rendering, we'll be using interleaved array, which is where different attributes for a vertex are
        # grouped together. This requires us to tell OpenGL how big a total record is (stride), and where the fields
        # are in the record (offset).

        # The total number of bytes. Each field will be a float32 (4 bytes), and there are 11 total fields.
        recBytes = int(4 * 11)

        # Let OpenGL know we'll be using 4 fields per vertex; these indices are referenced in the shader pipeline
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)
        glEnableVertexAttribArray(2)
        glEnableVertexAttribArray(3)
        # for each attribute. Describe the count, stride, and offset.
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, recBytes, c_void_p(0))   # x,y offset in screen pixels.
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, recBytes, c_void_p(8))   # s,t coordinates into atlas texture.
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, recBytes, c_void_p(16))  # x,y,z anchor point for string in worldspace
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, recBytes, c_void_p(28))  # r,g,b,a color for rendering text.

        # glBindBuffer(GL_ARRAY_BUFFER,0)
        glBindVertexArray(0)

    def __init__(self,fontFile,fontSize=64,**kwargs):

        if not os.path.exists(fontFile):
            raise FileNotFoundError(f"Font file '{fontFile}' does not appear to exist")

        # import here so import is optional
        import freetype

        self._atlas = {}

        # grab the face, which is basically the Font
        self._face = freetype.Face(fontFile)
        self._face.set_char_size(fontSize << 6)
        self._ptSize=fontSize
        self._fontPath=fontFile

        self._width = 0
        self._height = 0
        wd=0
        ht=0
        self._initialized=False

        # grab the ordinal values for the charset
        # by default, just grab the lower 128 minus the 32 control characters
        ords = range(32,128)
        if 'charset' in kwargs:
            cSet=set(kwargs['charset'])
            # always ensure we have endchar /127
            cSet.add(chr(127))
            ords = [ord(c) for c in cSet]

        self._ords = ords

        # find the width, height needed in pixels, including padding, for storing all the glyphs in an OpenGL texture.
        for i in ords:
            self._face.load_char(i)
            g = self._face.glyph

            if wd+g.bitmap.width>=TxtRenderer.MAX_WIDTH:
                self._height+=ht
                self._width=TxtRenderer.MAX_WIDTH
                ht=0
                wd=0
            wd+=g.bitmap.width

            ht = max(ht,g.bitmap.rows)
        self._height+=ht
        self._width=max(wd,self._width)

        # the rest of the initialization will take place in openGL

    def initGL(self,activeTex):
        """ Initialize components that require an OpenGL context.

        Args:
            activeTex: The texture slot to use for manipulation (such as GL_TEXTURE0).
        """

        if not self._initialized:

            # Target the texture object for operations.
            self.atlasTex=glGenTextures(1)
            glActiveTexture(activeTex)
            glBindTexture(GL_TEXTURE_2D, self.atlasTex)

            # For atlases, you don't want byte/word alignment, as it may break the lookup.
            glPixelStorei(GL_UNPACK_ALIGNMENT,1)

            # allocate texture space in GPU memory, and set all values to zero.
            # The atlas will be an alpha map, so we only need a single channel.
            glTexImage2D(GL_TEXTURE_2D,0,GL_RED,self._width,self._height,0, GL_RED,GL_UNSIGNED_BYTE,np.zeros([(self._width)*self._height],dtype=np.uint8))

            # build the atlas.
            x = 0
            y= 0
            ht =0
            for i in self._ords:
                if i in (10,13):
                    # skip newline, carriage return
                    continue
                self._face.load_char(i)
                g = self._face.glyph

                # Add entry for CPU atlas.

                buff = np.array(g.bitmap.buffer,dtype=np.uint8)

                # Copy the rendered glyph to the atlas texture in GPU memory
                if x+g.bitmap.width >TxtRenderer.MAX_WIDTH:
                    x=0
                    y+=ht
                    ht=0
                self._atlas[chr(i)] = AtlasEntry(g, x, y)
                glTexSubImage2D(GL_TEXTURE_2D, 0,x,y,g.bitmap.width,g.bitmap.rows, GL_RED,GL_UNSIGNED_BYTE,buff)
                ht = max(ht, g.bitmap.rows)
                x += g.bitmap.width

            # Use GL_LINEAR here for better upscaling when scale factor is used.
            # Note that if no scaling is used and glyphs are rendered relative to screen res, the GL_NEAREST is the
            # better choice
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

            self._initialized=True

    def loadStrings(self,vao,buff,strs,sx=1,sy=1):
        """Create renderable versions of a collection of strings. Each character will be billboarded to a quad (two
           triangles) with its texture coordinates pinning the correct glyph to be rendered.

        Args:
            vao: The VAO which will be used to render the supplied strings.
            buff: The array VBO which will be used to store the vertices and their attributes.
            strs: An iterable container of `StringEntry` objects which contain a string and rendering information.
            sx: An x-scaling factor to apply; defaults to 1.
            sy: A y-scaling factor to apply; defaults to 1.

        Returns:
            int: The total number of vertices created and uploaded to the VBO. This value should be suitable for rendering
            with the `GL_TRIANGLES` mode.
        """

        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER,buff)

        # find combined lengths
        chrCount=0
        for se in strs:
            chrCount+=se.validCount

        # create an empty container for storing 11 values for 6 vertices for each character in the strings.
        verts = np.empty([chrCount,6,11],dtype=np.float32)
        cp = 0
        # step through each string
        for se in strs:

            # find the dimensions of the bounding box for the string, in pixels.
            xW,xH = self.renderSize(se.txt)

            # apply the appropriate horizontal justification.
            if se.h_justify== 'left':
                xStart = 0
            elif se.h_justify== 'right':
                xStart = -xW
            else: # center
                xStart = -(xW//2)

            # apply the appropriate vertical justification.
            if se.v_justify== 'bottom':
                yStart=0
            elif se.v_justify== 'top':
                yStart=-xH
            else: # center
                yStart = - (xH // 2)

            x= xStart
            y= yStart

            for c in se.txt:

                if c=='\r':
                    continue # skip return carriage
                if c=='\n':
                    # apply newline
                    x = xStart
                    y-= (self._face.size.height >> 8)*sy
                    continue

                # grab the atlas entry for the character, or nochar placeholder if the character isn't present.
                entry = self._atlas.get(c,self._atlas[chr(127)])

                # apply the various offsets, advances, and scalings for the character.
                x2 = x + entry.bl*sx
                y2 = (-y - entry.bt * sy)*-1

                aw = entry.bw
                ah = entry.bh
                tx = entry.tx
                ty = entry.ty
                w = entry.bw * sx
                h = entry.bh * sy

                x+= entry.ax * sx
                y+= entry.ay * sy

                if w == 0 or h == 0:
                    continue

                # Build the four corners of the quad with the information to pass to the GPU.
                p1 = (x2  , y2  , tx     ,ty , *se.anchor[:3],*se.color[:4])
                p2 = (x2+w, y2  , tx + aw,ty , *se.anchor[:3],*se.color[:4])
                p3 = (x2+w, y2-h, tx + aw,ty+ah, *se.anchor[:3],*se.color[:4])
                p4 = (x2  , y2-h, tx     ,ty+ah, *se.anchor[:3],*se.color[:4])

                # Apply the vertices in the order to draw the two triangles for the quad.
                verts[cp]=(p1,p2,p3,p1,p4,p3)
                cp+=1

        # Copy all the vertex information into the VBO in GPU memory.
        glBufferData(GL_ARRAY_BUFFER,verts.nbytes,verts.ravel(),GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER,0)
        glBindVertexArray(0)

        return cp*6

    def renderSize(self,testStr,sx=1,sy=1):
        """Estimate the dimension of the bounding box of a string, in pixels.

        Args:
            testStr: The String to test.
            sx: The x-scaling factor; defaults to 1.
            sy: The y-scaling factor; defaults to 1.

        Returns:
            tuple: A pair of ints corresponding to the width and height of the strings bounding box, in pixels.
        """

        w,h = 0,0
        wMax=0
        h=(self._face.size.height>>6)*sy
        for c in testStr:

            if c=='\r':
                # skip carriage return
                continue

            if c!= '\n':
                entry = self._atlas.get(c, self._atlas[chr(127)])

                w += entry.ax * sx
                wMax=max(w,wMax)
                # h = max(h,entry.bh * sy)
            else:
                # special case; if newline encountered, move to next row
                h+=(self._face.size.height >> 6)*sy
                w=0
        return wMax,h


    def cleanupGL(self):
        """Cleanup any OpenGL resources."""
        glDeleteTextures(1, np.array([self.atlasTex]))

    @property
    def fontPtSize(self):
        """int: The point size of the rendered font."""
        return self._ptSize

    @property
    def fontFilePath(self):
        """str: The path to the font definition file."""
        return self._fontPath

    @property
    def atlasWidth(self):
        """int: The width of the atlas texture, in pixels."""
        return self._width

    @property
    def atlasHeight(self):
        """int: The height of the atlas texture, in pixels."""
        return self._height

