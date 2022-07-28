""" shaders.py

##########################################################
  "Shaders" are programs that tell a GPU what to do
  at various rendering steps.
  Currently, this module uses shaders for the vertex
  placement, geometry rendering, and fragment coloration
  steps of the rendering pipeline.
##########################################################

Shaders are expecting glsl version 430. Would use 450, but NETL is still providing hardware with
ancient drivers. Eventually may need smarter check to detect on startup, but this should work.

Each of the shaders in this file can be overridden, but don't do this unless
you know what you are doing.
"""

from OpenGL.GL import *



_defines = '''#version 430
#define PI 3.1415926535897932384626433832795
#define HALF_PI  PI*0.5
#define QUART_PI PI*0.25

'''

_pointFns = '''
//Charcodes for point glyphs
#define ORD_CIRCLE   46u  //'.'
#define ORD_DOWNTRI  118u //'v'
#define ORD_UPTRI    94u  //'^'
#define ORD_SQUARE   115u //'s'
#define ORD_DIAMND   100u //'d'
#define ORD_X        120u //'x'
#define ORD_CROSS     43u //'+'

vec4 applySD(vec4 ptColor,float sDist,const float bordThick)
{
    //vec4 outColor =vec4(edgeColor.xyz,0.);
    vec4 outColor =vec4(ptColor.xyz,0.);
    if (sDist<0.)
        outColor= fSelected==0 ? ptColor : selectColor;
    vec4 useEdgeColor = fSelected == 0 ? ptColor : selectColor;
    vec2 gradient = vec2(dFdx(sDist),dFdy(sDist));
    float fromLine = abs(sDist/length(gradient));   
    float lineweight = clamp(bordThick - fromLine,0.f,1.f);

    return mix(outColor,useEdgeColor,lineweight);
}

vec4 pointCircle(vec4 ptColor)
{
    
    const float THICKNESS = ptScale <= 4 ? 0. : 1.;
    const float TEST_RAD = ptScale <= 4 ? 1. : .85;
    
    vec2 signCoord = (2.*gl_PointCoord) - 1.;
    float radius = length(signCoord);
    float sDist = radius - TEST_RAD;
    
    return applySD(ptColor,sDist, THICKNESS);
    
}

vec4 pointSquare(vec4 ptColor)
{
    //todo add border
    return fSelected==0 ? ptColor : selectColor;
}

vec4 pointDiamond(vec4 ptColor)
{
    const float THICKNESS = ptScale <= 4 ? 0. : 1.;
    vec2 adj = (2.*gl_PointCoord.xy) - 1.0;
    float sDist= (abs(adj.x)+abs(adj.y))-1.;
    
    return applySD(ptColor,sDist, THICKNESS);
}

vec4 pointX(vec4 ptColor)
{
    const float THICKNESS = ptScale <= 4 ? 0. : 1.;
    vec2 adj = (2.*gl_PointCoord.xy) - 1.0;

    float sDist= abs(abs(adj.x)-abs(adj.y))-0.2;
//    if(sDist>=0)
//        discard;
    return applySD(ptColor,sDist, THICKNESS);
}

vec4 pointCross(vec4 ptColor)
{
    const float THICKNESS = ptScale <= 4 ? 0. : 1.;
    vec2 adj = (2.*gl_PointCoord.xy) - 1.0;
    float trg =min(abs(adj.x),abs(adj.y));
    
    float sDist= trg-0.2;
    if(sDist>=0)
        discard;
    return ptColor;
//    return applySD(ptColor,sDist, THICKNESS);

}

vec4 pointTriangle(vec4 ptColor, bool pointDown)
{
    const float THICKNESS = ptScale <= 4 ? 0. : 1.;
    vec2 adj = (2.*gl_PointCoord.xy) - 1.0;
    float height=gl_PointCoord.y;
    if (pointDown)
        height = 1.-height;
    float sDist= abs(adj.x)-height;
    
    return applySD(ptColor,sDist, THICKNESS);
}

vec4 doPoint(vec4 ptColor,uint typeCode)
{
    vec4 outColor;
    switch(typeCode)
    {
    case ORD_DOWNTRI:
        outColor = pointTriangle(ptColor,true);
        break;
    case ORD_UPTRI:
        outColor = pointTriangle(ptColor,false);
        break;
    case ORD_SQUARE:
        outColor = pointSquare(ptColor);
        break;
    case ORD_DIAMND:
        outColor = pointDiamond(ptColor);
        break;
    case ORD_X:
        outColor = pointX(ptColor);
        break;
    case ORD_CROSS:
        outColor = pointCross(ptColor);
        break;
    case ORD_CIRCLE:
    default:
        outColor=pointCircle(ptColor);
    };
    return outColor;
}
'''

