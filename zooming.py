from tkinter import *
from math import log, exp

import operator

__doc__="""
todo:

scale constraints don't work yet

certain scale constraints should affect position, maybe vice versa

"""

class Pair:
    """ordered pair of numbers. element-wise add/mult/etc. access the numbers by index or .x .y"""
    def __init__(self,a,b):
        self.a=a
        self.b=b
    def __add__(self,other): return Pair(self[0]+other[0],self[1]+other[1])
    def __sub__(self,other): return Pair(self[0]-other[0],self[1]-other[1])
    def __mul__(self,other): return Pair(self[0]*other[0],self[1]*other[1])
    def __truediv__(self,other): return Pair(self[0]/other[0],self[1]/other[1])
    def __iadd__(self,other):
        self[0]+=other[0]
        self[1]+=other[1]
        return self
    def __isub__(self,other):
        self[0]-=other[0]
        self[1]-=other[1]
        return self
    def __imul__(self,other):
        self[0]*=other[0]
        self[1]*=other[1]
        return self
    def __itruediv__(self,other):
        self[0]/=other[0]
        self[1]/=other[1]
        return self
    
    def __neg__(self):
        r= Pair(-self[0],-self[1])
        return r
    def __getattr__(self,attr):
        if attr in ('x','a'): return self[0]
        if attr in ('y','b'): return self[1]
        # raise NotImplementedError(attr)
        # had to comment this out in order to work with Python 2.4.3
    def __coerce__(self,other):
        return None
    def __str__(self):
        return "(%s,%s)"%(self.a,self.b)
    def __repr__(self):
        return "Pair%s" % str(self)
    def __iter__(self):
        return iter((self[0],self[1]))
    def __getitem__(self,i):
        if i==0: return self.a
        if i==1: return self.b
        raise IndexError
    def __setitem__(self,i,val):
        if i==0: self.a=val
        if i==1: self.b=val
        if i<0 or i>1:
            raise IndexError

class Constraint:
    def __init__(self,varname,op,value):
        """
        for example:
         leftedge>0 (world coords)
         scl.x==scl.y
        """
        if varname not in 'left top right bottom sclx scly'.split():
            raise ValueError("varname '%s' is unknown" % varname)
        if op not in ('<','>','<=','>=','=='):
            raise ValueError("op '%s' is unknown" % op)
        try:
            value=float(value) # make sure possible floats are actually float type
        except ValueError:
            pass
        if not isinstance(value,float) and value not in ('sclx','scly'):
            raise ValueError("value '%s' is unknown" % value)

        self.var=varname
        self.op=op
        self.value=value

    def __str__(self):
        return "<Constraint %s %s %s>" % (self.var,self.op,self.value)

    def calc(self,v,edge,transformed):
        """
        calc receives requested value 'v' and returns a new
        value. returning v itself means that the
        constraint had no effect-- the requested value will not
        violate the constraint.

        this function might decide to adjust v to
        meet the constraint though.  the available data is a
        transformed edge coodrinate and the actual edge
        coordinate. the coordinate system is unspecified, but all
        values will be in the same coord system.
        """

        if ((self.op==">" and transformed>edge) or
            (self.op=="<" and transformed<edge) or
            (self.op=="==" and transformed!=edge)):
            #print "%s correcting by %s, ev=%s, tv=%s"  % (self,transformed-edge,edge,transformed)
            v=v-(transformed-edge)
        return v

