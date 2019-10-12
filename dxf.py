#!/usr/bin/env python
"""Utilities for translating between dxf and native cadvas (.pkl) format"""
import math
import ezdxf

GEOMCOLOR = "white"
CONSTRCOLOR = "magenta"

def pnt_n_vctr_to_coef(pnt, vector):
    (u, v, w) = pnt
    (x, y, z) = vector
    pt1 = (u, v)
    pt2 = (u + x, v + y)
    return cnvrt_2pts_to_coef(pt1, pt2)

def normalize_vector(vctr):
    x, y, z = vctr
    diag = math.sqrt(x * x + y * y)
    return (x / diag, y / diag, 0)

def coef_to_pnt_n_vctr(coords):
    a, b, c = coords
    if abs(b) >= abs(a):
        y_intercept = -(c / b)
        p0 = (0, y_intercept, 0)
    else:
        x_intercept = -(c / a)
        p0 = (x_intercept, 0, 0)
    vector = normalize_vector((b, -a, 0))
    return (p0, vector)

def cnvrt_2pts_to_coef(pt1, pt2):
    """Return (a,b,c) coefficients of cline defined by 2 (x,y) pts."""
    x1, y1 = pt1
    x2, y2 = pt2
    a = y2 - y1
    b = x1 - x2
    c = x2*y1-x1*y2
    return (a, b, c)

def dxf2native(filename):
    """Generate a dictionary of {k=type: v=attribs} from dxf entities."""

    drawlist = []
    dwg = ezdxf.readfile(filename)
    for e in dwg.modelspace():  # e = dxf entity
        if e.dxftype() == 'XLINE':
            # print(e.dxfattribs())
            coords = pnt_n_vctr_to_coef(e.dxf.start, e.dxf.unit_vector)
            drawlist.append({'cl': (coords, CONSTRCOLOR)})
        if e.dxftype() == 'LINE':
            # print(e.dxfattribs())
            coords = (e.dxf.start, e.dxf.end)
            drawlist.append({'gl': (coords, GEOMCOLOR)})
        elif e.dxftype() == 'CIRCLE':
            # print(e.dxfattribs())
            coords = (e.dxf.center, e.dxf.radius)
            drawlist.append({'gc': (coords, GEOMCOLOR)})
        elif e.dxftype() == 'ARC':
            # print(e.dxfattribs())
            coords = (e.dxf.center, e.dxf.radius,
                      e.dxf.start_angle, e.dxf.end_angle)
            drawlist.append({'ga': (coords, GEOMCOLOR)})
        elif e.dxftype() == 'TEXT':
            # print(e.dxfattribs())
            coords = e.dxfattribs()['align_point']
            text = e.dxfattribs()['text']
            style = e.dxfattribs()['style']
            size = e.dxfattribs()['height']
            attribs = (coords, text, style, size, 'cyan')  # no dxf color attrib
            drawlist.append({'tx': attribs})
            
    return drawlist


def native2dxf(drawlist, dxf_filename):
    """Generate .dxf file format from native CADvas drawing."""
    
    # Create a new DXF R2010 drawing
    dwg = ezdxf.new('R2010')  # Official DXF version name: 'AC1024'
    msp = dwg.modelspace()  # Create new model space
    # Add new entities to the model space
    for ent_dict in drawlist:
        if 'cl' in ent_dict:
            coords, color = ent_dict['cl']
            pnt, vctr = coef_to_pnt_n_vctr(coords)
            msp.add_xline(pnt, vctr)
        if 'gl' in ent_dict:
            (p0, p1), color = ent_dict['gl']
            msp.add_line(p0, p1)
        if 'gc' in ent_dict:
            (center, radius), color = ent_dict['gc']
            msp.add_circle(center, radius)
        if 'ga' in ent_dict:
            (center, radius, start, end), color = ent_dict['ga']
            msp.add_arc(center, radius, start, end)
        if 'tx' in ent_dict:
            (coords, text, style, size, color) = ent_dict['tx']
            dxfattribs = dict((('align_point', coords),
                               ('halign', 2),
                               ('height', size),
                               ('insert', coords),
                               ('layer', '0'),
                               ('oblique', 0.0),
                               ('paperspace', 0),
                               ('rotation', 0.0),
                               ('style', style),
                               ('text', text),
                               ('text_generation_flag', 0),
                               ('valign', 2),
                               ('width', 1.0)))
            msp.add_text(text, dxfattribs)
    dwg.saveas(dxf_filename)