# <editor-fold desc="~~~ Vertex Shaders ~~~">
passthru_vert = _defines + '''

layout (location=0) in vec4 pos;
uniform mat4 mvpMat=mat4(1.);

void main()
{
    gl_Position=mvpMat*pos;
}
'''

thickline_vert = _defines + '''

in layout(location=0) vec2 vert;
in layout(location=1) float inRefVal;

uniform mat4  mvpMat;
uniform vec2  resolution;

out float gRefVal;

void main()
{
    vec4 pos = mvpMat * vec4(vert,0.,1.);
    pos.xyz /= pos.w;
    pos.xy = (pos.xy + 1.0) * 0.5 * resolution;

    gRefVal = inRefVal;
    gl_Position = pos;
}
'''

refcolortex_vert = _defines + '''

layout (location=0) in vec4 pos;
layout (location=1) in vec2 st;
uniform mat4 mvpMat;

out vec2 tCoord;

void main()
{
    vec4 vert=mvpMat*pos;
    gl_Position=vert;

    tCoord=st;


}
'''

point_vert = _defines + '''

layout (location=0) in vec4 pos;
layout (location=1) in int selected;
layout (location=2) in vec4 inColor;
layout (location=3) in float inSize;
layout (location=4) in uint inGlyph;
uniform mat4 pMat;

//uniform vec4 inColor;

flat out int fSelected;
flat out vec4 ptColor;
flat out float ptScale;
flat out uint glyph;

void main()
{
    vec4 vert =pMat*pos;
    gl_Position= vert;
    gl_PointSize=inSize;
    fSelected = selected;
    ptColor = inColor;
    ptScale = inSize;
    glyph = inGlyph;
    
    
}
'''

point_ref_vert = _defines + '''

layout (location=0) in vec4 pos;
layout (location=1) in int selected;
layout (location=2) in float inRefVal;

uniform mat4 mvpMat;
uniform vec2 refSizeRange=vec2(1.,1.);
uniform bool clampGradient = false;
uniform vec2 valueBoundaries = vec2(0.,1.);

flat out int fSelected;
flat out float refVal;
flat out float ptScale;

void main()
{
    vec4 vert = mvpMat*pos;
    gl_Position = vert;

    fSelected = selected;
    refVal = inRefVal;
    if (clampGradient)
        refVal = (refVal-valueBoundaries[0])/(valueBoundaries[1]-valueBoundaries[0]);
    
    // This will only fire if GL_PROGRAM_POINT_SIZE is enabled.
    //Assumes refValue is normalized
    ptScale = mix(refSizeRange[0],refSizeRange[1],refVal);
    gl_PointSize = ptScale;

}
'''


text_vert = _defines + '''

in layout(location=0) vec3 vert;
in layout(location=1) vec2 st;
in layout(location=2) vec2 anchor;

uniform mat4 mvpMat = mat4(1.);
uniform mat4 txtViewMat = mat4(1.);

out vec2 f_st;

void main(void)
{
    mat4 viewMat=txtViewMat;
    // undo scaling
    viewMat[0][0]=1.;
    viewMat[1][1]=1.;
    viewMat[2][2]=1.;

    //find position without scaling
    vec4 newOffs = (txtViewMat*mvpMat*vec4(anchor,0.,1.))-(viewMat*mvpMat*vec4(anchor,0.,1.));
    newOffs.w=0.;
    gl_Position = (viewMat*mvpMat*(vec4(vert,1.)))+newOffs;

    f_st = st;
}
'''

