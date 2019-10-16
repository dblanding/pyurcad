"""
PyurCad is Pure CAD in the sense that it uses only Python3 and the standard
libraries that come with it. It is a rewrite of cadvas without the use of
Python MegaWidgets.
"""

import math
import os
import pickle
import pprint
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import entities
import geometryhelpers as gh
import tkrpncalc
import txtdialog
from zooming import Zooming

GEOMCOLOR = 'white'     # color of geometry entities
CONSTRCOLOR = 'magenta'  # color of construction entities
TEXTCOLOR = 'cyan'      # color of text entities
DIMCOLOR = 'red'        # color of dimension entities
RUBBERCOLOR = 'yellow'  # color of (temporary) rubber elements


class PyurCad(tk.Tk):

    tool_bar_function_names = {'noop': "No Current Operation",
                               'hvcl': "Horizontal & Vertical Construction Line",
                               'hcl': "Horizontal Construction Line",
                               'vcl': "Vertical Construction Line",
                               'acl': "Angled Construction Line",
                               'clrefang': "Construction Line by Ref Angle",
                               'abcl': "Angle Bisector Construction Line",
                               'lbcl': "Linear Bisector Consturction Line",
                               'parcl': "Parallel Construction Line",
                               'perpcl': "Perpendicular Construction Line",
                               'cltan1': "Construction Line Tangent to Circle",
                               'cltan2': "Construction Line Tangent to 2 Circles",
                               'ccirc': "Construction Circle",
                               'cc3p': "Construction Circle by 3 Points",
                               'cccirc': "Concentric Construction Circle",
                               'line': "Line",
                               'poly': "Poly Line",
                               'rect': "Rectangle",
                               'circ': "Circle",
                               'arcc2p': "Arc by Center, Start, End Point",
                               'arc3p': "Arc by 3 Points",
                               'slot': "Slot by 2 Points & Width",
                               'split': "Split Line",
                               'join': "Join 2 Lines",
                               'fillet': "Fillet 2 Adjacent Lines",
                               'translate': "Translate Geometry",
                               'rotate': "Rotate Geometry"}

    tool_bar_functions = ('noop', 'hvcl', 'hcl',
                          'vcl', 'acl', 'clrefang',
                          'abcl', 'lbcl', 'parcl',
                          'perpcl', 'cltan1', 'cltan2',
                          'ccirc', 'cc3p', 'cccirc',
                          'line', 'poly', 'rect',
                          'circ', 'arcc2p', 'arc3p',
                          'slot', 'split', 'join',
                          'fillet', 'translate', 'rotate')

    selected_tool_bar_function = tool_bar_functions[0]

    catchCntr = False
    catch_pnt = None    # ID of (temporary) catch point
    catch_radius = 5    # radius of catch region
    catch_pnt_size = 5  # size of displayed catch point
    rubber = None       # ID of (temporary) rubber element
    rtext = None        # ID of (temporary) rubber text
    sel_boxID = None    # ID of (temporary) selection box
    op = ''             # current CAD operation (create or modify)
    op_stack = []
    text_entry_enable = 0
    text = ''
    curr = {}           # all entities in curr dwg {k=handle: v=entity}
    prev = {}
    allow_list = 0      # enable/disable item selection in list mode
    sel_mode = ''       # selection mode for screen picks
    float_stack = []    # float values (unitless)
    pt_stack = []       # points, in ECS (mm) units
    obj_stack = []      # canvas items picked from the screen
    sel_box_crnr = None  # first corner of selection box, if any
    undo_stack = []     # list of dicts of sets of entities
    redo_stack = []     # data popped off undo_stack
    filename = None     # name of file currently loaded (or saved as)
    dimgap = 10         # extension line gap (in canvas units)
    textsize = 10       # default text size
    textstyle = 'Calibri'   # default text style
    TEXTCOLOR = TEXTCOLOR
    CONSTR_DASH = 2     # dash size for construction lines & circles
    modified_text_object = None
    cl_list = []        # list of all cline coords (so they don't get lost)
    shift_key_advice = ' (Use SHIFT key to select center of element)'
    unit_dict = {'mm': 1.0,
                 'inches': 25.4,
                 'feet': 304.8}
    units = 'mm'
    unitscale = unit_dict[units]
    calculator = None   # reference to a Toplevel window
    txtdialog = None    # reference to a Toplevel window
    popup = None
    msg = "Left-Click a tool button to start.  Middle-Click on screen to end."

    # =======================================================================
    # Functions for converting between canvas CS and engineering CS
    # =======================================================================

    def ep2cp(self, pt):
        """Convert pt from ECS to CCS."""
        return self.canvas.world2canvas(pt[0], -pt[1])

    def cp2ep(self, pt):
        """Convert pt from CCS to ECS."""
        x, y = self.canvas.canvas2world(pt[0], pt[1])
        return (x, -y)

    # =======================================================================
    # File, View, Units and Measure commands
    # =======================================================================

    def printps(self):
        openfile = None
        ftypes = [('PostScript file', '*.ps'),
                  ('All files', '*')]
        openfile = filedialog.asksaveasfilename(filetypes=ftypes)
        if openfile:
            outfile = os.path.abspath(openfile)
            self.ipostscript(outfile)

    def ipostscript(self, file='drawing.ps'):
        ps = self.canvas.postscript()
        ps = ps.replace('1.000 1.000 1.000 setrgbcolor',
                        '0.000 0.000 0.000 setrgbcolor')
        fd = open(file, 'w')
        fd.write(ps)
        fd.close()

    def fileOpen(self):
        openfile = None
        ftypes = [('CADvas dwg', '*.pkl'),
                  ('All files', '*')]
        openfile = filedialog.askopenfilename(filetypes=ftypes,
                                              defaultextension='.pkl')
        if openfile:
            infile = os.path.abspath(openfile)
            self.load(infile)

    def fileImport(self):
        openfile = None
        ftypes = [('DXF format', '*.dxf'),
                  ('All files', '*')]
        openfile = filedialog.askopenfilename(filetypes=ftypes,
                                              defaultextension='.dxf')
        if openfile:
            infile = os.path.abspath(openfile)
            self.load(infile)

    def fileSave(self):
        openfile = self.filename
        if openfile:
            outfile = os.path.abspath(openfile)
            self.save(outfile)
        else:
            self.fileSaveas()

    def fileSaveas(self):
        ftypes = [('CADvas dwg', '*.pkl'),
                  ('All files', '*')]
        openfile = filedialog.asksaveasfilename(filetypes=ftypes,
                                                defaultextension='.pkl')
        if openfile:
            self.filename = openfile
            outfile = os.path.abspath(openfile)
            self.save(outfile)

    def fileExport(self):
        ftypes = [('DXF format', '*.dxf'),
                  ('All files', '*')]
        openfile = filedialog.asksaveasfilename(filetypes=ftypes,
                                                defaultextension='.dxf')
        if openfile:
            outfile = os.path.abspath(openfile)
            self.save(outfile)

    def save(self, file):

        drawlist = []
        for entity in self.curr.values():
            drawlist.append({entity.type: entity.get_attribs()})

        fext = os.path.splitext(file)[-1]
        if fext == '.dxf':
            import dxf
            dxf.native2dxf(drawlist, file)
        elif fext == '.pkl':
            with open(file, 'wb') as f:
                pickle.dump(drawlist, f)
            self.filename = file
        elif not fext:
            print("Please type entire filename, including extension.")
        else:
            print("Save files of type {fext} not supported.")

    def load(self, file):
        """Load CAD data from file.

        Data is saved/loaded as a list of dicts, one dict for each
        drawing entity, {key=entity_type: val=entity_attribs} """

        fext = os.path.splitext(file)[-1]
        if fext == '.dxf':
            import dxf
            drawlist = dxf.dxf2native(file)
        elif fext == '.pkl':
            with open(file, 'rb') as f:
                drawlist = pickle.load(f)
            self.filename = file
        else:
            print("Load files of type {fext} not supported.")
        for ent_dict in drawlist:
            if 'cl' in ent_dict:
                attribs = ent_dict['cl']
                e = entities.CL(attribs)
                self.cline_gen(e.coords)  # This method takes coords
            elif 'cc' in ent_dict:
                attribs = ent_dict['cc']
                e = entities.CC(attribs)
                self.cline_gen(e)
            elif 'gl' in ent_dict:
                attribs = ent_dict['gl']
                e = entities.GL(attribs)
                self.gline_gen(e)
            elif 'gc' in ent_dict:
                attribs = ent_dict['gc']
                e = entities.GC(attribs)
                self.gcirc_gen(e)
            elif 'ga' in ent_dict:
                attribs = ent_dict['ga']
                e = entities.GA(attribs)
                self.garc_gen(e)
            elif 'dl' in ent_dict:
                attribs = ent_dict['dl']
                e = entities.DL(attribs)
                self.dim_gen(e)
            elif 'tx' in ent_dict:
                attribs = ent_dict['tx']
                print(attribs)
                e = entities.TX(attribs)
                self.text_gen(e)
        self.view_fit()
        self.save_delta()  # undo/redo thing

    def close(self):
        self.quit()

    def view_fit(self):
        bbox = self.canvas.bbox('g', 'd', 't')
        if bbox:
            xsize, ysize = bbox[2]-bbox[0], bbox[3]-bbox[1]
            xc, yc = (bbox[2]+bbox[0])/2, (bbox[3]+bbox[1])/2
            w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
            self.canvas.move_can(w/2-xc, h/2-yc)
            wm, hm = .9 * w, .9 * h
            xscale, yscale = wm/float(xsize), hm/float(ysize)
            if xscale > yscale:
                scale = yscale
            else:
                scale = xscale
            self.canvas.scale(w/2, h/2, scale, scale)
            self.regen()

    def regen(self, event=None):
        self.regen_all_cl()
        self.regen_all_dims()
        self.regen_all_text()

    def set_units(self, units):
        if units in self.unit_dict.keys():
            self.units = units
            self.unitscale = self.unit_dict.get(units)
            self.unitsDisplay.configure(text="Units: %s" % self.units)
            self.regen_all_dims()

    def meas_dist(self, obj=None):
        """Measure distance between 2 points."""
        self.op = 'meas_dist'
        if not self.pt_stack:
            self.update_message_bar('Pick 1st point for distance measurement.')
            self.set_sel_mode('pnt')
        elif len(self.pt_stack) == 1:
            self.update_message_bar('Pick 2nd point for distance measurement.')
        elif len(self.pt_stack) > 1:
            p2 = self.pt_stack.pop()
            p1 = self.pt_stack.pop()
            dist = gh.p2p_dist(p1, p2)/self.unitscale
            self.update_message_bar('%s %s' % (dist, self.units))
            self.launch_calc()
            self.calculator.putx(dist)

    def itemcoords(self, obj=None):
        """Print coordinates (in ECS) of selected element."""
        if not self.obj_stack:
            self.update_message_bar('Pick element from drawing.')
            self.set_sel_mode('items')
        elif self.obj_stack:
            elem = self.obj_stack.pop()
            if 'g' in self.canvas.gettags(elem):
                x1, y1, x2, y2 = self.canvas.coords(elem)
                print(self.cp2ep((x1, y1)), self.cp2ep((x2, y2)))
            else:
                print("This works only for 'geometry type' elements")

    def itemlength(self, obj=None):
        """Print length (in current units) of selected line, circle, or arc."""
        if not self.obj_stack:
            self.update_message_bar('Pick element from drawing.')
            self.set_sel_mode('items')
        elif self.obj_stack:
            elem = None
            length = 0
            for item in self.obj_stack.pop():
                if 'g' in self.canvas.gettags(item):
                    elem = self.curr[item]
                    if elem.type is 'gl':
                        p1, p2 = elem.coords
                        length = gh.p2p_dist(p1, p2) / self.unitscale
                    elif elem.type is 'gc':
                        length = math.pi*2*elem.coords[1]/self.unitscale
                    elif elem.type is 'cc':
                        length = math.pi*2*elem.coords[1]/self.unitscale
                    elif elem.type is 'ga':
                        pc, r, a0, a1 = elem.coords
                        ang = float(self.canvas.itemcget(item, 'extent'))
                        length = math.pi*r*ang/180/self.unitscale
                    if length:
                        self.launch_calc()
                        self.calculator.putx(length)

    def launch_calc(self):
        if not self.calculator:
            self.calculator = tkrpncalc.Calculator(self)
            #self.calculator.grab_set()
            self.calculator.geometry('+800+50')

    def on_close_menu_clicked(self):
        self.close_window()

    def close_window(self):
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.destroy()

    def on_about_menu_clicked(self, event=None):
        messagebox.showinfo(
            "About", "PYurCAD (pureCAD)\n Doug Blanding\n dblanding@gmail.com")

    # =======================================================================
    # Debug Tools
    # =======================================================================

    def show_op(self):
        print(self.op)

    def show_curr(self):
        pprint.pprint(self.curr)
        self.end()

    def show_prev(self):
        pprint.pprint(self.prev)
        self.end()

    def show_undo(self):
        pprint.pprint(self.undo_stack)
        self.end()

    def show_redo(self):
        pprint.pprint(self.redo_stack)
        self.end()

    def show_zoomscale(self):
        zoom_scale = self.canvas.scl.x
        print(zoom_scale)
        self.end()

    def show_calc(self):
        print(self.calculator)
        self.end()

    def show_dir_self(self):
        pprint.pprint(dir(self))
        self.end()

    def draw_line(self):
        self.current_item = self.canvas.create_line(
            self.start_x, self.start_y, self.end_x, self.end_y,
            fill=self.fill, width=self.width, arrow=self.arrow, dash=self.dash)

    def draw_workplane(self):
        start_x, start_y = self.ep2cp((-100, -100))
        end_x, end_y = self.ep2cp((400, 400))
        self.wp = self.canvas.create_rectangle(
            start_x, start_y, end_x, end_y, outline='#d5ffd5', fill=None, width=20)

    # =======================================================================
    # Construction
    # construction lines (clines) are "infinite" length lines
    # described by the equation:            ax + by + c = 0
    # they are defined by coefficients:     (a, b, c)
    #
    # circles are defined by coordinates:   (pc, r)
    # =======================================================================

    def cline_gen(self, cline, rubber=0, regen=False):
        '''Generate clines from coords (a,b,c) in ECS (mm) values.'''
        # extend clines 500 canvas units beyond edge of canvas
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        toplft = self.cp2ep((-500, -500))
        botrgt = self.cp2ep((w+500, h+500))
        trimbox = (toplft[0], toplft[1], botrgt[0], botrgt[1])
        endpts = gh.cline_box_intrsctn(cline, trimbox)
        if len(endpts) == 2:
            p1 = self.ep2cp(endpts[0])
            p2 = self.ep2cp(endpts[1])
            if rubber:
                if self.rubber:
                    self.canvas.coords(self.rubber, p1[0], p1[1], p2[0], p2[1])
                else:
                    self.rubber = self.canvas.create_line(p1[0], p1[1],
                                                          p2[0], p2[1],
                                                          fill=CONSTRCOLOR,
                                                          tags='r',
                                                          dash=self.CONSTR_DASH)
            else:
                if self.rubber:
                    self.canvas.delete(self.rubber)
                    self.rubber = None
                handle = self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                                 fill=CONSTRCOLOR, tags='c',
                                                 dash=self.CONSTR_DASH)
                self.canvas.tag_lower(handle)
                attribs = (cline, CONSTRCOLOR)
                e = entities.CL(attribs)
                self.curr[handle] = e
                if not regen:
                    self.cl_list.append(cline)

    def regen_all_cl(self, event=None):
        """Delete existing clines, remove them from self.curr, and regenerate

        This needs to be done after pan or zoom because the "infinite" length
        clines are not really infinite, they just hang off the edge a bit. So
        when zooming out, new clines need to be generated so they extend over
        the full canvas. Also, when zooming in, some clines are completely off
        the canvas, so we need a way to keep them from getting lost."""

        cl_keylist = [k for k, v in self.curr.items() if v.type is 'cl']
        for handle in cl_keylist:
            self.canvas.delete(handle)
            del self.curr[handle]
        for cline in self.cl_list:
            self.cline_gen(cline, regen=True)

    def hcl(self, pnt=None):
        """Create horizontal construction line from one point or y value."""

        message = 'Pick a pt or enter a value'
        message += self.shift_key_advice
        self.update_message_bar(message)
        proceed = 0
        if self.pt_stack:
            p = self.pt_stack.pop()
            proceed = 1
        elif self.float_stack:
            y = self.float_stack.pop()*self.unitscale
            p = (0, y)
            proceed = 1
        elif pnt:
            p = self.cp2ep(pnt)
            cline = gh.angled_cline(p, 0)
            self.cline_gen(cline, rubber=1)
        if proceed:
            cline = gh.angled_cline(p, 0)
            self.cline_gen(cline)

    def vcl(self, pnt=None):
        """Create vertical construction line from one point or x value."""

        message = 'Pick a pt or enter a value'
        message += self.shift_key_advice
        self.update_message_bar(message)
        proceed = 0
        if self.pt_stack:
            p = self.pt_stack.pop()
            proceed = 1
        elif self.float_stack:
            x = self.float_stack.pop()*self.unitscale
            p = (x, 0)
            proceed = 1
        elif pnt:
            p = self.cp2ep(pnt)
            cline = gh.angled_cline(p, 90)
            self.cline_gen(cline, rubber=1)
        if proceed:
            cline = gh.angled_cline(p, 90)
            self.cline_gen(cline)

    def hvcl(self, pnt=None):
        """Create a horizontal & vertical construction line pair at a point."""

        message = 'Pick a pt or enter coords x,y'
        message += self.shift_key_advice
        self.update_message_bar(message)
        if self.pt_stack:
            p = self.pt_stack.pop()
            self.cline_gen(gh.angled_cline(p, 0))
            self.cline_gen(gh.angled_cline(p, 90))

    def acl(self, pnt=None):
        """Create construction line thru a point, at a specified angle."""

        if not self.pt_stack:
            message = 'Pick a pt for angled construction line or enter coords'
            message += self.shift_key_advice
            self.update_message_bar(message)
        elif self.pt_stack and self.float_stack:
            p0 = self.pt_stack[0]
            ang = self.float_stack.pop()
            cline = gh.angled_cline(p0, ang)
            self.cline_gen(cline)
        elif len(self.pt_stack) > 1:
            p0 = self.pt_stack[0]
            p1 = self.pt_stack.pop()
            cline = gh.cnvrt_2pts_to_coef(p0, p1)
            self.cline_gen(cline)
        elif self.pt_stack and not self.float_stack:
            message = 'Specify 2nd point or enter angle in degrees'
            message += self.shift_key_advice
            self.update_message_bar(message)
            if pnt:
                p0 = self.pt_stack[0]
                p1 = self.cp2ep(pnt)
                ang = gh.p2p_angle(p0, p1)
                cline = gh.angled_cline(p0, ang)
                self.cline_gen(cline, rubber=1)

    def clrefang(self, p3=None):
        """Create a construction line at an angle relative to a reference."""

        if not self.pt_stack:
            message = 'Specify a pt for new construction line'
            message += self.shift_key_advice
            self.update_message_bar(message)
        elif not self.float_stack:
            self.update_message_bar('Enter offset angle in degrees')
        elif len(self.pt_stack) == 1:
            message = 'Pick first point on reference line'
            message += self.shift_key_advice
            self.update_message_bar(message)
        elif len(self.pt_stack) == 2:
            message = 'Pick second point on reference line'
            message += self.shift_key_advice
            self.update_message_bar(message)
        elif len(self.pt_stack) == 3:
            p3 = self.pt_stack.pop()
            p2 = self.pt_stack.pop()
            p1 = self.pt_stack.pop()
            baseangle = gh.p2p_angle(p2, p3)
            angoffset = self.float_stack.pop()
            ang = baseangle + angoffset
            cline = gh.angled_cline(p1, ang)
            self.cline_gen(cline)

    def abcl(self, pnt=None):
        """Create an angular bisector construction line."""

        if not self.float_stack and not self.pt_stack:
            message = 'Enter bisector factor (Default=.5) or specify vertex'
            message += self.shift_key_advice
            self.update_message_bar(message)
        elif not self.pt_stack:
            message = 'Specify vertex point'
            message += self.shift_key_advice
            self.update_message_bar(message)
        elif len(self.pt_stack) == 1:
            self.update_message_bar('Specify point on base line')
        elif len(self.pt_stack) == 2:
            self.update_message_bar('Specify second point')
            if pnt:
                f = .5
                if self.float_stack:
                    f = self.float_stack[-1]
                p2 = self.cp2ep(pnt)
                p1 = self.pt_stack[-1]
                p0 = self.pt_stack[-2]
                cline = gh.ang_bisector(p0, p1, p2, f)
                self.cline_gen(cline, rubber=1)
        elif len(self.pt_stack) == 3:
            f = .5
            if self.float_stack:
                f = self.float_stack[-1]
            p2 = self.pt_stack.pop()
            p1 = self.pt_stack.pop()
            p0 = self.pt_stack.pop()
            cline = gh.ang_bisector(p0, p1, p2, f)
            self.cline_gen(cline)

    def lbcl(self, pnt=None):
        """Create a linear bisector construction line."""

        if not self.pt_stack and not self.float_stack:
            message = 'Enter bisector factor (Default=.5) or specify first point'
            message += self.shift_key_advice
            self.update_message_bar(message)
        elif not self.pt_stack:
            message = 'Specify first point'
            message += self.shift_key_advice
            self.update_message_bar(message)
        elif len(self.pt_stack) == 1:
            message = 'Specify second point'
            message += self.shift_key_advice
            self.update_message_bar(message)
            if pnt:
                f = .5
                if self.float_stack:
                    f = self.float_stack[-1]
                p2 = self.cp2ep(pnt)
                p1 = self.pt_stack[-1]
                p0 = gh.midpoint(p1, p2, f)
                baseline = gh.cnvrt_2pts_to_coef(p1, p2)
                newline = gh.perp_line(baseline, p0)
                self.cline_gen(newline, rubber=1)
        elif len(self.pt_stack) == 2:
            f = .5
            if self.float_stack:
                f = self.float_stack[-1]
            p2 = self.pt_stack.pop()
            p1 = self.pt_stack.pop()
            p0 = gh.midpoint(p1, p2, f)
            baseline = gh.cnvrt_2pts_to_coef(p1, p2)
            newline = gh.perp_line(baseline, p0)
            self.cline_gen(newline)

    def parcl(self, pnt=None):
        """Create parallel clines in one of two modes:

        1) At a specified offset distance from selected straight element, or
        2) Parallel to a selected straight element through a selected point."""

        if not self.obj_stack and not self.float_stack:
            self.update_message_bar(
                'Pick a straight element or enter an offset distance')
            self.set_sel_mode('items')
        elif self.float_stack:      # mode 1
            if not self.obj_stack:
                self.set_sel_mode('items')
                self.update_message_bar(
                    'Pick a straight element to be parallel to')
            elif not self.pt_stack:
                self.set_sel_mode('pnt')
                self.update_message_bar('Pick on (+) side of line')
            else:
                obj = self.obj_stack.pop()
                p = self.pt_stack.pop()
                item = obj[0]
                baseline = (0, 0, 0)
                if self.canvas.type(item) == 'line':
                    if 'c' in self.canvas.gettags(item):
                        baseline = self.curr[item].coords
                    elif 'g' in self.canvas.gettags(item):
                        p1, p2 = self.curr[item].coords
                        baseline = gh.cnvrt_2pts_to_coef(p1, p2)
                d = self.float_stack[-1]*self.unitscale
                cline1, cline2 = gh.para_lines(baseline, d)
                p1 = gh.proj_pt_on_line(cline1, p)
                p2 = gh.proj_pt_on_line(cline2, p)
                d1 = gh.p2p_dist(p1, p)
                d2 = gh.p2p_dist(p2, p)
                if d1 < d2:
                    self.cline_gen(cline1)
                else:
                    self.cline_gen(cline2)
        elif self.obj_stack:        # mode 2
            obj = self.obj_stack[-1]
            if not obj:
                return
            item = obj[0]
            baseline = (0, 0, 0)
            if self.canvas.type(item) == 'line':
                if 'c' in self.canvas.gettags(item):
                    baseline = self.curr[item].coords
                elif 'g' in self.canvas.gettags(item):
                    p1, p2 = self.curr[item].coords
                    baseline = gh.cnvrt_2pts_to_coef(p1, p2)
            if not self.pt_stack:
                self.set_sel_mode('pnt')
                message = 'Select point for new parallel line'
                message += self.shift_key_advice
                self.update_message_bar(message)
                if pnt:
                    p = self.cp2ep(pnt)
                    parline = gh.para_line(baseline, p)
                    self.cline_gen(parline, rubber=1)
            else:
                p = self.pt_stack.pop()
                newline = gh.para_line(baseline, p)
                self.cline_gen(newline)

    def perpcl(self, pnt=None):
        """Create a perpendicular cline through a selected point."""

        if not self.obj_stack:
            self.update_message_bar('Pick line to be perpendicular to')
            self.set_sel_mode('items')
        else:
            message = 'Select point for perpendicular construction'
            message += self.shift_key_advice
            self.update_message_bar(message)
            self.set_sel_mode('pnt')
            obj = self.obj_stack[0]
            if not obj:
                return
            item = obj[0]
            baseline = (0, 0, 0)
            if self.canvas.type(item) == 'line':
                if 'c' in self.canvas.gettags(item):
                    baseline = self.curr[item].coords
                elif 'g' in self.canvas.gettags(item):
                    p1, p2 = self.curr[item].coords
                    baseline = gh.cnvrt_2pts_to_coef(p1, p2)
            if self.pt_stack:
                p = self.pt_stack.pop()
                newline = gh.perp_line(baseline, p)
                self.cline_gen(newline)
                self.obj_stack.pop()
            elif pnt:
                p = self.cp2ep(pnt)
                newline = gh.perp_line(baseline, p)
                self.cline_gen(newline, rubber=1)

    def cltan1(self, p1=None):
        '''Create a construction line through a point, tangent to a circle.'''

        if not self.obj_stack:
            self.update_message_bar('Pick circle')
            self.set_sel_mode('items')
        elif self.obj_stack and not self.pt_stack:
            self.update_message_bar('specify point')
            self.set_sel_mode('pnt')
        elif self.obj_stack and self.pt_stack:
            item = self.obj_stack.pop()[0]
            p = self.pt_stack.pop()
            circ = None
            if self.curr[item].type in ('gc', 'cc'):
                circ = self.curr[item].coords
            if circ:
                p1, p2 = gh.line_tan_to_circ(circ, p)
                cline1 = gh.cnvrt_2pts_to_coef(p1, p)
                cline2 = gh.cnvrt_2pts_to_coef(p2, p)
                self.cline_gen(cline1)
                self.cline_gen(cline2)

    def cltan2(self, p1=None):
        '''Create a construction line tangent to 2 circles.'''

        if not self.obj_stack:
            self.update_message_bar('Pick first circle')
            self.set_sel_mode('items')
        elif len(self.obj_stack) == 1:
            self.update_message_bar('Pick 2nd circle')
        elif len(self.obj_stack) == 2:
            item1 = self.obj_stack.pop()[0]
            item2 = self.obj_stack.pop()[0]
            circ1 = circ2 = None
            if self.curr[item1].type in ('gc', 'cc'):
                circ1 = self.curr[item1].coords
            if self.curr[item2].type in ('gc', 'cc'):
                circ2 = self.curr[item2].coords
            if circ1 and circ2:
                p1, p2 = gh.line_tan_to_2circs(circ1, circ2)
                cline = gh.cnvrt_2pts_to_coef(p1, p2)
                self.cline_gen(cline)

    def ccirc_gen(self, cc, tag='c'):
        """Create constr circle from a CC object. Save to self.curr."""

        coords, color = cc.get_attribs()
        handle = self.circ_draw(coords, color, tag=tag)
        self.curr[handle] = cc
        self.canvas.tag_lower(handle)

    def ccirc(self, p1=None):
        '''Create a construction circle from center point and
        perimeter point or radius.'''

        self.circ(p1=p1, constr=1)

    def cccirc(self, p1=None):
        '''Create a construction circle concentric to an existing circle,
        at a "relative" radius.'''

        if not self.obj_stack:
            self.set_sel_mode('items')
            self.update_message_bar('Select existing circle')
        elif self.obj_stack and not (self.float_stack or self.pt_stack):
            item = self.obj_stack[0][0]
            self.coords = None
            if self.curr[item].type in ('cc', 'gc'):
                self.coords = self.curr[item].coords
            self.set_sel_mode('pnt')
            self.update_message_bar(
                'Enter relative radius or specify point on new circle')
            if self.coords and p1:
                pc, r0 = self.coords
                ep = self.cp2ep(p1)
                r = gh.p2p_dist(pc, ep)
                self.circ_builder((pc, r), rubber=1)
        elif self.coords and self.float_stack:
            pc, r0 = self.coords
            self.obj_stack.pop()
            r = self.float_stack.pop()*self.unitscale + r0
            self.circ_builder((pc, r), constr=1)
        elif self.coords and self.pt_stack:
            pc, r0 = self.coords
            self.obj_stack.pop()
            p = self.pt_stack.pop()
            r = gh.p2p_dist(pc, p)
            self.circ_builder((pc, r), constr=1)

    def cc3p(self, p3=None):
        """Create a constr circle from 3 pts on circle."""

        if not self.pt_stack:
            self.update_message_bar('Pick first point on circle')
        elif len(self.pt_stack) == 1:
            self.update_message_bar('Pick second point on circle')
        elif len(self.pt_stack) == 2:
            self.update_message_bar('Pick third point on circle')
            if p3:
                p3 = self.cp2ep(p3)
                p2 = self.pt_stack[1]
                p1 = self.pt_stack[0]
                tup = gh.cr_from_3p(p1, p2, p3)
                if tup:
                    pc, r = tup
                    self.circ_builder((pc, r,), rubber=1)
        elif len(self.pt_stack) == 3:
            p3 = self.pt_stack.pop()
            p2 = self.pt_stack.pop()
            p1 = self.pt_stack.pop()
            pc, r = gh.cr_from_3p(p1, p2, p3)
            self.circ_builder((pc, r), constr=1)

    # =======================================================================
    # Geometry
    # geometry line parameters are stored in GL objects.
    # geometry lines are finite length segments between 2 pts: p1, p2
    # lines are defined by coordinates:         (p1, p2)
    #
    # =======================================================================

    def line_draw(self, coords, color, arrow=None, tag='g'):
        """Create and display line segment between two pts. Return ID.

        This is a low level method that accesses the canvas directly &
        returns tkid. The caller can save to self.curr if needed."""
        p1, p2 = coords
        xa, ya = self.ep2cp(p1)
        xb, yb = self.ep2cp(p2)
        tkid = self.canvas.create_line(xa, ya, xb, yb,
                                       fill=color, tags=tag, arrow=arrow)
        return tkid

    def gline_gen(self, gl):
        """Create line segment from gl object. Store {ID: obj} in self.curr.

        This provides access to line_gen using a gl object."""

        coords, color = gl.get_attribs()
        tkid = self.line_draw(coords, color)
        self.curr[tkid] = gl

    def line(self, p1=None):
        '''Create line segment between 2 points. Enable 'rubber line' mode'''

        rc = RUBBERCOLOR
        if not self.pt_stack:
            message = 'Pick start point of line or enter coords'
            message += self.shift_key_advice
            self.update_message_bar(message)
        elif len(self.pt_stack) > 1:
            p2 = self.pt_stack.pop()
            p1 = self.pt_stack.pop()
            coords = (p1, p2)
            attribs = (coords, GEOMCOLOR)
            e = entities.GL(attribs)
            self.gline_gen(e)
            if self.rubber:
                self.canvas.delete(self.rubber)
                self.rubber = None
            if self.rtext:
                self.canvas.delete(self.rtext)
                self.rtext = None
        elif self.pt_stack and p1:
            p0 = self.pt_stack[-1]
            x, y = self.ep2cp(p0)   # fixed first point (canvas coords)
            xr, yr = p1             # rubber point (canvas coords)
            x0, y0 = p0             # fixed first point (ECS)
            x1, y1 = self.cp2ep(p1)  # rubber point (ECS)
            strcoords = "(%1.3f, %1.3f)" % ((x1-x0)/self.unitscale,
                                            (y1-y0)/self.unitscale)
            if self.rubber:
                self.canvas.coords(self.rubber, x, y, xr, yr)
            else:
                self.rubber = self.canvas.create_line(x, y, xr, yr,
                                                      fill=rc, tags='r')
            if self.rtext:
                self.canvas.delete(self.rtext)
            self.rtext = self.canvas.create_text(xr+20, yr-20,
                                                 text=strcoords,
                                                 fill=TEXTCOLOR)
            self.update_message_bar('Specify end point of line')

    def poly(self, p1=None):
        '''Create chain of line segments, enabling 'rubber line' mode.'''

        if not self.pt_stack:
            self.poly_start_pt = None
            message = 'Pick start point or enter coords'
            message += self.shift_key_advice
            self.update_message_bar(message)
        elif len(self.pt_stack) > 1:
            lastpt = self.pt_stack[-1]
            self.line()     # This will pop 2 points off stack
            if not gh.same_pt_p(self.poly_start_pt, lastpt):
                self.pt_stack.append(lastpt)
        elif self.pt_stack and p1:
            if not self.poly_start_pt:
                self.poly_start_pt = self.pt_stack[-1]
            self.line(p1)   # This will generate rubber line
            self.update_message_bar('Pick next point or enter coords')

    def rect(self, p2=None):
        '''Generate a rectangle from 2 diagonally opposite corners.'''

        rc = RUBBERCOLOR
        if not self.pt_stack:
            self.update_message_bar(
                'Pick first corner of rectangle or enter coords')
        elif len(self.pt_stack) == 1 and p2:
            self.update_message_bar(
                'Pick opposite corner of rectangle or enter coords')
            p1 = self.pt_stack[0]
            x1, y1 = self.ep2cp(p1)
            x2, y2 = p2
            if self.rubber:
                self.canvas.coords(self.rubber, x1, y1, x2, y2)
            else:
                self.rubber = self.canvas.create_rectangle(x1, y1, x2, y2,
                                                           outline=rc,
                                                           tags='r')
        elif len(self.pt_stack) > 1:
            x2, y2 = self.pt_stack.pop()
            x1, y1 = self.pt_stack.pop()
            a = (x1, y1)
            b = (x2, y1)
            c = (x2, y2)
            d = (x1, y2)
            sides = ((a, b), (b, c), (c, d), (d, a))
            for p in sides:
                coords = (p[0], p[1])
                attribs = (coords, GEOMCOLOR)
                e = entities.GL(attribs)
                self.gline_gen(e)
            if self.rubber:
                self.canvas.delete(self.rubber)
                self.rubber = None

    # =======================================================================
    # geometry circle parameters are stored in GC objects.
    # circles are defined by coordinates:       (pc, r)
    # =======================================================================

    def circ_draw(self, coords, color, tag):
        """Draw a circle on the canvas and return the tkid handle.

        This low level method accesses the canvas directly & returns tkid.
        The caller should save handle & entity_obj to self.curr if needed."""

        if tag == 'c':
            dash = self.CONSTR_DASH
        else:
            dash = None
        ctr, rad = coords
        x, y = self.ep2cp(ctr)
        r = self.canvas.w2c_dx(rad)
        handle = self.canvas.create_oval(x-r, y-r, x+r, y+r,
                                         outline=color, dash=dash,
                                         tags=tag)
        return handle

    def gcirc_gen(self, gc, tag='g'):
        """Create geometry circle from a GC object. Save to self.curr."""

        coords, color = gc.get_attribs()
        handle = self.circ_draw(coords, color, tag=tag)
        self.curr[handle] = gc

    def circ_builder(self, coords, rubber=0, constr=0):
        """Create circle at center pc, radius r in engineering (mm) coords.

        Handle rubber circles, construction, and geom circles."""

        ctr, rad = coords       # ECS
        x, y = self.ep2cp(ctr)
        r = self.canvas.w2c_dx(rad)
        if rubber:
            color = RUBBERCOLOR
            tag = 'r'
            if self.rubber:
                self.canvas.coords(self.rubber, x-r, y-r, x+r, y+r)
            else:
                self.rubber = self.canvas.create_oval(x-r, y-r, x+r, y+r,
                                                      outline=color,
                                                      tags=tag)
        else:
            if constr:  # Constr circle
                attribs = (coords, CONSTRCOLOR)
                e = entities.CC(attribs)
                self.ccirc_gen(e)
            else:  # geom circle
                attribs = (coords, GEOMCOLOR)
                e = entities.GC(attribs)
                self.gcirc_gen(e)
            if self.rubber:
                self.canvas.delete(self.rubber)
                self.rubber = None

    def circ(self, p1=None, constr=0):
        '''Create a circle from center pnt and perimeter pnt or radius.'''

        finish = 0
        if not self.pt_stack:
            self.update_message_bar('Pick center of circle or enter coords')
        elif len(self.pt_stack) == 1 and p1 and not self.float_stack:
            self.update_message_bar('Specify point on circle or radius')
            pc = self.pt_stack[0]
            p1 = self.cp2ep(p1)
            r = gh.p2p_dist(pc, p1)
            coords = (pc, r)
            self.circ_builder(coords, rubber=1)
        elif len(self.pt_stack) > 1:
            p1 = self.pt_stack.pop()
            pc = self.pt_stack.pop()
            r = gh.p2p_dist(pc, p1)
            finish = 1
        elif self.pt_stack and self.float_stack:
            pc = self.pt_stack.pop()
            r = self.float_stack.pop()*self.unitscale
            finish = 1
        if finish:
            self.circ_builder((pc, r), constr=constr)

    # =======================================================================
    # geometry arc parameters are stored in GA objects
    # arcs are defined by coordinates:  (pc, r, a0, a1)
    # where:    pc = (x, y) coords of center point
    #           r = radius
    #           a0 = start angle in degrees
    #           a1 = end angle in degrees
    # =======================================================================

    def garc_gen(self, ga, tag='g'):
        """Create geometry arc from GA object (coords in ECS)

        pc  = arc center pt
        rad = radius of arc center in mm
        a0  = start angle in degrees measured CCW from 3 o'clock position
        a1  = end angle in degrees measured CCW from 3 o'clock position
        """
        coords, color = ga.get_attribs()
        pc, rad, a0, a1 = coords
        ext = a1-a0
        if ext < 0:
            ext += 360
        x, y = self.ep2cp(pc)
        r = self.canvas.w2c_dx(rad)
        x1 = x-r
        y1 = y-r
        x2 = x+r
        y2 = y+r
        if tag is 'r':
            if self.rubber:
                self.canvas.coords(self.rubber, x1, y1, x2, y2,)
                self.canvas.itemconfig(self.rubber, start=a0, extent=ext)
            else:
                self.rubber = self.canvas.create_arc(x1, y1, x2, y2,
                                                     start=a0, extent=ext,
                                                     style='arc', tags=tag,
                                                     outline=color)
        else:
            handle = self.canvas.create_arc(x1, y1, x2, y2,
                                            start=a0, extent=ext, style='arc',
                                            outline=color, tags=tag)
            self.curr[handle] = ga

    def arcc2p(self, p2=None):
        """Create an arc from center pt, start pt and end pt."""

        if not self.pt_stack:
            self.update_message_bar('Specify center of arc')
        elif len(self.pt_stack) == 1:
            self.update_message_bar('Specify start point of arc')
        elif len(self.pt_stack) == 2:
            self.update_message_bar('Specify end point of arc')
            if p2:
                p2 = self.cp2ep(p2)
                p1 = self.pt_stack[1]
                p0 = self.pt_stack[0]
                r = gh.p2p_dist(p0, p1)
                ang1 = gh.p2p_angle(p0, p1)
                ang2 = gh.p2p_angle(p0, p2)
                coords = (p0, r, ang1, ang2)
                attribs = (coords, RUBBERCOLOR)
                e = entities.GA(attribs)
                self.garc_gen(e, tag='r')
        elif len(self.pt_stack) == 3:
            p2 = self.pt_stack.pop()
            p1 = self.pt_stack.pop()
            p0 = self.pt_stack.pop()
            r = gh.p2p_dist(p0, p1)
            ang1 = gh.p2p_angle(p0, p1)
            ang2 = gh.p2p_angle(p0, p2)
            coords = (p0, r, ang1, ang2)
            attribs = (coords, GEOMCOLOR)
            e = entities.GA(attribs)
            self.garc_gen(e)

    def arc3p(self, p3=None):
        """Create an arc from start pt, end pt, and 3rd pt on the arc."""

        if not self.pt_stack:
            self.update_message_bar('Specify start of arc')
        elif len(self.pt_stack) == 1:
            self.update_message_bar('Specify end of arc')
        elif len(self.pt_stack) == 2:
            self.update_message_bar('Specify point on arc')
            if p3:
                p3 = self.cp2ep(p3)
                p2 = self.pt_stack[1]
                p1 = self.pt_stack[0]
                tup = gh.cr_from_3p(p1, p2, p3)
                if tup:   # tup=None if p1, p2, p3 are colinear
                    pc, r = tup
                    ang1 = gh.p2p_angle(pc, p1)
                    ang2 = gh.p2p_angle(pc, p2)
                    if not gh.pt_on_RHS_p(p3, p1, p2):
                        ang2, ang1 = ang1, ang2
                    coords = (pc, r, ang1, ang2)
                    attribs = (coords, RUBBERCOLOR)
                    e = entities.GA(attribs)
                    self.garc_gen(e, tag='r')
        elif len(self.pt_stack) == 3:
            p3 = self.pt_stack.pop()
            p2 = self.pt_stack.pop()
            p1 = self.pt_stack.pop()
            pc, r = gh.cr_from_3p(p1, p2, p3)
            ang1 = gh.p2p_angle(pc, p1)
            ang2 = gh.p2p_angle(pc, p2)
            if not gh.pt_on_RHS_p(p3, p1, p2):
                ang2, ang1 = ang1, ang2
            coords = (pc, r, ang1, ang2)
            attribs = (coords, GEOMCOLOR)
            e = entities.GA(attribs)
            self.garc_gen(e)
            if self.rubber:
                self.canvas.delete(self.rubber)
                self.rubber = None

    def slot(self, p1=None):
        if not self.pt_stack:
            self.update_message_bar('Specify first point for slot')
        elif len(self.pt_stack) == 1:
            self.update_message_bar('Specify second point for slot')
        elif len(self.pt_stack) == 2 and not self.float_stack:
            self.update_message_bar('Enter slot width')
        elif len(self.pt_stack) == 2 and self.float_stack:
            p2 = self.pt_stack.pop()
            p1 = self.pt_stack.pop()
            w = self.float_stack.pop()*self.unitscale
            baseline = gh.cnvrt_2pts_to_coef(p1, p2)
            crossline1 = gh.perp_line(baseline, p1)
            crossline2 = gh.perp_line(baseline, p2)
            circ1 = (p1, w/2)
            circ2 = (p2, w/2)
            p1e = gh.extendline(p2, p1, w/2)
            paraline1, paraline2 = gh.para_lines(baseline, w/2)
            p1a = gh.intersection(paraline1, crossline1)
            p1b = gh.intersection(paraline2, crossline1)
            self.pt_stack.extend([p1a, p1b, p1e])
            self.arc3p()
            p2e = gh.extendline(p1, p2, w/2)
            p2a = gh.intersection(paraline1, crossline2)
            p2b = gh.intersection(paraline2, crossline2)
            self.pt_stack.extend([p2a, p2b, p2e])
            self.arc3p()
            self.gline_gen(entities.GL(((p1a, p2a), GEOMCOLOR)))
            self.gline_gen(entities.GL(((p1b, p2b), GEOMCOLOR)))

    # =======================================================================
    # Modify geometry
    # =======================================================================

    def split(self, p1=None):
        """Split 1 line segment into 2 (at a selected point.)"""

        if not self.obj_stack:
            self.set_sel_mode('items')
            self.update_message_bar('Pick straight line to split')
        elif self.obj_stack and not self.pt_stack:
            self.set_sel_mode('pnt')
            message = 'Pick point for split'
            message += self.shift_key_advice
            self.update_message_bar(message)
        else:
            # When picking a geometry line that overlays a
            # construction line, need to ignore the c-line
            item_tuple = self.obj_stack.pop()
            for item in item_tuple:
                entity = self.curr[item]
                if entity.type is 'gl':
                    line = item
                    p0 = self.pt_stack.pop()
                    (p1, p2), clr = self.curr[line].get_attribs()
                    del self.curr[line]
                    self.canvas.delete(line)
                    self.gline_gen(entities.GL(((p0, p1), GEOMCOLOR)))
                    self.gline_gen(entities.GL(((p0, p2), GEOMCOLOR)))

    def join(self, p1=None):
        """Join 2 adjacent line segments into 1. """

        if not self.obj_stack:
            self.set_sel_mode('items')
            self.update_message_bar('Pick first line to join')
        elif len(self.obj_stack) == 1:
            self.update_message_bar('Pick second line to join')
        elif len(self.obj_stack) == 2:
            item2 = self.obj_stack.pop()[0]
            item1 = self.obj_stack.pop()[0]
            for item in (item1, item2):
                if not (self.canvas.type(item) == 'line' and
                        'g' in self.canvas.gettags(item)):
                    print('Incorrect types of items picked for join')
                    return
            gl1 = self.curr[item1]
            gl2 = self.curr[item2]
            coords1, clr = gl1.get_attribs()
            coords2, clr = gl2.get_attribs()
            pts = gh.find_common_pt(coords1, coords2)
            if pts:
                cp, ep1, ep2 = pts
            else:
                print('No common pt found')
                return
            for item in (item1, item2):
                del self.curr[item]
                self.canvas.delete(item)
            self.gline_gen(entities.GL(((ep1, ep2), GEOMCOLOR)))

    def fillet(self, p1=None):
        """Create a fillet of radius r at the common corner of 2 lines."""

        if not self.obj_stack and not self.float_stack:
            self.update_message_bar('Enter radius for fillet')
        elif not self.obj_stack:
            self.set_sel_mode('items')
            self.update_message_bar('Pick corner to apply fillet')
        elif self.obj_stack and self.float_stack:
            rw = self.float_stack[-1]*self.unitscale
            rc = self.canvas.w2c_dx(rw)
            found = self.obj_stack.pop()
            items = []
            for item in found:
                if self.canvas.type(item) == 'line' and \
                   'g' in self.canvas.gettags(item):
                    items.append(item)
            if len(items) == 2:
                line1coords, color = self.curr[items[0]].get_attribs()
                line2coords, color = self.curr[items[1]].get_attribs()
                pts = gh.find_common_pt(line1coords,
                                     line2coords)
                if pts:
                    # common pt, other end pt1, other end pt2
                    cp, ep1, ep2 = pts
                else:
                    print('No common point found')
                    return
                # find arc center and tangent points
                ctr, tp1, tp2 = gh.find_fillet_pts(rw, cp, ep1, ep2)
                # shorten adjacent sides
                for item in items:
                    del self.curr[item]
                    self.canvas.delete(item)
                self.gline_gen(entities.GL(((ep1, tp1), GEOMCOLOR)))
                self.gline_gen(entities.GL(((ep2, tp2), GEOMCOLOR)))

                # make arc, but first, get the order of tp1 and tp2 right
                a1 = math.atan2(tp1[1]-ctr[1], tp1[0]-ctr[0])
                a2 = math.atan2(tp2[1]-ctr[1], tp2[0]-ctr[0])
                if (a2-a1) > math.pi or -math.pi < (a2-a1) < 0:
                    tp1, tp2 = tp2, tp1
                self.pt_stack = [ctr, tp1, tp2]
                self.arcc2p()

    def translate(self, p=None):
        """Move (or copy) selected geometry item(s) by two points.

        To copy items, enter number of copies.
        Otherwise, item(s) will be moved (not copied)."""

        if not self.obj_stack and not self.pt_stack and \
           not self.float_stack:
            self.set_sel_mode('items')
            self.allow_list = 1
            msg = 'Specify number of copies or select geometry item(s) to move'
            self.update_message_bar(msg)
        elif not self.obj_stack and not self.pt_stack:
            self.update_message_bar('Select geometry item(s) to move')
        elif self.obj_stack and not self.pt_stack:
            self.set_sel_mode('pnt')
            self.allow_list = 0
            self.update_message_bar('Select "FROM" point')
        elif self.obj_stack and len(self.pt_stack) == 1:
            self.update_message_bar('Select "TO" point')
        elif self.obj_stack and len(self.pt_stack) == 2:
            if self.float_stack:
                repeat = int(self.float_stack.pop())
            else:
                repeat = 0
            p1 = self.pt_stack.pop()
            p0 = self.pt_stack.pop()
            handles = self.obj_stack.pop()
            dp = gh.sub_pt(p1, p0)
            cx, cy = gh.sub_pt(self.ep2cp(p1), self.ep2cp(p0))
            items = [self.curr[handle] for handle in handles]
            delete_original = False
            if not repeat:  # move, (not copy)
                delete_original = True
                repeat = 1
            for item in items:
                if item.type is 'gl':
                    pnts, _ = item.get_attribs()
                    for x in range(repeat):
                        pnts = (gh.add_pt(pnts[0], dp),
                                gh.add_pt(pnts[1], dp))
                        gl = entities.GL((pnts, GEOMCOLOR))
                        self.gline_gen(gl)
                elif item.type is 'gc':
                    pnts, _ = item.get_attribs()
                    for x in range(repeat):
                        pnts = (gh.add_pt(pnts[0], dp), pnts[1])
                        gc = entities.GC((pnts, GEOMCOLOR))
                        self.gcirc_gen(gc)
                elif item.type is 'ga':
                    pnts, _ = item.get_attribs()
                    for x in range(repeat):
                        pnts = (gh.add_pt(pnts[0], dp),
                                pnts[1], pnts[2], pnts[3])
                        ga = entities.GA((pnts, GEOMCOLOR))
                        self.garc_gen(ga)
                else:
                    print('Only geometry type items can be moved with this command.')
            if delete_original:
                for handle in handles:
                    self.canvas.delete(handle)
                    del self.curr[handle]

    def rotate(self, p=None):
        """Move (or copy) selected geometry item(s) by rotating about a point.

        To copy items, enter number of copies.
        Otherwise, item(s) will be moved (not copied)."""

        if not self.obj_stack and not self.pt_stack and not self.float_stack:
            self.repeat = 0   # No copies. "move" mode is intended.
            self.set_sel_mode('items')
            self.allow_list = 1
            msg = 'Specify number of copies or select geometry item(s) to move'
            self.update_message_bar(msg)
        elif not self.obj_stack and not self.pt_stack:
            self.update_message_bar('Select geometry item(s) to move')
        elif self.obj_stack and not self.pt_stack:
            if self.float_stack:
                self.repeat = int(self.float_stack.pop())   # number of copies
            self.set_sel_mode('pnt')
            self.allow_list = 0
            self.update_message_bar('Select center of rotation')
        elif self.obj_stack and self.pt_stack and not self.float_stack:
            self.update_message_bar('Specify angle of rotation in degrees')
        elif self.obj_stack and self.pt_stack and self.float_stack:
            ctr = self.pt_stack.pop()
            handles = self.obj_stack.pop()
            A = self.float_stack.pop()
            items = [self.curr[handle] for handle in handles]
            delete_original = False
            if not self.repeat:  # move, (not copy)
                delete_original = True
                self.repeat = 1
            for item in items:
                if item.type is 'gl':
                    pnts, _ = item.get_attribs()
                    for x in range(self.repeat):
                        pnts = (gh.rotate_pt(pnts[0], A, ctr),
                                gh.rotate_pt(pnts[1], A, ctr))
                        gl = entities.GL((pnts, GEOMCOLOR))
                        self.gline_gen(gl)
                elif item.type is 'gc':
                    pnts, _ = item.get_attribs()
                    for x in range(self.repeat):
                        pnts = (gh.rotate_pt(pnts[0], A, ctr), pnts[1])
                        gc = entities.GC((pnts, GEOMCOLOR))
                        self.gcirc_gen(gc)
                elif item.type is 'ga':
                    pnts, _ = item.get_attribs()
                    for x in range(self.repeat):
                        pnts = (gh.rotate_pt(pnts[0], A, ctr),
                                pnts[1], pnts[2] + A, pnts[3] + A)
                        ga = entities.GA((pnts, GEOMCOLOR))
                        self.garc_gen(ga)
                else:
                    print('Only geometry type items can be moved with this command.')
            if delete_original:
                for handle in handles:
                    self.canvas.delete(handle)
                    del self.curr[handle]

    # =======================================================================
    # Dimensions
    # linear dimensions have coords:    (p1, p2, p3, d)
    # where p1 and p2 are the points being dimensioned,
    # d is the direction along which the dimension is being measured,
    # represented by the coefficients of a cline: d = (a, b, c)
    # and p3 is the location of the center of the dimension text.
    # =======================================================================

    def dim_draw(self, dim_obj):
        """Create a linear dimension from dim_obj and return handle.

        There are 5 individual components that make up a linear dimension:
        The text, 2 dimension lines, and 2 extension lines. Each component
        shares a tag which is unique to this 'group' of 5 components. This
        permits all components to be found when any component is selected
        on the canvas. It is intended to treat dimensions as 'disposable'.
        For example, to move a dimension, just delete all 5 components,
        then regenerate them in the new position."""

        (p1, p2, p3, c), color = dim_obj.get_attribs()
        dimdir = gh.para_line(c, p3)
        p1b = gh.proj_pt_on_line(dimdir, p1)
        p2b = gh.proj_pt_on_line(dimdir, p2)
        d = gh.p2p_dist(p1b, p2b) / self.unitscale
        text = '%.3f' % d
        x3, y3 = self.ep2cp(p3)
        tkid = self.canvas.create_text(x3, y3, fill=color, text=text)
        dgidtag = 'd%s' % tkid  # unique dimension group ID tag
        self.canvas.itemconfig(tkid, tags=('d', dgidtag))
        # create dimension lines
        xa, ya, xb, yb = self.canvas.bbox(tkid)
        xa, ya = self.cp2ep((xa, ya))
        xb, yb = self.cp2ep((xb, yb))
        innerpts = gh.cline_box_intrsctn(dimdir, (xa, ya, xb, yb))
        ip1 = gh.closer(p1b, innerpts[0], innerpts[1])
        ip2 = gh.closer(p2b, innerpts[0], innerpts[1])
        self.line_draw((ip1, p1b), color=color, tag=('d', dgidtag), arrow=LAST)
        self.line_draw((ip2, p2b), color=color, tag=('d', dgidtag), arrow=LAST)
        # create extension lines
        # make ext line gap appear same size irrespective of zoom
        gap = self.canvas.c2w_dx(self.dimgap)
        p1a = gh.shortenline(p1b, p1, gap)
        p2a = gh.shortenline(p2b, p2, gap)
        p1c = gh.extendline(p1, p1b, gap)
        p2c = gh.extendline(p2, p2b, gap)
        if p1a and p2a and p1c and p2c:
            self.line_draw((p1a, p1c), color=color, tag=('d', dgidtag))
            self.line_draw((p2a, p2c), color=color, tag=('d', dgidtag))
        return dgidtag

    def dim_gen(self, dim_obj):
        """Generate dimension from dim_obj and save to self.curr."""

        dgid = self.dim_draw(dim_obj)
        self.curr[dgid] = dim_obj

    def regen_all_dims(self, event=None):
        """Delete all existing dimensions, and regenerate.

        This needs to be done after zoom because the dimension text does
        not change size with zoom."""

        dimlist = [v for v in self.curr.values() if v.type == 'dl']
        self.del_all_d()
        for ent_obj in dimlist:
            self.dim_gen(ent_obj)

    def dim_lin(self, p=None, d=(0, 1, 0)):
        """Manually create a linear dimension obj. Add to self.curr."""

        rc = RUBBERCOLOR
        if not self.pt_stack:
            self.update_message_bar('Pick 1st point.')
        elif len(self.pt_stack) == 1:
            self.update_message_bar('Pick 2nd point.')
        elif len(self.pt_stack) == 2 and p:
            self.update_message_bar('Pick location for dimension text.')
            p3 = self.cp2ep(p)
            p2 = self.pt_stack[1]
            p1 = self.pt_stack[0]
            if not gh.same_pt_p(p3, p2):
                if self.rubber:
                    for each in self.canvas.find_withtag(self.rubber):
                        self.canvas.delete(each)
                att = ((p1, p2, p3, d), rc)
                rubber_ent = entities.DL(att)
                self.rubber = self.dim_draw(rubber_ent)
        elif len(self.pt_stack) == 3:
            if self.rubber:
                for each in self.canvas.find_withtag(self.rubber):
                    self.canvas.delete(each)
            p3 = self.pt_stack.pop()
            p2 = self.pt_stack.pop()
            p1 = self.pt_stack.pop()
            coords = (p1, p2, p3, d)
            attribs = (coords, DIMCOLOR)
            dl = entities.DL(attribs)
            dgid = self.dim_draw(dl)
            self.curr[dgid] = dl

    def dim_h(self, p=None):
        """Create a horizontal dimension"""

        self.dim_lin(p)

    def dim_v(self, p=None):
        """Create a vertical dimension"""

        self.dim_lin(p, d=(1, 0, 0))

    def dim_par(self, p=None):
        """Create a dimension parallel to a selected line element."""

        if not self.obj_stack:
            self.set_sel_mode('items')
            self.update_message_bar(
                'Pick linear element to define direction of dimension.')
        elif self.obj_stack:
            self.set_sel_mode('pnt')
            item = self.obj_stack[-1][0]
            if self.canvas.type(item) == 'line':
                tags = self.canvas.gettags(item)
                d = None
                if 'c' in tags:
                    d = self.curr[item].coords
                elif 'g' in tags:
                    p1, p2 = self.curr[item].coords
                    d = gh.cnvrt_2pts_to_coef(p1, p2)
                if d:
                    self.dim_lin(p, d)

    # =======================================================================
    # Text
    # Text parameters are stored as attributes of a TX object.
    # attribs = (x,y), text, style, size, color
    # where (x, y) are the coordinates of the center of the text.
    # style, size, color define the font.
    # =======================================================================

    def text_draw(self, tx, tag='t'):
        """Draw text on canvas and return handle."""

        x, y = tx.coords
        text = tx.text
        style = tx.style
        size = tx.size
        color = tx.color
        u, v = self.ep2cp((x, y))
        zoom_scale = self.canvas.scl.x
        zoomed_font_size = int(size * zoom_scale)  # tk canvas requires int
        font = (style, zoomed_font_size)
        handle = self.canvas.create_text(u, v, text=text, tags=tag,
                                         fill=color, font=font)
        return handle

    def text_gen(self, tx, tag='t'):
        """Generate text from a TX object and save to self.curr."""

        handle = self.text_draw(tx, tag=tag)
        self.curr[handle] = tx

    def regen_all_text(self, event=None):
        """Delete all existing text and regenerate.

        This needs to be done after zoom because text size is defined
        in terms of canvas pixels and doesn't change size with zoom."""

        tx_list = [tx for tx in self.curr.values() if tx.type == 'tx']
        attribs_list = [tx.get_attribs() for tx in tx_list]
        self.del_all_t()
        for attribs in attribs_list:
            tx = entities.TX(attribs)
            self.text_gen(tx)

    def text_enter(self, p=None):
        """Place new text on drawing."""

        rc = RUBBERCOLOR
        if not self.text:
            self.text_entry_enable = 1
            self.update_message_bar('Enter text')
        elif not self.pt_stack:
            self.update_message_bar('Pick location for center of text')
            if p:
                x, y = p
                if self.rubber:
                    self.canvas.delete(self.rubber)
                self.rubber = self.canvas.create_text(x, y, text=self.text,
                                                      fill=rc, tags='r')
        elif self.pt_stack:
            p = self.pt_stack.pop()
            attribs = (p, self.text, self.textstyle,
                       self.textsize, self.TEXTCOLOR)
            tx = entities.TX(attribs)
            self.text_gen(tx)
            self.text = None
            if self.rubber:
                self.canvas.delete(self.rubber)
            if self.op_stack:
                self.op = self.op_stack.pop()

    def text_move(self, p=None):
        """Move existing text to new point."""

        if not self.obj_stack:
            self.set_sel_mode('items')
            self.update_message_bar('Select text to move.')
        elif not self.pt_stack:
            if not self.rubber:
                for item_tuple in self.obj_stack:
                    for item in item_tuple:
                        if 't' in self.canvas.gettags(item):
                            if item in self.curr:
                                old_tx = self.curr[item]
                                old_attribs = old_tx.get_attribs()
                                self.rubber_tx = entities.TX(old_attribs)
                                self.rubber = self.text_draw(self.rubber_tx,
                                                             tag='r')
            if self.rubber:
                self.canvas.delete(self.rubber)
            if p:  # cursor coordinates supplied by mouse_move
                p = self.cp2ep(p)  # coords of p are in CCS
                self.rubber_tx.coords = p
            self.rubber = self.text_draw(self.rubber_tx, tag='r')
            self.update_message_bar('Pick new location for center of text')
            self.set_sel_mode('pnt')
        elif self.pt_stack:
            newpoint = self.pt_stack.pop()
            handle = self.obj_stack.pop()[0]
            if handle in self.curr:
                tx = self.curr[handle]
                attribs = list(tx.get_attribs())
                attribs[0] = newpoint
                attribs = tuple(attribs)
                new_tx = entities.TX(attribs)
                self.text_gen(new_tx)
                del self.curr[handle]
                self.canvas.delete(handle)
            if self.rubber:
                self.canvas.delete(self.rubber)
                self.rubber = None
                del self.rubber_tx
            self.regen_all_text()

    def txt_params(self, obj=None):
        self.op = 'txt_params'
        if not self.obj_stack and not self.modified_text_object:
            self.update_message_bar('Pick text to modify')
            self.set_sel_mode('items')
        elif self.obj_stack and not self.modified_text_object:
            msg = "Use editor to modify parameters, then click 'Change Parameters'"
            self.update_message_bar(msg)
            self.set_sel_mode('pnt')  # keep mouse_move calling func
            self.handle = self.obj_stack.pop()[0]
            self.obj_stack = []
            ent = self.curr[self.handle]
            if ent.type is 'tx':
                self.launch_txtdialog()
                self.txtdialog.putx(ent.text)
                self.txtdialog.puty(ent.color)
                self.txtdialog.putz(ent.size)
                self.txtdialog.putt(ent.style)
                self.txtdialog.coords = ent.coords
        elif self.modified_text_object:
            try:
                self.text_gen(self.modified_text_object)
                self.canvas.delete(self.handle)
                del self.curr[self.handle]
                del self.handle
            except AttributeError:
                print("Select text first, then click 'Change Parameters'")
                del self.handle
            self.modified_text_object = None
            self.regen()

    def launch_txtdialog(self):
        if not self.txtdialog:
            self.txtdialog = txtdialog.TxtDialog(self)
            self.txtdialog.grab_set()
            self.txtdialog.geometry('+1000+500')

    # =======================================================================
    # Delete
    # =======================================================================

    def del_el(self, item_tuple=None):
        '''Delete individual elements.'''

        self.set_sel_mode('items')
        self.allow_list = 1
        self.update_message_bar('Pick element(s) to delete.')
        if self.obj_stack:
            item_tuple = self.obj_stack.pop()
            for item in item_tuple:
                tags = self.canvas.gettags(item)
                if item in self.curr:
                    e = self.curr[item]
                    if e.type is 'cl':
                        self.cl_list.remove(e.coords)
                    del self.curr[item]
                    self.canvas.delete(item)
                else:
                    if 'd' in tags:
                        dgid = tags[1]
                        dim_items = self.canvas.find_withtag(dgid)
                        for each in dim_items:
                            self.canvas.delete(each)
                        del self.curr[dgid]

    def del_all_c(self):
        '''Delete All construction.'''

        delete = [k for k, v in self.curr.items() if v.type in ('cl', 'cc')]
        for k in delete:
            del self.curr[k]
        for item in self.canvas.find_withtag('c'):
            self.canvas.delete(item)
        self.cl_list = []

    def del_all_g(self):
        '''Delete all geometry.'''

        delete = [k for k, v in self.curr.items() if v.type is 'gl']
        for k in delete:
            del self.curr[k]
        delete = [k for k, v in self.curr.items() if v.type is 'gc']
        for k in delete:
            del self.curr[k]
        delete = [k for k, v in self.curr.items() if v.type is 'ga']
        for k in delete:
            del self.curr[k]
        for item in self.canvas.find_withtag('g'):
            self.canvas.delete(item)

    def del_all_d(self):
        '''Delete all dimensions.'''

        delete = [k for k, v in self.curr.items() if v.type is 'dl']
        for k in delete:
            del self.curr[k]
        for item in self.canvas.find_withtag('d'):
            self.canvas.delete(item)

    def del_all_t(self):
        '''Delete all text.'''

        delete = [k for k, v in self.curr.items() if v.type is 'tx']
        for k in delete:
            del self.curr[k]
        for item in self.canvas.find_withtag('t'):
            self.canvas.delete(item)

    def del_all(self):
        '''Delete all.'''

        self.curr.clear()
        self.canvas.delete(ALL)
        self.cl_list = []

    # =======================================================================
    # Undo / Redo
    # =======================================================================

    """
    When drawing entities are created and displayed, their parameters are
    stored in objects that are specific to their 'type'. The objects which
    encapsulate them each have a .type attribute mirroring the type of the
    entity being encapsulated. The types are as follows:

    'cl'    construction line
    'cc'    construction circle
    'gl'    geometry line
    'gc'    geometry circle
    'ga'    geometry arc
    'dl'    linear dimension
    'tx'    text

    Information about all the entities currently in the drawing is kept in a
    dictionary named self.curr, whose values are the entity objects
    encapsulating each entity and whose keys are the canvas generated handles
    associated with each entity.
    In order to implement undo and redo, it is neccesary to detect whenever
    there is a change in self.curr. To do this, a copy of self.curr (named
    self.prev) is maintained. Whenever a CAD operation ends, the save_delta()
    method is called. This method first compares self.curr with self.prev to
    see if they are equal. If not, a set containing the values in self.curr is
    compared with a set containing the values in self.prev. The difference is
    loaded onto the undo_stack. The curr config is then copied to self.prev.
                             __________
                            |  Change  |
                            |_detected_|
                                 ||
                                 ||1
                                 \/          2
     ____________            __________    diff    ______________
    | redo stack |          |   Curr   |    -->   |  Undo stack  |
    |____________|          |__________|          |______________|
                                 ||
                                 ||3
                                 \/
                             __________
                            |   Prev   |
                            |__________|

    1. difference detected between curr and prev.
    2. diff (delta) pushed onto undo_stack.
    3. copy of curr saved to prev.


    The undo & redo buttons work as shown in the diagram below.

     ____________     2      __________ 3       1  ______________
    | redo stack |   <--    |   Curr   |    <--   |  Undo stack  |
    |____________|          |__________|          |______________|
                                 ||
                                 ||4
                                 \/
                             __________
                            |   Prev   |
                            |__________|

    For example, when the Undo button is clicked:
    1. undo_data is popped off the undo_stack.
    2. undo data is pushed onto the redo_stack.
    3. curr is updated with undo_data.
    4. copy of curr is save to prev.


     ____________ 1       3  __________      2     ______________
    | redo stack |   -->    |   Curr   |    -->   |  Undo stack  |
    |____________|          |__________|          |______________|
                                 ||
                                 ||4
                                 \/
                             __________
                            |   Prev   |
                            |__________|

    Similarly, if the Redo button is clicked:
    1. redo_data is popped off the redo_stack.
    2. redo data is pushed onto the undo_stack.
    3. curr is updated with redo_data.
    4. copy of curr is saved to prev.

    Typically, after clicking undo / redo buttons one or more times,
    the user will resume running CAD operations that create, modify or
    delete CAD data. Once CAD operations are resumed, the data on the
    redo stack is no longer relevant and is discarded. Thus, when the
    save_delta method runs, the redo stack is emptied.
    """

    def save_delta(self):
        """After a drawing change, save deltas on undo stack."""

        if self.curr.values() != self.prev.values():
            plus = set(self.curr.values()) - set(self.prev.values())
            minus = set(self.prev.values()) - set(self.curr.values())
            if plus or minus:  # Only save if something changed
                delta = {'+': plus, '-': minus}
                self.undo_stack.append(delta)
                self.prev = self.curr.copy()
                self.clear_redo()

    def undo(self, event=None):
        """Pop data off undo, push onto redo, update curr, copy to prev."""

        self.end()
        if self.undo_stack:
            undo_data = self.undo_stack.pop()
            self.redo_stack.append(undo_data)
            for item in undo_data['+']:
                self.rem_draw(item)
            for item in undo_data['-']:
                self.add_draw(item)
            self.prev = self.curr.copy()
        else:
            print("No Undo steps available.")

    def redo(self, event=None):
        """Pop data off redo, push onto undo, update curr, copy to prev."""

        self.end()
        if self.redo_stack:
            redo_data = self.redo_stack.pop()
            self.undo_stack.append(redo_data)
            for item in redo_data['+']:
                self.add_draw(item)
            for item in redo_data['-']:
                self.rem_draw(item)
            self.prev = self.curr.copy()
        else:
            print("No Redo steps available.")

    def add_draw(self, entity):
        """Add entity to current drawing."""

        if entity.type is 'cl':
            self.cline_gen(entity.coords)  # This one takes coords
        elif entity.type is 'cc':
            self.ccirc_gen(entity)
        elif entity.type is 'gl':
            self.gline_gen(entity)
        elif entity.type is 'gc':
            self.gcirc_gen(entity)
        elif entity.type is 'ga':
            self.garc_gen(entity)
        elif entity.type is 'dl':
            self.dim_gen(entity)
        elif entity.type is 'tx':
            self.text_gen(entity)

    def rem_draw(self, entity):
        """Remove entity from current drawing."""

        kvlist = list(self.curr.items())
        for k, v in kvlist:
            if v == entity:
                if entity.type is 'cl':
                    self.cl_list.remove(entity.coords)
                self.canvas.delete(k)
                del self.curr[k]

    def clear_redo(self):
        self.redo_stack.clear()

    def clear_undo(self):
        self.undo_stack.clear()

    # =======================================================================
    # Program flow control
    # =======================================================================

    def execute_selected_method(self):
        self.current_item = None
        func = getattr(self, self.selected_tool_bar_function,
                       self.function_not_defined)
        func()

    def function_not_defined(self):
        pass

    def on_tool_bar_button_clicked(self, button_index):
        self.end()
        self.update_tool_bar_button_on_top_bar(button_index)
        if button_index == 0:
            self.op = ''
            self.update_message_bar(self.msg)
        else:
            self.op = self.selected_tool_bar_function
            self.dispatch(self.op)

    def update_tool_bar_button_on_top_bar(self, button_index):
        self.selected_tool_bar_function = self.tool_bar_functions[button_index]
        self.remove_options_from_top_bar()
        self.display_options_in_the_top_bar()

    def display_options_in_the_top_bar(self):
        self.show_selected_tool_icon_in_top_bar(self.selected_tool_bar_function)
        options_function_name = "{}_options".format(self.selected_tool_bar_function)
        func = getattr(self, options_function_name, self.function_not_defined)
        func()

    def remove_options_from_top_bar(self):
        for child in self.top_bar.winfo_children():
            child.destroy()

    def show_selected_tool_icon_in_top_bar(self, function_name):
        display_name = self.tool_bar_function_names[function_name] + ":"
        tk.Label(self.top_bar, text=display_name).pack(side="left")
        photo = tk.PhotoImage(
            file='icons/' + function_name + '.gif')
        label = tk.Label(self.top_bar, image=photo)
        label.image = photo
        label.pack(side="left")

    def update_message_bar(self, msg):
        self.message.configure(text=msg)

    # =======================================================================
    # User Interface methods
    # =======================================================================

    def noop(self):
        """Empty method for 'No Operation'"""
        self.update_message_bar(self.msg)

    def dispatch(self, key):
        """Dispatch commands initiated by menubar & toolbar buttons."""
        self.set_sel_mode('pnt')
        self.op = key
        if self.op:
            func = 'self.%s()' % self.op
            eval(func)
        self.entry.focus()

    def set_sel_mode(self, mode=''):
        '''Set selection mode and cursor style.
        Selection mode should be controlled by current operation
        in order to determine what is returned from screen picks.'''
        cursordict = {'':       'top_left_arrow',
                      'pnt':    'crosshair',
                      'items':  'right_ptr',
                      'list':   'right_ptr'}
        if mode in cursordict.keys():
            self.sel_mode = mode
            self.canvas.config(cursor=cursordict[mode])

    def end(self):
        '''End current operation'''

        if self.rubber:
            self.canvas.delete(self.rubber)
            self.rubber = None
        if self.rtext:
            self.canvas.delete(self.rtext)
            self.rtext = None
        if self.catch_pnt:
            self.canvas.delete(self.catch_pnt)
            self.catch_pnt = None
        if self.op:
            self.op = ''
        self.sel_box_crnr = None
        self.canvas.delete(self.sel_boxID)
        self.sel_boxID = None
        self.text = ''
        self.pt_stack = []
        self.float_stack = []
        self.obj_stack = []
        self.text_entry_enable = 0
        self.set_sel_mode('')
        self.allow_list = 0
        self.quit_popup()
        self.save_delta()
        self.update_message_bar('CTRL-LMB to pan.  CTRL-RMB to zoom.')
        # print("running 'end()'")
        # print("Selected function: {}".format(self.selected_tool_bar_function))

    def enterfloat(self, str_value):
        """Receive string value (from calculator) and do the right thing."""

        if str_value:
            val = float(str_value)
            self.float_stack.append(val)
            func = 'self.%s()' % self.op
            eval(func)

    def keyboard_entry(self, event):
        """Store user entered values on stack.

        POINTS:
        points are stored in mm units in ECS on self.pt_stack.
        This is one of the places where unit scale is applied.

        FLOATS:
        floats are stored as unitless numbers on self.float_stack.
        Because a float value may be used for anything: radius, angle,
        x value, y value, whatever; it is not possible to know here
        how a float value will be used. It remains the responsibility
        of the using function to condition the float value
        appropriately by applying unitscale for distances, etc."""

        if self.op:
            text = self.entry.get()
            self.entry.delete(0, len(text))
            if self.text_entry_enable:
                self.text = text
            else:
                tlist = text.split(',')
                if len(tlist) == 1:
                    val = tlist[0]
                    self.float_stack.append(float(val))
                elif len(tlist) == 2 and self.sel_mode == 'pnt':
                    # user entered points are already in ECS units
                    x, y = tlist
                    x = float(x) * self.unitscale
                    y = float(y) * self.unitscale
                    self.pt_stack.append((x, y))
            func = 'self.%s()' % self.op
            eval(func)

    def lft_click(self, event):
        '''Place screen picks on stack(s), call method named by self.op.

        In "point" mode, put x,y coords of "catch point", if any, on point
        stack, otherwise put pointer x,y coords on stack.
        In "items" mode, put a tuple of selected items on "object stack".
        If first click does not find one or more items within its
        "catch radius", enter "box select mode" and look for objects that
        lie completely inside box defined by 1st and 2nd clicks.
        '''

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        cr = self.catch_radius
        if self.sel_mode == 'pnt':
            # convert screen coords to ECS units and put on pt_stack
            if self.catch_pnt:
                l, t, r, b = self.canvas.coords(self.catch_pnt)
                x = (r + l)/2
                y = (t + b)/2
            p = self.cp2ep((x, y))
            self.pt_stack.append(p)
        elif self.sel_mode in ('items', 'list'):
            items = self.canvas.find_overlapping(x-cr, y-cr, x+cr, y+cr)
            if not items and not self.sel_box_crnr:
                self.sel_box_crnr = (x, y)
                return
            if self.sel_box_crnr:
                x1, y1 = self.sel_box_crnr
                items = self.canvas.find_enclosed(x1, y1, x, y)
                self.sel_box_crnr = None
                self.canvas.delete(self.sel_boxID)
                self.sel_boxID = None
            if self.sel_mode == 'items':
                self.obj_stack.append(items)
            elif self.sel_mode == 'list':
                if not self.obj_stack:
                    self.obj_stack.append([])
                for item in items:
                    if item not in self.obj_stack[-1]:
                        self.obj_stack[-1].append(item)

    def mid_click(self, event):
        #self.end()
        self.on_tool_bar_button_clicked(0)

    def rgt_click(self, event):
        '''Popup menu for view options.'''

        if self.popup:
            self.popup.destroy()
        self.popup = tk.Toplevel()
        self.popup.overrideredirect(1)
        frame = tk.Frame(self.popup)
        tk.Button(frame, text='View Fit',
                  command=lambda: (self.view_fit(), self.quit_popup())).pack()
        if self.allow_list:
            tk.Button(frame, text='Start list',
                      command=lambda: (self.set_sel_mode('list'),
                                       self.quit_popup())).pack()
            tk.Button(frame, text='End list',
                      command=lambda: (self.set_sel_mode('items'),
                                       eval('self.%s()' % self.op),
                                       self.quit_popup())).pack()
        frame.pack()
        # size, x, y = tk.winfo_toplevel().winfo_geometry().split('+')
        x = 100
        y = 100
        if self.allow_list:
            self.popup.geometry('60x90+%s+%s' % (x+event.x, y+event.y+30))
        else:
            self.popup.geometry('60x30+%s+%s' % (x+event.x, y+event.y+30))

    def quit_popup(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None

    def gen_catch_pnt(self, x, y, color='yellow', regen=0):
        '''Generate (or regenerate) a catch point at coordinates x, y.'''

        ps = self.catch_pnt_size
        if regen:
            self.canvas.coords(self.catch_pnt, x-ps, y-ps, x+ps, y+ps)
        else:
            self.catch_pnt = self.canvas.create_rectangle(x-ps, y-ps,
                                                          x+ps, y+ps,
                                                          outline=color)

    def set_cntr_catch(self, event):
        '''Set center catch flag'''

        if event.type == '2' and event.keysym == 'Shift_L':
            self.catchCntr = True
        else:
            self.catchCntr = False

    def mouse_move(self, event):
        '''Display a catch point (ID=self.catch_pnt) on a line within
        self.catch_radius of the cursor. Catch point should be "sticky"
        at midpoints, ends and intersections.'''

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.sel_mode == 'pnt':
            cr = self.catch_radius
            found = self.canvas.find_overlapping(x-cr, y-cr, x+cr, y+cr)
            items = []
            for each in found:
                if self.canvas.type(each) in ('line', 'oval', 'arc') and\
                   'r' not in self.canvas.gettags(each):
                    items.append(each)
            cp = self.find_catch_pt(items, x, y)
            if cp:
                x, y = cp
                if self.catch_pnt:
                    self.gen_catch_pnt(x, y, regen=1)
                else:
                    self.gen_catch_pnt(x, y)
            else:
                if self.catch_pnt:
                    self.canvas.delete(self.catch_pnt)
                    self.catch_pnt = 0
            p1 = (x, y)  # func wants canvas coords to make rubber element
            if self.op:
                func = 'self.%s(%s)' % (self.op, p1)
                eval(func)
        elif self.sel_box_crnr:
            x1, y1 = self.sel_box_crnr
            if self.sel_boxID:
                self.canvas.coords(self.sel_boxID, x1, y1, x, y)
            else:
                self.sel_boxID = self.canvas.create_rectangle(x1, y1, x, y,
                                                              outline='cyan',
                                                              tags='sb')
        elif self.sel_mode == 'items':
            func = 'self.%s()' % self.op
            eval(func)

    def find_catch_pt(self, items, x, y):
        cr = self.catch_radius
        if len(items) == 1:
            item = items[0]
            if self.canvas.type(item) == 'arc':
                x0, y0, x1, y1 = self.canvas.coords(item)
                xc = (x0+x1)/2
                yc = (y0+y1)/2
                r = (x1-x0)/2
                a0 = float(self.canvas.itemcget(item, 'start'))
                a1 = a0 + float(self.canvas.itemcget(item, 'extent'))
                a0 = -a0*math.pi/180
                a1 = -a1*math.pi/180
                p0 = (xc+r*math.cos(a0), yc+r*math.sin(a0))
                p1 = (xc+r*math.cos(a1), yc+r*math.sin(a1))
                arc_end_pts = (p0, p1)
                if self.catchCntr:
                    return (xc, yc)
                caught = None
                for pt in arc_end_pts:
                    if gh.pnt_in_box_p((pt[0], pt[1]),
                                    (x-cr, y-cr, x+cr, y+cr)):
                        caught = pt
                if caught:
                    return caught
                ip = gh.line_circ_inters(xc, yc, x, y, xc, yc, r)
                for pt in ip:
                    if gh.p2p_dist(pt, (x, y)) < cr:
                        return pt
            elif self.canvas.type(item) == 'oval':
                x0, y0, x1, y1 = self.canvas.coords(item)
                xc, yc = ctr = gh.midpoint((x0, y0), (x1, y1))
                r = (x1-x0)/2
                if self.catchCntr:
                    return (xc, yc)
                inters_pts = gh.line_circ_inters(xc, yc, x, y, xc, yc, r)
                for pt in inters_pts:
                    if gh.p2p_dist(pt, (x, y)) < cr:
                        return (pt[0], pt[1])
            elif self.canvas.type(item) == 'line':
                x0, y0, x1, y1 = self.canvas.coords(item)  # end pnts
                xm, ym = gh.midpoint((x0, y0), (x1, y1))   # mid point
                pts = ((x0, y0), (x1, y1), (xm, ym))
                caught = None
                for pt in pts:
                    if 'g' in self.canvas.gettags(item) and \
                       gh.pnt_in_box_p((pt[0], pt[1]),
                                    (x-cr, y-cr, x+cr, y+cr)):
                        caught = pt
                if caught:
                    return caught
                line = gh.cnvrt_2pts_to_coef((x0, y0), (x1, y1))
                u, v = gh.proj_pt_on_line(line, (x, y))
                if x0 < u < x1 or x0 > u > x1 or y0 < v < y1 or y0 > v > y1:
                    return (u, v)

        if len(items) > 1:  # intersection found
            if self.canvas.type(items[0]) == 'line' and\
               self.canvas.type(items[1]) == 'line':
                a, b, c, d = self.canvas.coords(items[0])
                e, f, g, h = self.canvas.coords(items[1])
                line1 = gh.cnvrt_2pts_to_coef((a, b), (c, d))
                line2 = gh.cnvrt_2pts_to_coef((e, f), (g, h))
                if line1 == line2:  # colinear; toss one and try again
                    items.pop()
                    return self.find_catch_pt(items, x, y)
                ip = gh.intersection(line1, line2)
                if not ip:
                    items.pop(0)
                    return self.find_catch_pt(items, x, y)
                return ip
            elif self.canvas.type(items[0]) in ('oval', 'arc') and\
                 self.canvas.type(items[1]) in ('oval', 'arc'):
                a, b, c, d = self.canvas.coords(items[0])
                x1, y1 = gh.midpoint((a, b), (c, d))
                r1 = (c-a)/2
                e, f, g, h = self.canvas.coords(items[1])
                x2, y2 = gh.midpoint((e, f), (g, h))
                r2 = (g-e)/2
                ip = gh.circ_circ_inters(x1, y1, r1, x2, y2, r2)
                if ip:
                    for pt in ip:
                        if gh.p2p_dist(pt, (x, y)) < cr:
                            return pt
            elif self.canvas.type(items[0]) in ('oval', 'arc') and\
                 self.canvas.type(items[1]) == 'line':
                items[0], items[1] = items[1], items[0]
            if self.canvas.type(items[0]) == 'line' and\
               self.canvas.type(items[1]) in ('oval', 'arc'):
                x1, y1, x2, y2 = self.canvas.coords(items[0])
                line = gh.cnvrt_2pts_to_coef((x1, y1), (x2, y2))
                e, f, g, h = self.canvas.coords(items[1])
                xc, yc = cntr = gh.midpoint((e, f), (g, h))
                r = (g-e)/2
                ip = gh.line_circ_inters(x1, y1, x2, y2, xc, yc, r)
                for pt in ip:
                    if gh.p2p_dist(pt, (x, y)) < cr:
                        return pt

    def bindings(self):
        self.canvas.panbindings()
        self.canvas.zoombindings()
        self.canvas.bind("<Motion>", self.mouse_move)
        self.canvas.bind("<Button-1>", self.lft_click)
        self.canvas.bind("<Button-2>", self.mid_click)
        self.canvas.bind("<Button-3>", self.rgt_click)
        self.bind("<Key>", self.set_cntr_catch)
        self.bind("<KeyRelease>", self.set_cntr_catch)
        self.bind("<Control-B1-ButtonRelease>", self.regen_all_cl)
        self.bind("<Control-B3-ButtonRelease>", self.regen)
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)

    # =======================================================================
    # GUI
    # =======================================================================

    def __init__(self):
        super().__init__()
        self.create_gui()
        self.title("PYurCAD")

    def create_gui(self):
        self.create_menu()
        self.create_bar_frame()
        self.create_tool_bar()
        self.create_tool_bar_buttons()
        self.create_drawing_canvas()
        self.bind_menu_accelrator_keys()
        self.show_selected_tool_icon_in_top_bar("noop")

    def create_menu(self):
        self.menubar = tk.Menu(self)
        self.filemenu = tk.Menu(self.menubar, tearoff=1)
        self.filemenu.add_command(label="Print", command=self.printps)
        self.filemenu.add_command(label="Open", command=self.fileOpen)
        self.filemenu.add_command(label="Save", command=self.fileSave)
        self.filemenu.add_command(label="Save as", command=self.fileSaveas)
        self.filemenu.add_command(label="Import DXF", command=self.fileImport)
        self.filemenu.add_command(label="Export DXF", command=self.fileExport)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_close_menu_clicked)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.editmenu = tk.Menu(self.menubar, tearoff=1)
        self.editmenu.add_command(label="Undo Ctrl+Z", command=self.undo)
        self.editmenu.add_command(label="Redo Ctrl+Y", command=self.redo)
        self.menubar.add_cascade(label="Edit", menu=self.editmenu)

        self.viewmenu = tk.Menu(self.menubar, tearoff=1)
        self.viewmenu.add_command(label="Fit", command=self.view_fit)
        self.menubar.add_cascade(label="View", menu=self.viewmenu)

        self.unitmenu = tk.Menu(self.menubar, tearoff=1)
        self.unitmenu.add_command(label="mm", command=lambda k="mm": self.set_units(k))
        self.unitmenu.add_command(label="inches",
                                  command=lambda k="inches": self.set_units(k))
        self.unitmenu.add_command(label="feet",
                                  command=lambda k="feet": self.set_units(k))
        self.menubar.add_cascade(label="Units", menu=self.unitmenu)

        self.measmenu = tk.Menu(self.menubar, tearoff=1)
        self.measmenu.add_command(label="Pt-Pt distance", command=self.meas_dist)
        self.measmenu.add_command(label="Item Coords",
                                  command=lambda k="itemcoords": self.dispatch(k))
        self.measmenu.add_command(label="Item Length",
                                  command=lambda k="itemlength": self.dispatch(k))
        self.measmenu.add_command(label="Calculator", command=self.launch_calc)
        self.menubar.add_cascade(label="Measure", menu=self.measmenu)

        self.dimmenu = tk.Menu(self.menubar, tearoff=1)
        self.dimmenu.add_command(label="Dim Horizontal",
                                 command=lambda k="dim_h": self.dispatch(k))
        self.dimmenu.add_command(label="Dim Vertical",
                                 command=lambda k="dim_v": self.dispatch(k))
        self.dimmenu.add_command(label="Dim Parallel",
                                 command=lambda k="dim_par": self.dispatch(k))
        self.menubar.add_cascade(label="Dimensions", menu=self.dimmenu)

        self.textmenu = tk.Menu(self.menubar, tearoff=1)
        self.textmenu.add_command(label="Create Text",
                                  command=lambda k="text_enter": self.dispatch(k))
        self.textmenu.add_command(label="Move Text",
                                  command=lambda k="text_move": self.dispatch(k))
        self.textmenu.add_command(label="Edit Text",
                                  command=self.txt_params)
        self.menubar.add_cascade(label="Text", menu=self.textmenu)

        self.delmenu = tk.Menu(self.menubar, tearoff=1)
        self.delmenu.add_command(label="Delete Element",
                                 command=lambda k="del_el": self.dispatch(k))
        self.delmenu.add_command(label="Delete All Constr", command=self.del_all_c)
        self.delmenu.add_command(label="Delete All Geometry", command=self.del_all_g)
        self.delmenu.add_command(label="Delete All Dimensions", command=self.del_all_d)
        self.delmenu.add_command(label="Delete All Text", command=self.del_all_t)
        self.delmenu.add_separator()
        self.delmenu.add_command(label="Delete All 2D", command=self.del_all)
        self.menubar.add_cascade(label="Delete", menu=self.delmenu)

        self.debugmenu = tk.Menu(self.menubar, tearoff=1)
        self.debugmenu.add_command(label="show Zoom Scale",
                                   command=lambda k="show_zoomscale": self.dispatch(k))
        self.debugmenu.add_command(label="show self.calculator",
                                   command=lambda k="show_calc": self.dispatch(k))
        self.debugmenu.add_command(label="show dir(self)",
                                   command=lambda k="show_dir_self": self.dispatch(k))
        self.debugmenu.add_command(label="draw Workplane",
                                   command=self.draw_workplane)
        self.debugmenu.add_command(label="Launch Cube",
                                   command=self.launch_cube)
        self.menubar.add_cascade(label="Debug", menu=self.debugmenu)

        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="About", command=self.on_about_menu_clicked)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        self.config(menu=self.menubar)

    def create_bar_frame(self):
        self.bar_frame = tk.Frame(self, height=15, relief="raised")
        self.create_status_bar()
        self.create_top_bar()
        self.bar_frame.pack(fill="x", side="top")

    def create_tool_bar(self):
        self.tool_bar = tk.Frame(self, relief="raised", width=50)
        self.tool_bar.pack(fill="y", side="left", pady=3)

    def create_tool_bar_buttons(self):
        for index, name in enumerate(self.tool_bar_functions):
            icon = tk.PhotoImage(file='icons/' + name + '.gif')
            self.button = tk.Button(
                self.tool_bar, image=icon,
                command=lambda index=index: self.on_tool_bar_button_clicked(index))
            self.button.grid(
                row=index // 3, column=1 + index % 3, sticky='nsew')
            self.button.image = icon

    def create_status_bar(self):
        self.status_bar = tk.Frame(self.bar_frame)
        self.create_units_display()
        self.create_entry_widget()
        self.create_message_widget()
        self.status_bar.pack(side="right")

    def create_top_bar(self):
        self.top_bar = tk.Frame(self.bar_frame)
        self.top_bar.pack(side="left", pady=2)

    def create_units_display(self):
        self.unitsDisplay = tk.Label(self.status_bar, text='Units: mm')
        self.unitsDisplay.pack(side="right", padx=5)

    def create_entry_widget(self):
        self.entry = tk.Entry(self.status_bar, width=15)
        self.entry.pack(side="right", padx=10)
        self.entry.bind("<KeyPress-Return>", self.keyboard_entry)
        self.entry.bind("<KeyPress-KP_Enter>", self.keyboard_entry)

    def create_message_widget(self):
        self.message = tk.Label(self.status_bar, text=self.msg)
        self.message.pack(side="right")

    def create_drawing_canvas(self):
        self.canvas_frame = tk.Frame(self, width=1200, height=900)
        self.canvas_frame.pack(side="right", expand="yes", fill="both")
        self.canvas = Zooming(self.canvas_frame, background="black",
                              width=800, height=500)
        self.canvas.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.BOTH)
        self.bindings()  # original cadvas bindings
        self.canvas.move_can(60, 420)  # Put 0,0 near lower left corner

    def bind_menu_accelrator_keys(self):
        self.bind('<KeyPress-F1>', self.on_about_menu_clicked)

    def build_menu(self, menu_definitions):
        menu_bar = tk.Menu(self)
        for definition in menu_definitions:
            menu = tk.Menu(menu_bar, tearoff=0)
            top_level_menu, pull_down_menus = definition.split('-')
            menu_items = map(str.strip, pull_down_menus.split(','))
            for item in menu_items:
                self._add_menu_command(menu, item)
            menu_bar.add_cascade(label=top_level_menu, menu=menu)
        self.config(menu=menu_bar)

    def _add_menu_command(self, menu, item):
        if item == 'sep':
            menu.add_separator()
        else:
            menu_label, accelrator_key, command_callback = item.split('/')
            try:
                underline = menu_label.index('&')
                menu_label = menu_label.replace('&', '', 1)
            except ValueError:
                underline = None
            menu.add_command(label=menu_label, underline=underline,
                             accelerator=accelrator_key, command=eval(command_callback))

    # =======================================================================
    # Rotating Cube
    # =======================================================================

    def transpose_matrix(self, matrix):
        return list(zip(*matrix))

    def translate_vector(self, x, y, dx, dy):
        return x + dx, y + dy

    def matrix_multiply(self, matrix_a, matrix_b):
        zip_b = list(zip(*matrix_b))
        return [[
            sum(ele_a * ele_b for ele_a, ele_b in zip(row_a, col_b))
            for col_b in zip_b
            ] for row_a in matrix_a]

    def rotate_along_x(self, x, shape):
        return self.matrix_multiply(
            [[1, 0, 0], [0, math.cos(x), -math.sin(x)],
             [0, math.sin(x), math.cos(x)]], shape)

    def rotate_along_y(self, y, shape):
        return self.matrix_multiply(
            [[math.cos(y), 0, math.sin(y)], [0, 1, 0],
             [-math.sin(y), 0, math.cos(y)]], shape)

    def rotate_along_z(self, z, shape):
        return self.matrix_multiply(
            [[math.cos(z), math.sin(z), 0],
             [-math.sin(z), math.cos(z), 0], [0, 0, 1]], shape)

    last_x = 0
    last_y = 0

    def launch_cube(self):
        self.init_data()
        self.draw_cube()
        self.bind_mouse_buttons()
        #self.continually_rotate()
        self.epsilon = lambda d: d * 0.01

    def init_data(self):
        self.cube = self.transpose_matrix(
            [[-100, -100, -100], [-100, 100, -100], [-100, -100, 100 ],
             [-100, 100, 100],  [100, -100, -100], [100, 100, -100],
             [100, -100, 100], [100, 100, 100]])

    def bind_mouse_buttons(self):
        self.canvas.bind("<Button-2>", self.on_mouse_clicked)
        self.canvas.bind("<B2-Motion>", self.on_mouse_motion)

    def draw_cube(self):
        cube_points = [
            [0, 1, 2, 4], [3, 1, 2, 7], [5, 1, 4, 7], [6, 2, 4, 7]]
        w = self.canvas.winfo_width() / 2
        h = self.canvas.winfo_height() / 2
        self.canvas.delete(tk.ALL)
        for i in cube_points:
            for j in i:
                self.canvas.create_line(
                    self.translate_vector(
                        self.cube[0][i[0]], self.cube[1][i[0]], w, h),
                    self.translate_vector(
                        self.cube[0][j], self.cube[1][j], w, h),
                    fill=GEOMCOLOR)

    def on_mouse_clicked(self, event):
        self.last_x = event.x
        self.last_y = event.y

    def on_mouse_motion(self, event):
        dx = self.last_y - event.y
        self.cube = self.rotate_along_x(self.epsilon(-dx), self.cube)
        dy = self.last_x - event.x
        self.cube = self.rotate_along_y(self.epsilon(dy), self.cube)
        self.draw_cube()
        self.on_mouse_clicked(event)


if __name__ == '__main__':

    app = PyurCad()
    app.mainloop()