class Zooming(Canvas):
    """canvas that supports zoom and pan. in this object, the 'world'
    coordinates are the unchanging ones. you convert to/from 'canvas'
    coordinates, which are the ones suitable for all canvas
    operations.

    maybe sometime i'll wrap all the canvas ops so you can work
    exclusively in world coords."""
    
    def __init__(self,*k,**kw):
        Canvas.__init__(self,*k,**kw)

        # our transformation is stored in off/scl
        # world points get offset by off, then
        # scaled by scl. so the offsets stay in world units.
        self.off=Pair(0,0)
        self.scl=Pair(1,1)

        self.constraints=[] # list of Constraint objs

    def addconstraint(self,*args):
        self.constraints.append(Constraint(*args))
        # some identity transformations will give the new constraint a
        # chance to push the transformation around:
        if self.winfo_ismapped(): # only if the winfo sizes are correct
            self.move(0,0)
            self.scale(0,0,1,1)
    def delconstraint(self,varname,op):
        keep=[]
        for c in self.constraints:
            if not (c.var==varname and c.op==op):
                keep.append(c)
        self.constraints=keep
                
    def move(self,dx,dy):
        """canvas move command, but always moves everything and
        updates the transformation.  dx,dy are world coordinates."""

        for c in self.constraints:
            if c.var=="left":
                dx = self.c2w_dx(c.calc(v=self.w2c_dx(dx),
                                        edge=0,
                                        transformed=self.world2canvas(c.value+dx,0)[0]))
            if c.var=="right":
                dx = self.c2w_dx(c.calc(v=self.w2c_dx(dx),
                                        edge=self.winfo_width(),
                                        transformed=self.world2canvas(c.value+dx,0)[0]))
            if c.var=="top":
                dy = self.c2w_dy(c.calc(v=self.w2c_dy(dy),
                                        edge=0,
                                        transformed=self.world2canvas(0,c.value+dy)[1]))
            if c.var=="bottom":
                dy = self.c2w_dy(c.calc(v=self.w2c_dy(dy),
                                        edge=self.winfo_height(),
                                        transformed=self.world2canvas(0,c.value+dy)[1]))
                
        cdx,cdy=self.world2canvas_vector(dx,dy)
        Canvas.move(self,"all",cdx,cdy)
        self.off+=(dx,dy)

    def move_can(self,dx,dy):
        """like move, but you give canvas units (pixels) instead of world units"""
        return self.move(*(Pair(dx,dy)/self.scl))

    def scale(self,xOrigin,yOrigin,xScale,yScale):
        """canvas scale command, but also updates the transformation. all objects are scaled.
        origin is in canvas coordinates (use world2canvas to convert from world coords if necessary)."""
        if xScale==0 or yScale==0:
            print("Zooming.scale received scale factor of 0 - ignoring")
            return

        for c in self.constraints:
            if c.var=="sclx":
                xScale = -c.calc(-xScale, edge=xScale, transformed=c.value/self.scl.x)
            if c.var=="scly":
                yScale = -c.calc(-yScale, edge=yScale, transformed=c.value/self.scl.y)
        
        factor = Pair(xScale,yScale)

        # to acheive the desired effect of the xOrigin,yOrigin canvas
        # point holding stationary during the scale, we remember the
        # world coords of that 'scale center' before the scaling
        worldorigin_prescale=Pair(*self.canvas2world(xOrigin,yOrigin))
        # ..apply the scaling
        self.scl*=factor
        # ..and see where the scale center moved (in world coords)
        worldorigin_postscale=Pair(*self.canvas2world(xOrigin,yOrigin))

        # now, we simply correct the offset so the scale center does not move
        self.off+=(worldorigin_postscale-worldorigin_prescale)
        Canvas.scale(self,"all",xOrigin,yOrigin,xScale,yScale)

        # a null move will let the offset constraints take effect
        self.move(0,0)

    def setscale(self,xOrigin,yOrigin,xScale,yScale):
        """sets scale factor absolutely, rather than multiplying to the existing scale factor"""
        self.scale(xOrigin,yOrigin,xScale/self.scl.x,yScale/self.scl.y)
        
    def world2canvas(self,*worldcoord):
        """takes a world coordinate as a tuple and returns the canvas coordinate"""
        r=(Pair(*worldcoord)+self.off)*self.scl
        return tuple(r)
        
    def canvas2world(self,*canvascoord):
        """takes a canvas coordinate as a tuple and returns the world coordinate"""
        r=(Pair(*canvascoord)/self.scl)-self.off
        return tuple(r)

    def canvas2world_vector(self,*v):
        """converts a canvas vector to world vector"""
        return Pair(*v)/self.scl
    def world2canvas_vector(self,*v):
        """converts a world vector to canvas vector"""
        return Pair(*v)*self.scl
    # convenience (?) - *for vectors only*
    def c2w_dx(self,dx): return self.canvas2world_vector(dx,0)[0]
    def w2c_dx(self,dx): return self.world2canvas_vector(dx,0)[0]
    def c2w_dy(self,dy): return self.canvas2world_vector(0,dy)[1]
    def w2c_dy(self,dy): return self.world2canvas_vector(0,dy)[1]

    def panbindings(self):
        """Ctrl-LMB used to pan the canvas like me10"""
        def press(self,ev):
            self.lastmouse=Pair(ev.x,ev.y)
        def motion(self,ev):
            self.move_can(ev.x-self.lastmouse.x,ev.y-self.lastmouse.y)
            self.lastmouse=Pair(ev.x,ev.y)
        def release(self,ev):
            pass
        self.bind("<Control-ButtonPress-1>",lambda ev: press(self,ev))
        self.bind("<Control-B1-Motion>",lambda ev: motion(self,ev))
        # Use the ctrl-B1-rel event in the app to trigger cline regen
        #self.bind("<Control-B1-ButtonRelease>",lambda ev: release(self,ev))
        
    def zoombindings(self):
        """Ctrl-RMB to zoom the canvas like me10"""
        
        def press(self,ev):
            self.firstmouse=Pair(ev.x,ev.y)
            self.prevmouse=Pair(ev.x,ev.y)
        def motion(self,ev):
            self.scale(self.firstmouse.x,self.firstmouse.y,
                       1+.02*(ev.y-self.prevmouse.y),
                       1+.02*(ev.y-self.prevmouse.y))
            self.prevmouse=Pair(ev.x,ev.y)
        def release(self,ev):
            pass
        self.bind("<Control-ButtonPress-3>",lambda ev: press(self,ev))
        self.bind("<Control-B3-Motion>",lambda ev: motion(self,ev))
        # Use the ctrl-B3-rel event in the app to trigger cline regen
        #self.bind("<Control-B3-ButtonRelease>",lambda ev: release(self,ev))