rubberband_vert = _defines + '''

in vec4 vert;

out vec2 st;

void main()
{
    //assume already in [-1,1]
    gl_Position = vert;
    st = vert.xy;
}

'''

fbBlit_vert = _defines + '''

in layout(location=0) vec4 pos;
out vec2 fCoord;

void main()
{
    // passthru vert
    gl_Position = pos;

    // convert [-1,1] to [0,1]
    fCoord = (pos.xy + 1.) / 2.;

}
'''
# </editor-fold>

# <editor-fold desc="~~~ Geometry Shaders ~~~">

thickline_geom = _defines + '''

layout(lines_adjacency) in;
layout(triangle_strip,max_vertices=8) out;

uniform vec2  resolution;
uniform float width;

in float gRefVal[];
out vec2 refCoord;
out float refVal;

void emitVertex(vec4 v,vec2 circleVert,float inVal)
{
    refCoord = circleVert;
    refVal = inVal;
    v.xy = v.xy / resolution * 2. - 1.;
    v.xyz *= v.w;
    gl_Position = v;

    EmitVertex();
}


void main()
{
    vec4 v0=gl_in[0].gl_Position;
    vec4 v1=gl_in[1].gl_Position;
    vec4 v2=gl_in[2].gl_Position;
    vec4 v3=gl_in[3].gl_Position;

    if (v1==v2)
        return;
    vec2 v_line  = normalize(v2.xy - v1.xy);
    vec2 nv_line = vec2(-v_line.y, v_line.x);
    vec4 offs = vec4(nv_line * width * 0.5,0.,0.);
    vec4 foreslashVec = vec4(v_line*width*0.5,0.,0.)+offs;
    vec4 backslashVec = vec4(-foreslashVec.y,foreslashVec.x,0.,0.);


    //left cap
    if (v0!=v1)
    {
        emitVertex(v1+backslashVec,vec2(1.,1.),gRefVal[1]);
        emitVertex(v1-foreslashVec,vec2(1.,-1.),gRefVal[1]);
    }

    //lines
    emitVertex(v1+offs,vec2(0.,1.),gRefVal[1]);
    emitVertex(v1-offs,vec2(0.,-1.),gRefVal[1]);
    emitVertex(v2+offs,vec2(0.,1.),gRefVal[2]);
    emitVertex(v2-offs,vec2(0.,-1.),gRefVal[2]);


    //right cap
    if (v2!=v3)
    {
        emitVertex(v2+foreslashVec,vec2(1.,1.),gRefVal[2]);
        emitVertex(v2-backslashVec,vec2(1.,-1.),gRefVal[2]);
    }
}

'''

axes_geom = _defines + '''

layout(lines) in;
layout(max_vertices=128) out;
layout(line_strip) out;


//Just need to be projection matrix
uniform mat4 txtProjMat;
uniform mat4 txtVpMat;
uniform float tickWidth = 2.;
uniform float capTickWidth = 10.;
uniform int subTickCount = 0;

void EmitEdge(vec2 a, vec2 b,vec2 offset)
{
    vec4 v4Offs= txtProjMat*vec4(offset,0.,0.);
    gl_Position = (txtVpMat*vec4(a,0.,1.))-v4Offs;
    EmitVertex();
    gl_Position = (txtVpMat*vec4(b,0.,1.))+v4Offs;
    EmitVertex();
    EndPrimitive();
}

void main()
{

    vec2 v0 = gl_in[0].gl_Position.xy;
    vec2 v1 = gl_in[1].gl_Position.xy;

    vec2 n = normalize(v1-v0);
    vec2 offset = n.yx*tickWidth; 
    vec2 capOffset = n.yx*capTickWidth;

    EmitEdge(v0,v1,vec2(0.));
    EmitEdge(v0,v0,capOffset);
    EmitEdge(v1,v1,capOffset);

    float step = distance(v0,v1)/float(subTickCount+1);

    for(int i = 1; i<=subTickCount;++i)
    {
        vec2 currPos = v0 + (n*step * float(i));
        EmitEdge(currPos,currPos,offset);
    }

}
'''
# </editor-fold>

