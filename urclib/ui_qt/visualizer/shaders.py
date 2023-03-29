# This file is part of URC Assessment Method.
#
# URC Assessment Method is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# URC Assessment Method is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with URC Assessment Method. If not, see
# <https://www.gnu.org/licenses/>.

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
#define ORD_STAR      42u //'*'

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
    return ptColor;
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


vec3 barycentric(vec2 p, vec2 p0, vec2 p1, vec2 p2)
{
    mat2 T = mat2(p0-p2,p1-p2);
    vec3 results = vec3(0);
    results.xy = inverse(T)*(p-p2);
    results.z = 1. - results.x-results.y;
    return results;

}

bool inBarycentric(vec3 p)
{
    return all(greaterThan(p,vec3(0.)));
}
bool inTriangle(vec2 p, vec2 p0, vec2 p1, vec2 p2)
{
    vec3 bc = barycentric(p,p0,p1,p2);
    return inBarycentric(bc);
}

vec4 pointStar(vec4 ptColor, bool pointDown)
{

    const float THICKNESS = ptScale <= 4 ? 0. : 1.;
    vec2 adj=(2.*gl_PointCoord.xy) - 1.0;
    if (pointDown)
        adj.y*=-1.;
    
    //const float INNER_RAD_2 = 0.25;
    //if (pow(adj.x,2)+pow(adj.y,2) < INNER_RAD_2)
    //    return ptColor;
        
    //TODO: add pre-calculated tris here
    vec2 tris[5][3] = {
                      {vec2( 0.   , 1.   ),vec2(-.3804,-.1236),vec2( .3804,-.1236)},
                      {vec2( .9511, .3090),vec2(-.2351, .3236),vec2( .0   ,-.4   )},
                      {vec2( .5878,-.8090),vec2( .2351, .3236),vec2(-.3804,-.1236)},
                      {vec2(-.5878,-.8090),vec2( .3804,-.1236),vec2(-.2351, .3236)},
                      {vec2(-.9511, .3090),vec2( 0.   ,-.4   ),vec2( .2351, .3236)},
                    };

    bool hit = false;
    vec3 baryCoord=vec3(0);
    for (int i=0; !hit && i<5; ++i)
    {        
        baryCoord = barycentric(adj,tris[i][0],tris[i][1],tris[i][2]);
        hit = inBarycentric(baryCoord);
    }
    
    if (!hit)
        discard;
    
    return ptColor;
    
    // todo: fix border
    // float sDist = 1 - min(baryCoord.x,min(baryCoord.y,baryCoord.z));
    // return applySD(ptColor,sDist, THICKNESS);

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
    case ORD_STAR:
        outColor = pointStar(ptColor,true);
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

in layout(location=0) vec2 vert;
in layout(location=1) vec2 st;
in layout(location=2) vec3 anchor;
in layout(location=3) vec4 color;

uniform mat4 mvpMat;
uniform vec2 xyOffs=vec2(0.0,0.0);
uniform vec2 resolution;

out vec2 f_st;
out vec4 fillColor;

void main(void)
{
    //convert vertex offset (in pixels) from anchor to clip-space 
    vec2 corner= (2.*(vert/resolution));
   
    gl_Position = mvpMat * vec4(anchor,1.0);

    //offset the corner from the anchor point
    gl_Position /= gl_Position.w;
    gl_Position.xy += corner+xyOffs;

    f_st = st;
    fillColor = color;
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
in vec4 fillColor;
layout(binding=0) uniform sampler2D textAtlas;
uniform bool showOutline=false;
uniform vec3 outlineColor=vec3(1.,0.,0.);

layout (location=0) out vec4 outColor;
layout (location=1) out vec4 hitMask;

//matrices for SOBEL filter
mat3 sx = mat3( 
    1.0, 2.0, 1.0, 
    0.0, 0.0, 0.0, 
   -1.0, -2.0, -1.0 
);
mat3 sy = mat3( 
    1.0, 0.0, -1.0, 
    2.0, 0.0, -2.0, 
    1.0, 0.0, -1.0 
);

void main(void)
{
    // NOTE: even though texelFetch is integer, we need f_st to be
    // float since Pipeline will not interpolate b/w integers

    float alpha = texelFetch(textAtlas,ivec2(f_st),0).r;

    // use discard if space is empty to avoid writing to depth buffer in empty places
    // this allows text to overlap; there will still be some ugliness where the font is
    // antialiased, but that's ok.
    if (abs(alpha)<10e-5)
        discard;

    outColor=fillColor;
    outColor.a*=alpha;

    if (showOutline)
    {
        //mix in select mask
        mat3 I;
        for (int i=0; i<3; i++) 
        {
            for (int j=0; j<3; j++) 
            {
                //assume binary black/white mask
                I[i][j] = texelFetch(textAtlas, ivec2(f_st) + ivec2(i-1,j-1), 0 ).r;
            }
        }

        float gx = dot(sx[0], I[0]) + dot(sx[1], I[1]) + dot(sx[2], I[2]); 
        float gy = dot(sy[0], I[0]) + dot(sy[1], I[1]) + dot(sy[2], I[2]);

        float g = sqrt(pow(gx, 2.0)+pow(gy, 2.0));
        outColor.rgb = mix(outColor.rgb,outlineColor,step(0.5,g));
        hitMask=vec4(1.);
    }

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
                  "raster":     (refcolortex_vert,None,           colortex_frag,   None,              None),
                  "fbBlit":     (fbBlit_vert,     None,           fbBlit_frag,     None,              None),
                  }

fieldMappings={"simple":["mvpMat",
                         "inColor"
                        ],
               "point":["pMat",
                        "selectColor",
                        "inColor",
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
                         "xyOffs",
                         "resolution",
                         "textAtlas",
                         "showOutline",
                         "outlineColor",
                        ],
                 "raster":["mvpMat",
                         "selectColor",
                         "isSelect"
                        ]
   }


def findUniformLocations(progDict,mappings):
    """ Find the index location of all uniform variables in each shader program.

    Args:
        progDict (dict): A dictionary that matches the output of `buildShaders()`.
        mappings (dict): A dict of dicts which maps the names of uniform variables to locate.

    Returns:
        dict: Uniform name (key) and location (value).
    """
    #  A uniform variable is a value that can be set prior to rendering that will apply to all invocations of a given
    #  shader during the rendering process.

    ret = {}
    for n,p in progDict.items():
        if n in mappings:
            ret[p]={v:glGetUniformLocation(p,v) for v in mappings[n]}
    return ret

def buildShaders(recipes):
    """Take the supplied shader source codes, compile, and combine into shader programs.

    Args:
        recipes (dict): Lists of shaders to build shader pipelines.

    Returns:
        dict: The OpenGL identifiers for the newly built shaders, stored under the key used for the
            equivalent recipe entry.
    """

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
    """Assign a uniform block to any shader program which explicitly calls for it.

    Args:
        progs (list): The programs to parse for the designated uniform block.
        bindPt (int): The uniform array binding index.
        lbl (str): The dlg_label of the uniform block declared within the shader program.
    """

    for p in progs:
        ind = glGetUniformBlockIndex(p, lbl)
        if ind != GL_INVALID_INDEX:
            glUniformBlockBinding(p, ind, bindPt)


def _grabSubShaderList(names, suffix):
    """Build file name list of shaders to export based on names provided.

    Args:
        names (list): The list of names to transform.
        suffix (str): The suffix of names to include.

    Returns:
        list: the filenames to apply.
    """
    ext = suffix.replace('_', '.')
    return [(x, x.replace(suffix, ext)) for x in names if x.endswith(suffix)]


def ExportShadersToFiles(outDir):
    """Convenience method for exporting all shaders to external files.

    Args:
        outDir(str or Path): path to parent directory

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
    """Convenience manager for multiple shader programs.

    Args:
        progRecipes (dict,optional): The shader program recipes to include. If `None`, the module variable
                `shader_recipes` is used.
        mappings (dict,optional): The uniform field mappings to shader programs. If `None`, the module variable
               `fieldMappings` is used.
    """

    def __init__(self,progRecipes=None,mappings=None):

        self._active=0

        if progRecipes is None:
            progRecipes = shader_recipes
        if mappings is None:
            mappings = fieldMappings

        self._progs= buildShaders(progRecipes)
        self._mappings = findUniformLocations(self._progs,mappings)

    def cleanup(self):
        """Delete all the programs managed by this manager."""
        for prog in self._progs.values():
            glDeleteProgram(prog)

    def useProgram(self,progName=None):
        """Activate a shader prograam by name.

        Args:
            progName (str,optional): The name of the program to activate; all programs are deactivated if omitted.
        """

        self._active = self._progs[progName] if progName is not None else 0
        glUseProgram(self._active)

    def useProgramDirectly(self,prog):
        """Activate a shader prograam by OpenGL identifier.

        Args:
            prog (int): The OpenGL shader program identifier.
        """

        self._active = prog
        glUseProgram(self._active)

    def __getitem__(self, item):

        try:
            return self._mappings[self._active][item]
        except KeyError as e:
            e.args=(e.args[0]+f'; Recognized uniform fields: {list(self._mappings[self._active].keys())}',)
            raise

    def progLookup(self,progName):
        """Find an OpenGL program identifier by program name.

        Args:
            progName (str): The program to search for.

        Returns:
            int: The identifier for the program, or 0 if `progName` does not map to a known shader program.
        """
        try:
            return self._progs[progName]
        except KeyError:
            return 0


    @property
    def shaderProgram(self):
        """int: OpenGL identifier of active shader program."""
        return self._active