class outline_marker:
    pass

if __name__=='__main__':

    from math import sin,cos

    root=Tk()
    z=Zooming(root,width=400,height=400)
    z.pack(fill=BOTH,expand=1)
    
    z.panbindings()
    z.zoombindings()

    apply(z.create_rectangle,(z.world2canvas(5,5)+z.world2canvas(395,395)),{'tags':'demo'})
    z.scale(60,60,.5,.5)
    apply(z.create_rectangle,(z.world2canvas(5,5)+z.world2canvas(15,15)),{'tags':'demo'})
    z.scale(60,60,2,2)
    apply(z.create_rectangle,(z.world2canvas(15,15)+z.world2canvas(25,25)),{'tags':'demo'})
    z.itemconfigure("demo",width=2)

    # this draws a grid, with a crazy scalings
    # between each new set of lines
    unscale=Pair(1,1)
    for x in [i*15 for i in range(1,27)]:
        z.scale(x*10,x*10,2,2)
        apply(z.create_line,(z.world2canvas(x,0)+z.world2canvas(x,400)),{'tags':'grid'})
        apply(z.create_line,(z.world2canvas(0,x)+z.world2canvas(400,x)),{'tags':'grid'})
        z.scale(x*10,x*10,.5,.5)
        sca=Pair(sin(x+.1),cos(x+.1))
        z.scale(50,50,sca[0],sca[1])
        unscale/=sca
    z.scale(50,50,unscale[0],unscale[1])
    z.itemconfigure("grid",width=1)
        
    apply(z.create_rectangle,(z.world2canvas(153,153)+z.world2canvas(395,395)))

#    z.addconstraint("right","<",400)
#    z.addconstraint("left",">",0)
#    z.addconstraint("left","==",50)
#    z.addconstraint("top",">",0)
#    z.addconstraint("bottom","<",500)
    z.addconstraint("sclx","==",1)

    root.mainloop()