# <editor-fold desc="~~~ Fragment Shaders ~~~">
simple_frag = _defines + '''

layout (location=0) out vec4 vColor;

uniform vec4 inColor=vec4(0.,0.,0.,1.);

void main()
{
    vColor=inColor;
}
'''

point_frag = _defines + '''

layout (location=0) out vec4 vColor;

flat in int fSelected;
flat in vec4 ptColor;
flat in float ptScale;
flat in uint glyph;

//uniform uint glyph = 46u; //circle
uniform vec4 selectColor;
//uniform float ptScale;
uniform vec4 edgeColor= vec4(0.,0.,0.,1.);

''' + _pointFns + '''

void main()
{
    //Assume coordinates are in unit space; x and y are in [0,1].
    //if x^2+y^2 is greater than the unit circle's radius^2 (ie 0.25) discard.
    //This is pretty fast, and it produces a nice result no matter the zoom level.

    //some prettiness adjusted from here: https://gamedev.stackexchange.com/questions/141264/an-efficient-way-for-generating-smooth-circle

    vColor = doPoint(ptColor,glyph);
    //float sqDist = pow(gl_PointCoord.x-RAD-MARGIN,2)+pow(gl_PointCoord.y-RAD-MARGIN,2);
    //if (sqDist>RAD_SQ)
    //    discard;

    // float buff=1./ptScale;
    // 
    // 
    // if (fSelected == 0)
    // {        
    //     vColor = ptColor;
    //     vColor.a = smoothstep(RAD_SQ+buff,RAD_SQ-buff,sqDist);
    //     if (vColor.a <1.0)
    //         vColor.xyz=edgeColor.xyz;
    // }
    // else
    // {
    //     vColor = selectColor;
    // }
// 
    // //vColor=  selectColor;
}
'''

point_ref_frag = _defines + '''

layout (location=0) out vec4 vColor;

flat in int fSelected;
flat in float refVal;
flat in float ptScale;

// use location 1 to be consistant with colorbands in other shaders
layout(binding=1) uniform sampler1D colorBand;

uniform vec4 selectColor;
uniform vec4 edgeColor= vec4(0.,0.,0.,1.);

uniform bool customGradient = false;
uniform vec2 valueBoundaries = vec2(0.,1.);

uniform uint glyph = 46u; //circle

''' + _pointFns + '''

void main()
{
    // filter only values we want; max valueboundaries is (0.,1.)
    if (refVal < valueBoundaries[0] || refVal > valueBoundaries[1])
        discard;

    // if clamped, adjust lookup value to compress entire gradient range to range of 
    // value boundaries.
    
    vec4 ptColor = vec4(1.);
    if (customGradient)
    {
        //use the reference value to pull a color from the colorband.
        ptColor=texture(colorBand,refVal);

    }
    else
    {
        //simple gradient - assumes normalized value
        ptColor=vec4(refVal,refVal*0.5,0.,1.);
    }

    //Assume coordinates are in unit space; x and y are in [0,1].
    //if x^2+y^2 is greater than the unit circle's radius^2 (ie 0.25) discard.
    //This is pretty fast, and it produces a nice result no matter the zoom level.

    //some prettiness adjusted from here: https://gamedev.stackexchange.com/questions/141264/an-efficient-way-for-generating-smooth-circle

    vColor = doPoint(ptColor,glyph);

}
'''

line_ref_frag = _defines + '''

layout (location=0) out vec4 vColor;

in float refVal;
in vec2 refCoord;

// use location 1 to be consistant with colorbands in other shaders
layout(binding=1) uniform sampler1D colorBand;

uniform bool customGradient = false;
uniform vec2 valueBoundaries = vec2(0.,1.);


void main()
{
    // filter only values we want; max valueboundaries is (0.,1.)
    if (length(refCoord) > 1. || refVal < valueBoundaries[0] || refVal > valueBoundaries[1])
        discard;

    // if clamped, adjust lookup value to compress entire gradient range to range of 
    // value boundaries.

    vec4 lineColor = vec4(1.);
    if (customGradient)
    {
        //use the reference value to pull a color from the colorband.
        lineColor=texture(colorBand,refVal);

    }
    else
    {
        //simple gradient - assumes normalized value
        lineColor=vec4(refVal,refVal*0.5,0.,1.);
    }
    
    vColor = lineColor;

}
'''

select_frag = _defines + '''

layout (location=0) out vec4 vColor;

uniform vec4 inColor1;
uniform vec4 inColor2;
uniform float stripeWidth = 10;
void main()
{
    vColor=inColor1;
    if (mod(gl_FragCoord.x + gl_FragCoord.y, stripeWidth) > stripeWidth*0.5)
        vColor = inColor2;
}
'''

select_line_frag = _defines + '''

layout (location=0) out vec4 vColor;

uniform vec4 inColor1;
uniform vec4 inColor2;
uniform float stripeWidth = 10;

in vec2 refCoord;

float sqLength(vec2 v)
{
    return pow(v.x,2)+pow(v.y,2);
}

void main()
{
    if(sqLength(refCoord)>1.)
        discard;
    vColor=inColor1;
    if (mod(gl_FragCoord.x + gl_FragCoord.y, stripeWidth) > stripeWidth*0.5)
        vColor = inColor2;
    //vColor=vec4(0.,fDist,0.,1.);
}
'''

refcolortex_frag = _defines + '''

layout (location=0) out vec4 vColor;

in vec2 tCoord;

layout(binding=0) uniform sampler2D valueTex;
layout(binding=1) uniform sampler1D colorBand;

uniform bool customGradient = false;
uniform bool clampGradient = false;
uniform vec2 valueBoundaries = vec2(0.,1.);


void main()
{

    //grab the reference value from the raster
    //either assume normalize, or provide enough
    //data to the shader to normalize for band hookup.
    if (any(lessThan(tCoord,vec2(0.,0.))) || any(greaterThan(tCoord,vec2(1.,1.))))
        discard;
    float refVal = texture(valueTex,tCoord)[0];

    // filter only values we want; max valueboundaries is (0.,1.)
    if (refVal < valueBoundaries[0] || refVal > valueBoundaries[1])
        discard;

    // if clamped, adjust lookup value to compress entire gradient range to range of 
    // value boundaries.
    if (clampGradient)
            refVal = (refVal-valueBoundaries[0])/(valueBoundaries[1]-valueBoundaries[0]);

    if (customGradient)
    {
        //use the reference value to pull a color from the colorband.
        vColor=texture(colorBand,refVal);

    }
    else
    {
        //simple gradient - assumes normalized value
        vColor=vec4(refVal,refVal*0.5,0.,1.);
    }
}

'''

colortex_frag = _defines + '''

layout (location=0) out vec4 vColor;

in vec2 tCoord;

layout(binding=0) uniform sampler2D valueTex;
uniform bool isSelect = false;
uniform vec4 selectColor = vec4(0.);

void main()
{

    vColor = !isSelect ? texture(valueTex,tCoord) : selectColor;
    //vColor = vec4(tCoord,0.,1.);
    if (vColor[0] < 0.0)
        discard;

}

'''

refcolorval_frag = _defines + '''

layout (location=0) out vec4 vColor;

in vec2 tCoord;

uniform float refValue;
layout(binding=2) uniform sampler1D colorBand;

uniform bool customGradient = false;

void main()
{

    if (refValue < 0.0)
        discard;

    if (customGradient)
    {
        //use the reference value to pull a color from the colorband.
        vColor=texture(colorBand,refValue);
    }
    else
    {
        //simple gradient - assumes normalized value
        vColor=vec4(refValue,0,0.,1.);
        //vColor=vec4(tCoord[0],tCoord[1],0.,1.);
    }

}

'''

rubberband_frag = _defines + '''

in vec2 st;

uniform vec4 color1 = vec4(0.,0.,0.,1.);
uniform vec4 color2 = vec4(1.,1.,1.,1.);

layout (location=0) out vec4 fColor;
void main()
{
    int ix= int(100.0 * st.x);
    int iy= int(100.0 * st.y);

    fColor=color1;
    if ((ix+iy) % 2==1)
        fColor = color2;
}
'''

text_frag = _defines + '''

in vec2 f_st;

uniform sampler2D textAtlas;

uniform vec4 fillColor=vec4(0.,0.,0.,1.);

layout (location=0) out vec4 outColor;

void main(void)
{
    // NOTE: even though texelFetch is integer, we need f_st to be
    // float since Pipeline will not interpolate b/w integers

    float alpha = texelFetch(textAtlas,ivec2(f_st),0).r;

    outColor=fillColor;
    outColor.a=alpha;
}

'''

fbBlit_frag = _defines + '''

in vec2 fCoord;

layout(binding=0) uniform sampler2D frameBuff;

layout (location=0) out vec4 fColor;

void main()
{
    fColor = texture(frameBuff,fCoord);
    //fColor = vec4(1.,0.,0.,1.);
}

'''
# </editor-fold>

# default shaders used by the visualizer. Entries can be overridden using custom shaders.
# Replace only; new entries in the shader_recipes dict will cause an exception to be raised.

# @formatter:on
#                               vertex            geometry        fragment         tess. control      tess eval
shader_recipes = {"simple":     (passthru_vert,   None,           simple_frag,     None,              None),
                  "point":      (point_vert,      None,           point_frag,      None,              None),
                  "refPoint":   (point_ref_vert,  None,           point_ref_frag,  None,              None),
                  "thickline":  (thickline_vert,  thickline_geom, select_line_frag,None,              None),
                  "refline":    (thickline_vert,  thickline_geom, line_ref_frag,   None,              None),
                  "selectPoly": (passthru_vert,   None,           select_frag,     None,              None),
                  "refColorTex":(refcolortex_vert,None,           refcolortex_frag,None,              None),
                  "refColorVal":(passthru_vert,   None,           refcolorval_frag,None,              None),
                  "rubberBand": (rubberband_vert, None,           rubberband_frag, None,              None),
                  "text":       (text_vert,       None,           text_frag,       None,              None),
                  "axes":       (passthru_vert,   axes_geom,      simple_frag,     None,              None),
                  "raster":     (refcolortex_vert,None,           colortex_frag,   None,              None),
                  "fbBlit":     (fbBlit_vert,     None,           fbBlit_frag,     None,              None),
                  }

fieldMappings={"simple":["mvpMat",
                         "inColor"
                        ],
               "point":["pMat",
                        "selectColor",
                        ],
             "refPoint":["mvpMat",
                         "refSizeRange",
                         "selectColor",
                         "edgeColor",
                         "customGradient",
                         "clampGradient",
                         "valueBoundaries",
                         "flatPtScale",
                         "glyph"
                        ],
            "thickline":["mvpMat",
                         "inColor1",
                         "inColor2",
                         "width",
                         "resolution",
                        ],
              "refline":["mvpMat",
                         "width",
                         "resolution",
                         "customGradient",
                         "valueBoundaries",
                        ],
           "selectPoly":["mvpMat",
                         "inColor1",
                         "inColor2",
                        ],
          "refColorTex":["mvpMat",
                         "customGradient",
                         "valueBoundaries",
                         "clampGradient"
                        ],
          "refColorVal":["mvpMat",
                         "refValue",
                         "customGradient"
                        ],
           "rubberBand":["color1",
                         "color2",
                        ],
                 "text":["mvpMat",
                         "txtViewMat",
                         "textAtlas",
                         "fillColor"
                        ],
                 "axes":["txtProjMat",
                         "txtVpMat",
                         "tickWidth",
                         "capTickWidth",
                         "subTickCount",
                        ],
               "raster":["mvpMat",
                         "selectColor",
                         "isSelect"
                        ]
   }


def findUniformLocations(progDict,mappings):

    # Find the index location of all uniform variables in each shader program. A uniform variable is a value
    # that can be set prior to rendering that will apply to all invocations of a given shader during the rendering
    # process.

    ret = {}
    for n,p in progDict.items():
        if n in mappings:
            ret[p]={v:glGetUniformLocation(p,v) for v in mappings[n]}
    return ret

def buildShaders(recipes):
    """Take the supplied shader source codes, compile, and combine into shader programs."""

    shader_types = (GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_FRAGMENT_SHADER,
                    GL_TESS_CONTROL_SHADER, GL_TESS_EVALUATION_SHADER)

    ret = {k: 0 for k in recipes.keys()}

    for name, src in recipes.items():

        prog = glCreateProgram()
        for i in range(len(shader_types)):
            if src[i] is not None:
                shad = glCreateShader(shader_types[i])
                glShaderSource(shad, src[i])
                glCompileShader(shad)
                if glGetShaderiv(shad, GL_COMPILE_STATUS, None) == GL_FALSE:
                    lbls=['vert','geom','frag','tcs','tes']
                    raise Exception("'"+name + "' ("+lbls[i]+") Shader Program compile failed:\n\n",
                                    glGetShaderInfoLog(shad))

                glAttachShader(prog, shad)
        glLinkProgram(prog)
        isLinked = glGetProgramiv(prog, GL_LINK_STATUS)
        if not isLinked:
            raise Exception("'"+name + "' Shader Program link failed:\n\n", glGetProgramInfoLog(prog))
        ret[name] = prog
    return ret


def assignUniformBlock(progs, bindPt, lbl):
    for p in progs:
        ind = glGetUniformBlockIndex(p, lbl)
        if ind != GL_INVALID_INDEX:
            glUniformBlockBinding(p, ind, bindPt)


def _grabSubShaderList(names, suffix):
    ext = suffix.replace('_', '.')
    return [(x, x.replace(suffix, ext)) for x in names if x.endswith(suffix)]


def ExportShadersToFiles(outDir):
    """Convenience method for exporting all shaders to external files.

    Args:
        dir(str or Path): path to parent directory

    """

    # add import here since it this function will rarely be called
    import os

    # https://stackoverflow.com/questions/1676835/how-to-get-a-reference-to-a-module-inside-the-module-itself
    currModule = __import__(__name__)

    varNames = dir(currModule)
    suffixes = ['_vert', '_frag', '_geom', '_teco', '_teev']
    for suff in suffixes:
        shads = _grabSubShaderList(varNames, suff)

        for v, file in shads:
            with open(os.path.join(outDir, file), 'w') as outFile:
                outFile.write(getattr(currModule, v))

######################################################################
# Utility class to wrap some of the functional behavior above

class ShaderProgMgr(object):

    def __init__(self,progRecipes=None,mappings=None):
        self._active=0

        if progRecipes is None:
            progRecipes = shader_recipes
        if mappings is None:
            mappings = fieldMappings

        self._progs= buildShaders(progRecipes)
        self._mappings = findUniformLocations(self._progs,mappings)

    def cleanup(self):
        for prog in self._progs.values():
            glDeleteProgram(prog)

    def useProgram(self,progName=None):

        self._active = self._progs[progName] if progName is not None else 0
        glUseProgram(self._active)

    def useProgramDirectly(self,prog):
        self._active = prog
        glUseProgram(self._active)

    def __getitem__(self, item):

        try:
            return self._mappings[self._active][item]
        except KeyError as e:
            e.args=(e.args[0]+f'; Recognized uniform fields: {list(self._mappings[self._active].keys())}',)
            raise

    def progLookup(self,progName):
        try:
            return self._progs[progName]
        except KeyError:
            return 0


    @property
    def shaderProgram(self):
        return self._active
