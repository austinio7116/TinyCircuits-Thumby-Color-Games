# Delunky - Endless Descent
# Original PICO-8 game by Johan Peitz (@johanpeitz) - DemakeJam 2018
# A demake of Spelunky by Derek Yu (@mossmouth)
# https://www.lexaloffle.com/bbs/?tid=31862
# License: see original cart
#
# Thumby Color port - translated from PICO-8 Lua via p8lib compatibility layer

from os import chdir
try:
  chdir("/Games/Delunky")
except:
  pass # already in correct directory (emulator)
from p8lib import *
import gc

# Button mapping: PICO-8 0=Left,1=Right,2=Up,3=Down,4=O/Z,5=X
# On Thumby Color: A=action(Z), B=secondary(X), dpad=dpad

# Utility functions from Delunky Lua
def chance(a):
  return rnd(1)<a

def add_params(src,dst):
  for k in src:
    dst[k]=src[k]

def sgn(x):
  if x>0: return 1
  if x<0: return -1
  return 0

class pico8():

  def _init(self):
    self.swap_state(self.title_state)

  # --------------------------------
  # play state
  # --------------------------------

  # entity modes
  # 0 idle/ground/inair
  # 1 ladder
  # 2 ledge
  # 3 fainted
  # 4 dead

  def init_play(self):
    self.shake(0,0)
    self.make_player(0,0)
    self.level=1
    self.start_next_level(self.level)

  def start_next_level(self,level):
    self.max_jumps=1
    self.jumps_left=1
    self.ok_to_jump=False
    self.particles=[]
    self.items=[]
    self.new_items=[]
    self.entities=[]
    gc.collect()

    # ratios
    snake_ratio=    0.1+level*0.05
    bat_ratio=      0.1+level*0.1
    spider_ratio=       level*0.1
    spike_ratio=    0.3+level*0.2
    trap_ratio=     0.1+level*0.15
    treasure_ratio= 0.1+level*0.01
    help_count=       2

    # make map
    m=self.make_map()

    # build dungeon
    cls()
    num_rooms=[12,12,12,8]
    for y in range(0,4):
      for x in range(0,4):
        room_type=m[x+1][y+1]
        # copy room to screen
        ry=room_type
        rx=flr(rnd(num_rooms[ry] if ry<len(num_rooms) else 1))
        if ry==0 and rx==11: num_rooms[0]=11 # only one idol room
        if room_type==5: # dbl drop
          rx=9+flr(rnd(3))
          ry=2
        if room_type==6: # exit
          rx=9+flr(rnd(3))
          ry=3
        if x+1!=m[5] or y+1!=m[6]:
          pal(7,0)
        sspr(0+rx*10,96+ry*8,10,8,x*10,y*8,10,8,chance(0.3))
        pal()

    # Flush the back buffer to front so pget() can read the room templates
    engine_draw.update()

    # populate tilemap
    for x in range(0,42):
      for y in range(0,34):
        # clear current data
        mset(x+1,y+1,0)

        # set new data
        c,_=pget(x,y)
        if c==4: mset(x+1,y+1,3) # stone
        if c==9 and chance(0.5): mset(x+1,y+1,3) # rnd stone

        if c==8 and chance(trap_ratio): # arrow trap
          d=1
          if pget(x-1,y)[0]==0: d=-1
          mset(x+1,y+1,16)
          self.make_arrow_trap(x+1,y+1,d)
        if c==12 and chance(spike_ratio): mset(x+1,y+1,35) # spikes
        if c==7: mset(x+1,y+1,1) # entry
        if c==6: mset(x+1,y+1,17) # exit
        if c==13: mset(x+1,y+1,30) # ladder
        if c==5: mset(x+1,y+1,14) # ladder floor
        if c==14 and chance(bat_ratio): # bat
          b=self.make_entity((x+1)*8+4,(y+1)*8+4,self.entities)
          add_params({
            "spr":85,
            "fs":8,
            "name":"bat",
            "update":self.bat_update,
            "on_roofhit":self.bat_roofhit,
            "ix":0.5,
            "iy":0.5,
            "mode":0 #hang
          },b)
        # help(crate/damsel) or stone or gap
        if c==15 and help_count>0:
          if chance(0.1):
            help_count+=1
            if chance(0.5):
              hlp=self.make_item(x+1,y,57)
              hlp["y"]+=4
              hlp["h"]=8
              hlp["name"]="crate"
              hlp["on_hit"]=self.crate_break
            else:
              self.make_damsel(x+1,y)
          elif chance(0.5):
            mset(x+1,y+1,3)
        # spider
        if c==10 and chance(spider_ratio): self.make_spider((x+1)*8+4,(y+1)*8+4,0)
        # snake
        if c==11 and chance(snake_ratio): self.make_snake((x+1)*8+4,(y+1)*8+4)
        if c==3: # altar
          mset(x,y-5,78)
          mset(x+1,y-5,79)
          mset(x,y-4,94)
          mset(x+1,y-4,95)
          mset(x,y-3,0)
          mset(x+1,y-3,0)
          mset(x,y-2,110)
          mset(x+1,y-2,111)
          mset(x,y-1,127)
          mset(x+1,y-1,127)

          mset(x,y+1,32)
          mset(x+1,y+1,33)
          idol=self.make_item(x,y,44)
          idol["x"]+=5
          idol["y"]-=4
          add_params({
            "name":"idol",
            "h":8,
            "value":100,
            "on_grab":self.grab_idol,
            "trap":True,
            "big":True
          },idol)

    # make frame
    for x in range(0,42):
      mset(x,0,3)
      mset(x,33,3)
    for y in range(0,34):
      mset(0,y,3)
      mset(41,y,3)

    # place gold
    for x in range(1,41):
      for y in range(1,33):
        if mget(x,y)==3:
          n=self.is_free(mget(x,y-1))
          s=not self.is_dirt(mget(x,y+1))

          # can place item
          if (n and s) or (n and y>0):
            if chance(treasure_ratio):
              self.make_gold(x,y-1,62+rnd(2)) # gold
            elif chance(0.02):
              if chance(0.6):
                self.make_item(x,y-1,29) # stone
              else:
                e=self.make_item(x,y-1,28) # pot
                e["on_landed"]=self.pot_break
                e["on_sidecol"]=self.pot_break
                e["on_hit"]=self.pot_break

          # have gold inside?
          if chance(0.1):
            mset(x,y,mget(x,y)+16)
          elif chance(0.05) and not s:
            # place a block
            mset(x,y,47)

        # background tiles
        if mget(x,y)==0 and chance(0.2):
          mset(x,y,48+flr(rnd(3)))

    # fix tile look
    self.auto_tile(0,0,48,34)

    # parse level
    for x in range(0,42):
      for y in range(0,34):
        tile=mget(x,y)
        # player
        if tile==1:
          self.pl["x"]=x*8+4
          self.pl["y"]=y*8+4
          self.camx=self.pl["x"]-64
          self.camy=self.pl["y"]-64
          if self.pl not in self.entities:
            self.entities.append(self.pl)
        # gold
        if tile==62 or tile==63:
          self.make_gold(x,y,tile)
          mset(x,y,0)
        # item
        if tile==28 or tile==29:
          self.make_item(x,y,tile)
          mset(x,y,0)

  def make_spider(self,x,y,mode):
    s=self.make_entity(x,y,self.entities)
    add_params({"spr":82,"name":"spider","update":self.spider_update,
      "on_landed":self.spider_landed,
      "on_sidecol":self.spider_sidecol,
      "mode":mode},s)
    if mode==1: self.activate_spider(s)

  def make_snake(self,x,y):
    s=self.make_entity(x,y,self.entities)
    add_params({"name":"snake","fs":8,"spr":80,"frames":2,"delay":5,
      "dir":(1 if chance(0.5) else -1),"g":0.5,
      "update":self.snake_update,"on_sidecol":self.snake_sidecol
    },s)
    s["dx"]=s["dir"]/2

  def spider_sidecol(self,e):
    e["dx"]=e.get("odx",0)

  def shake(self,length,pwr):
    self.screenshake=length
    self.screenshake_pwr=pwr

  def is_free(self,tile):
    if tile==0 or tile==48 or tile==49: return True
    return False

  def is_dirt(self,tile):
    if (tile>=2 and tile<=5) or (tile>=18 and tile<=21): return True
    return False

  def auto_tile(self,sx,sy,w,h):
    for x in range(sx,sx+w):
      for y in range(sy,sy+h):
        tile=mget(x,y)
        if self.is_dirt(tile):
          n=not self.is_dirt(mget(x,y-1))
          s=not self.is_dirt(mget(x,y+1))
          has_gold=16 if tile>15 else 0
          if n and s:
            mset(x,y,5+has_gold)
          else:
            if n: mset(x,y,2+has_gold)
            if s: mset(x,y,4+has_gold)

  def make_player(self,tx,ty):
    self.pl=self.make_entity(tx*8+4,ty*8+4,self.entities if hasattr(self,'entities') else [])
    add_params({"name":"player",
      "jumpable":False,
      "g":0.5,
      "spr":64,
      "frames":2,
      "fs":8,
      "mode":0,
      "draw":self.draw_player,
      "on_landed":self.player_landed,
      "on_air":self.player_fall,
      "hits_from_above":True,
      "collides_with_player":False,
      "money":0,
      "health":3,
      "kills":0,
      "dead_timer":0,
      "grab_cooldown":0,
      "whip":0,
      "holding":1,
      "item":None,
      "stowed_item":None,
      "bombs":[],
      "ropes":[]
    },self.pl)
    self.add_ropes(3)
    self.add_bombs(3)

  def add_bombs(self,amnt):
    for i in range(amnt):
      b=self.make_bomb(0,0)
      self.pl["bombs"].append(b)
      if b in self.items: self.items.remove(b)

  def add_ropes(self,amnt):
    for i in range(amnt):
      b=self.make_rope(0,0)
      self.pl["ropes"].append(b)
      if b in self.items: self.items.remove(b)

  def crate_break(self,e,whipped=False):
    if e in e["tbl"]: e["tbl"].remove(e)
    for i in range(7):
      p=self.make_entity(e["x"],e["y"],self.particles)
      add_params({
        "spr":104,"ix":1,"g":0.3,"col":False,
        "dir":sgn(rnd()-0.5),
        "dx":rnd(2)-1,
        "dy":-rnd(1),
        "life":5+rnd(5)
      },p)
    ne=self.make_entity(e["x"],e["y"],self.items)
    ne["spr"]=39+flr(rnd(2))
    ne["g"]=0.5
    ne["can_take"]=True
    ne["value"]=-1 if ne["spr"]==39 else -2

  def pot_break(self,e,whipped=False):
    odx=e.get("odx",0)
    ody=e.get("ody",0)
    if abs(odx)>2 or abs(ody)>2 or whipped:
      if e in e["tbl"]: e["tbl"].remove(e)
      r=rnd(1)
      if r<0.2:
        self.make_snake(e["x"],e["y"])
      elif r<0.4:
        self.make_spider(e["x"],e["y"],1)
      elif r<0.6:
        self.make_gold(e["x"]/8,e["y"]/8,60+rnd(4))

      for i in range(7):
        p=self.make_entity(e["x"],e["y"],self.particles)
        add_params({
          "spr":103,"ix":1,"g":0.3,"col":False,
          "dir":sgn(rnd()-0.5),
          "dx":rnd(2)-1,
          "dy":-1-rnd(2),
          "life":5+rnd(5)
        },p)

  def make_arrow_trap(self,tx,ty,d):
    e=self.make_entity(tx*8+4,ty*8+4,self.entities)
    add_params({
      "name":"arrow trap",
      "spr":34,
      "dir":d,
      "col":False,
      "update":self.update_arrow_trap,
      "ammo":1
    },e)

  def is_triggering_arrow_trap(self,at,e):
    dist=48 # 6 tiles
    if e["dx"]!=0 or e["dy"]!=0:
      in_range=False
      if at["dir"]>0 and e["x"]>at["x"] and e["x"]<at["x"]+dist: in_range=True
      if at["dir"]<0 and e["x"]<at["x"] and e["x"]>at["x"]-dist: in_range=True
      if in_range:
        if e["y"]>=at["y"]-5 and e["y"]<=at["y"]+3:
          return True
    return False

  def update_arrow_trap(self,at):
    if at["ammo"]==0: return
    for e in list(self.items):
      if self.is_triggering_arrow_trap(at,e):
        self.fire_arrow(at)
        return
    for e in list(self.entities):
      if self.is_triggering_arrow_trap(at,e):
        self.fire_arrow(at)
        return

  def fire_arrow(self,at):
    sfx(3)
    at["ammo"]-=1
    e=self.make_entity(at["x"]+at["dir"]*7,at["y"],self.new_items)
    add_params({
      "name":"arrow",
      "spr":43,
      "h":4,
      "dir":at["dir"],
      "dy":-1,
      "dx":7*at["dir"],
      "ix":0.98,
      "g":0.5,
      "knock_down":True,
      "damage":2,
      "use":self.item_throw,
      "drop":self.item_drop,
      "on_landed":self.item_landed,
      "on_sidecol":self.item_sidecol,
      "can_grab":True
    },e)

  def spider_update(self,e):
    dx=self.pl["x"]-e["x"]
    if e.get("health",1)>0:
      if e["mode"]==0:
        if self.pl["y"]>e["y"] and abs(dx)<8: self.activate_spider(e)
      else:
        if e.get("jump_delay",0)>0: e["jump_delay"]-=1
        if e.get("jump_delay",0)<=0 and not e.get("inair",False):
          e["spr"]=84
          e["dx"]=dx/20
          e["dy"]=-rnd(3)-3
    self.update_entity(e)

  def activate_spider(self,e):
    e["mode"]=1
    e["spr"]=84
    e["g"]=0.5
    e["ix"]=1
    e["jump_delay"]=5

  def spider_landed(self,e):
    e["jump_delay"]=5+rnd(10)
    e["spr"]=83
    e["dx"]=0

  def bat_update(self,e):
    dx=self.pl["x"]-e["x"]
    dy=self.pl["y"]-e["y"]+4
    d=sqrt(dx*dx+dy*dy)
    a=atan2(dx,dy)

    if e.get("health",1)>0:
      if e["mode"]==0: # hang
        if d<48 and self.pl.get("health",0)>0 and e["y"]<self.pl["y"]+1:
          e["spr"]=86
          e["frames"]=2
          e["frame"]=1
          e["mode"]=1
      elif e["mode"]==1: # track
        e["dx"]=0.5*cos(a)
        e["dy"]=0.5*sin(a)
        e["dir"]=sgn(e["dx"])
        if d>80 or self.pl.get("health",0)<=0: e["mode"]=2
      else: # return to ceiling
        e["dy"]-=0.2

    self.update_entity(e)

  def bat_roofhit(self,e):
    if e["mode"]!=2: return
    e["spr"]=85
    e["frame"]=0
    e["frames"]=0
    e["mode"]=0
    e["dx"]=0
    e["dy"]=0

  def snake_update(self,e):
    e["delay"]-=1
    if e.get("bleed_timer",0)>0:
      e["fs"]=9999
      e["frames"]=1
      e["spr"]=102
      e["delay"]=99

    if e["delay"]<0:
      if chance(0.1):
        e["dx"]=0
        e["delay"]=15+rnd(60)
      else:
        e["dir"]=1 if chance(0.5) else -1
        e["dx"]=0.2*e["dir"]
        e["ix"]=1
        e["delay"]=60+rnd(60)

    if not e.get("inair",False) and fget(mget((e["x"]+e["dir"]*2)/8,e["y"]/8+1))==0:
      e["dir"]=-e["dir"]
      e["dx"]=-e["dx"]
    self.update_entity(e)

  def snake_sidecol(self,e):
    e["delay"]=0

  def check_item_exit(self,e):
    if fget(mget(e["x"]/8,(e["y"]-4)/8),7):
      if e["name"]=="idol": self.pl["money"]+=e["value"]
      if e in e["tbl"]: e["tbl"].remove(e)
      self.pl["item"]=None
      self.switch_to_whip()
      sfx(7)

  def grab_idol(self,idol):
    if idol.get("trap",False):
      idol["trap"]=False
      # make boulder
      e=self.make_entity(-100,-100,self.entities)
      add_params({
        "name":"boulder",
        "flip_on_hit":False,
        "knock_down":True,
        "jumpable":False,
        "spr":74,
        "fs":2,
        "frames":2,
        "tw":2,
        "th":2,
        "ix":1,
        "dy":0,
        "g":1,
        "damage":99,
        "health":9999,
        "w":16,
        "h":16,
        "spawnx":idol["x"]-1,
        "spawny":idol["y"]-24,
        "delay":60,
        "update":self.boulder_update,
        "on_landed":self.boulder_landed
      },e)
      self.shake(e["delay"],3)

  def boulder_update(self,e):
    if e.get("delay",0)>0:
      e["delay"]-=1
      if e["delay"]==0:
        e["x"]=e["spawnx"]
        e["y"]=e["spawny"]
        e["dy"]=0.01
        e["dir"]=sgn(self.pl["x"]-e["x"])
        self.shake(2,6)
        e["dropped"]=False
    else:
      bx=e["x"]/8+e["dir"]
      by=e["y"]/8
      tiles=0
      if fget(mget(bx,by),0):
        self.crush_tile(bx,by,e["dx"])
        tiles+=1
      if fget(mget(bx,by-1),0):
        self.crush_tile(bx,by-1,e["dx"])
        tiles+=1
      e["dx"]-=0.20*tiles*sgn(e["dx"])
      self.update_entity(e)
      if tiles>0:
        self.auto_tile(int(bx),int(by)-2,1,4)
        self.shake(3,3)
        sfx(6)

      if abs(e["dx"])<0.6 and e["dy"]==0:
        tx=int(e["x"]/8)
        ty=int(e["y"]/8)-1
        mset(tx,ty,74)
        mset(tx+1,ty,75)
        mset(tx,ty+1,90)
        mset(tx+1,ty+1,91)
        if e in e["tbl"]: e["tbl"].remove(e)

  def crush_tile(self,tx,ty,v):
    tx=int(tx)
    ty=int(ty)
    # check for gold
    tile=mget(tx,ty)
    if tile>=18 and tile<=21: self.make_gold_pieces(tx,ty)
    # remove tile
    mset(tx,ty,0)
    # particles
    amnt=int(3+rnd(3))
    for i in range(amnt):
      p=self.make_entity(tx*8,ty*8,self.particles)
      add_params({
        "spr":120+rnd(2),
        "ix":0.98,
        "dx":v*(1+rnd(1)),
        "dy":-1-rnd(1),
        "g":0.3,
        "life":20+rnd(10),
        "col":False
      },p)

  def boulder_landed(self,e):
    if not e.get("dropped",False):
      e["dx"]=3*e["dir"]
      e["dropped"]=True
    self.shake(6,6)
    sfx(6)

  def make_gold(self,tx,ty,tile):
    e=self.make_entity(tx*8+4,ty*8+4,self.items)
    e["spr"]=flr(tile)
    e["g"]=0.5
    e["value"]=5
    e["can_take"]=True
    if e["spr"]==60 or e["spr"]==62: e["value"]*=3
    return e

  def make_item(self,tx,ty,tile):
    e=self.make_entity(tx*8+4,ty*8+3,self.items)
    add_params({
      "name":"#"+str(tile),
      "spr":tile,
      "ix":0.98,
      "g":0.5,
      "h":4,
      "use":self.item_throw,
      "drop":self.item_drop,
      "on_landed":self.item_landed,
      "on_sidecol":self.item_sidecol,
      "can_grab":True
    },e)
    e["y"]+=4
    return e

  def item_sidecol(self,e):
    e["dx"]=-e.get("odx",0)*0.5
    if abs(e["dx"])<0.1: e["dx"]=0

  def item_landed(self,e):
    e["dx"]*=0.3
    if abs(e["dx"])<0.2: e["dx"]=0
    if abs(e.get("ody",0))>2:
      e["dy"]=-e.get("ody",0)*0.3
    else:
      e["dx"]=0

  def item_throw(self,e):
    e["cooldown"]=3
    e["damage"]=1
    e["dx"]=self.pl["dir"]*(3 if self.pl["dy"]<0 else 4)
    e["dy"]=-5 if self.pl["dy"]<0 else -2
    self.pl["item"]=None
    self.switch_to_whip()
    sfx(3)

  def item_drop(self,e):
    e["cooldown"]=3
    e["dy"]=-1
    e["dx"]=self.pl["dir"]/2
    self.pl["item"]=None
    self.switch_to_whip()
    sfx(3)

  def make_damsel(self,x,y):
    di=self.make_item(x,y,11)
    di["name"]="damsel"
    di["y"]+=4
    di["h"]=8
    di["big"]=True

    de=self.make_entity(di["x"],di["y"],self.entities)
    de["name"]="damsel"
    de["spr"]=16
    de["collides_with_player"]=False
    de["update"]=self.damsel_e_update
    de["item"]=di
    de["health"]=3
    de["damage"]=0

    di["entity"]=de

    p={"g":0.5,"ix":0.98}
    add_params(p,di)
    add_params(p,de)

  def damsel_e_update(self,e):
    self.update_entity(e)
    e["x"]=e["item"]["x"]
    e["y"]=e["item"]["y"]

    # dead?
    if e.get("health",1)<1: e["item"]["spr"]=13

    # at gate?
    if fget(mget(e["x"]/8,(e["y"]-4)/8),7):
      self.pl["health"]+=1
      if e in e["tbl"]: e["tbl"].remove(e)
      if e["item"] in e["item"]["tbl"]: e["item"]["tbl"].remove(e["item"])
      self.pl["item"]=None
      self.switch_to_whip()
      sfx(7)

  def make_bomb(self,tx,ty):
    e=self.make_item(tx,ty,25)
    add_params({
      "name":"bomb",
      "h":4,
      "use":self.bomb_throw,
      "drop":self.bomb_drop,
      "update":self.bomb_update,
      "timer":0
    },e)
    return e

  def bomb_update(self,e):
    if e.get("timer",0)>0:
      e["timer"]-=1
      e["spr"]=26+flr(e["timer"]/2)%2
      if e["timer"]==0:
        e["life"]=1
        # explode
        self.shake(5,6)
        self.make_explosion(e["x"]-8,e["y"]-8)
        # destroy entities & tiles
        ex=flr(e["x"]/8)
        ey=flr(e["y"]/8)
        hitarea=[[0,0,1,0,0],
                 [0,1,1,1,0],
                 [1,1,1,1,1],
                 [0,1,1,1,0],
                 [0,0,1,0,0]]
        for xi in range(5):
          for yi in range(5):
            if hitarea[xi][yi]==1:
              tx=ex+xi-2
              ty=ey+yi-2
              # entities
              for e2 in list(self.entities):
                if abs(tx*8+4-e2["x"])<9 and abs(ty*8+4-e2["y"])<9:
                  self.damage_entity(e2,None,99,0)
              # tile
              tile=mget(tx,ty)
              if tile>=2 and tile<=5: mset(tx,ty,0)
              if tile==47 or tile==35 or tile==36: mset(tx,ty,0)
              if tile>=18 and tile<=21:
                mset(tx,ty,0)
                self.make_gold_pieces(tx,ty)
        self.auto_tile(ex-2,ey-3,5,7)

    self.update_entity(e)

  def make_gold_pieces(self,tx,ty):
    amnt=int(rnd(3)+1)
    for i in range(amnt):
      g=self.make_gold(tx,ty,60+rnd(2))
      add_params({
        "dx":rnd(5)-3,
        "dy":rnd(5)-3,
        "g":0.5,
        "ix":0.98,
        "can_take":True,
        "inair":True
      },g)

  def bomb_throw(self,e):
    self.bomb_activate(e)
    self.item_throw(e)

  def bomb_drop(self,e):
    self.bomb_activate(e)
    self.item_drop(e)

  def bomb_activate(self,e):
    e["spr"]=26
    e["timer"]=60
    e["can_grab"]=False

  def make_explosion(self,x,y):
    sfx(5)
    # dirt
    amnt=int(4+rnd(4))
    for i in range(amnt):
      e=self.make_entity(x+rnd(24),y-8+rnd(32),self.particles)
      add_params({
        "spr":118+rnd(2),
        "dir":sgn(rnd(2)-1),
        "dy":rnd(0.6)+0.4,
        "g":0.1,
        "life":10+rnd(4),
        "col":False,
      },e)

    # smalls
    amnt=int(4+rnd(4))
    for i in range(amnt):
      e=self.make_entity(x+8,y+8,self.particles)
      a=rnd(0.7)-0.1
      f=2+rnd(2)
      add_params({
        "spr":112,
        "dir":sgn(rnd(2)-1),
        "dx":f*cos(a),
        "dy":f*sin(a),
        "ix":0.95,
        "g":0.3,
        "fs":2+flr(rnd(3)),
        "frames":6,
        "col":False
      },e)
      e["life"]=e["fs"]*e["frames"]-1

    # big
    e=self.make_entity(x,y,self.particles)
    add_params({
      "dir":sgn(rnd(2)-1),
      "spr":144,
      "tw":3,
      "th":3,
      "fs":2,
      "frames":3,
      "col":False
    },e)
    e["life"]=e["fs"]*e["frames"]-1

  def make_rope(self,tx,ty):
    e=self.make_item(tx,ty,41)
    add_params({
      "name":"rope",
      "use":self.rope_throw,
      "drop":self.rope_drop,
      "activated":False,
      "on_roofhit":self.rope_roof_hit,
      "on_landed":self.rope_on_landed,
      "update":self.rope_update,
      "steps":0,
      "h":8,
      "flip_on_hit":False
    },e)
    return e

  def rope_update(self,e):
    if e.get("activated",False):
      tx=flr(e["x"]/8)
      ty=flr(e["y"]/8)
      if mget(tx,ty)!=31 and mget(tx,ty)!=15:
        if e["steps"]==0 and e["dy"]>0:
          mset(tx,ty,15)
        else:
          mset(tx,ty,31)
        e["steps"]+=1
        if e["steps"]==8:
          e["on_roofhit"](e)
    self.update_entity(e)

  def rope_drop(self,e):
    # can drop?
    tx=flr((e["x"]+self.pl["dir"]*4)/8)+self.pl["dir"]*0
    ty=flr(e["y"]/8)
    ty2=flr(e["y"]/8)+1

    if not self.is_solid(tx,ty) and not self.is_solid(tx,ty2):
      add_params({
        "x":tx*8+4,
        "spr":31,
        "dy":4,
        "dir":1,
        "g":0,
        "activated":True
      },e)
      self.pl["item"]=None
      self.switch_to_whip()

  def rope_throw(self,e):
    sfx(3)
    # adjust position
    e["x"]=flr(e["x"]/8)*8+4
    e["y"]-=5

    # make sure there is nothing directly on top
    if fget(mget(e["x"]/8,e["y"]/8),0):
      return

    # drop it
    e["spr"]=15
    e["dy"]=-4
    e["dir"]=1
    e["g"]=0
    e["activated"]=True
    self.pl["item"]=None
    self.switch_to_whip()

  def rope_on_landed(self,e):
    if e in self.items: self.items.remove(e)

  def rope_roof_hit(self,e):
    mset(flr(e["x"]/8),flr(e["y"]/8),31 if e["dy"]>0 else 15)
    if e in self.items: self.items.remove(e)

  def player_fall(self,e=None):
    self.jumps_left=max(0,self.jumps_left-1)

  def player_faint(self):
    pl=self.pl
    pl["bleed_timer"]=60 if pl["health"]==0 else 30
    pl["faint_timer"]=pl["bleed_timer"]

    if pl["mode"]==4: return

    pl["mode"]=3
    pl["spr"]=68
    pl["frame"]=0
    pl["frames"]=1

    if pl["item"]!=None and pl["holding"]==1:
      pl["item"]["drop"](pl["item"])
      pl["item"]=None

  def player_landed(self,e):
    self.jumps_left=self.max_jumps

    impact=0
    ody=self.pl.get("ody",0)
    if ody>=8: impact+=1
    if ody>=11: impact+=1
    if ody>=13: impact+=97

    if impact>0:
      self.damage_entity(self.pl,None,impact)
      self.player_faint()

    if self.pl["mode"]==3: # fainted
      # bounce
      if ody>3:
        self.pl["dy"]=-0.3*ody

  def drop_from_ledge(self):
    add_params({"mode":0,"spr":64,"frames":2,"dx":-self.pl["dir"],"grab_cooldown":5},self.pl)

  def update_play(self):
    pl=self.pl

    if not btn(2): self.ok_to_jump=True   # UP
    if not btn(3): self.ok_to_crouch=True  # DOWN

    # mode 0 = idle/ground/jump
    if pl["mode"]==0:
      if pl["item"]!=None and pl["item"].get("name")=="idol":
        self.check_item_exit(pl["item"])

      if btnp(4): self.switch_item()  # B = switch item

      if pl["grab_cooldown"]>0: pl["grab_cooldown"]-=1

      pl["grab"]=False
      # left/right
      if btn(0): # LEFT
        pl["dx"]-=2
        pl["dir"]=-1
        pl["grab"]=True
      if btn(1): # RIGHT
        pl["dx"]+=2
        pl["dir"]=1
        pl["grab"]=True

      # whip?
      if btnp(5) and pl["item"]==None: # A = action
        pl["whip"]=10
        sfx(0)
      if pl["whip"]>0: pl["whip"]-=1

      # use item?
      if btnp(5) and pl["item"]!=None: # A = action
        if btn(3): # DOWN = drop
          pl["item"]["drop"](pl["item"])
          self.ok_to_crouch=False
        else:
          pl["item"]["use"](pl["item"])

      # jump / grab climbable
      if btn(2): # UP
        # check for climbables
        if fget(mget(pl["x"]/8,pl["y"]/8),2):
          pl["mode"]=1
          pl["dx"]=0
        elif fget(mget(pl["x"]/8,pl["y"]/8),7):
          self.level+=1
          self.start_next_level(self.level)
          return
        elif self.jumps_left>0 and self.ok_to_jump:
          # regular jump
          pl["dy"]=-3.2
          self.jumps_left-=1
          pl["inair"]=True
          self.ok_to_jump=False
          sfx(4)

      # climb down
      if btn(3): # DOWN
        if fget(mget(pl["x"]/8,(pl["y"]+4)/8),2):
          pl["mode"]=1
          pl["dx"]=0
          pl["y"]+=1

    elif pl["mode"]==1:
      # mode 1 = climbing
      pl["whip"]=0
      pl["dy"]=0
      pl["spr"]=70

      pl["x"]+=(8*flr(pl["x"]/8)+4 - pl["x"])*0.4

      if btn(2): pl["dy"]=-1 # UP
      if btn(3): pl["dy"]=1  # DOWN

      drop=False
      if btn(0): # LEFT
        pl["dx"]-=2
        pl["dir"]=-1
        drop=True
      if btn(1): # RIGHT
        pl["dx"]+=2
        pl["dir"]=1
        drop=True

      # still on climbable?
      if not fget(mget(pl["x"]/8,(pl["y"]-2)/8),2) and not fget(mget(pl["x"]/8,(pl["y"]+3)/8),2):
        drop=True

      if drop:
        add_params({
          "inair":True,
          "mode":0,
          "spr":64,
          "frame":0,
          "frames":2
        },pl)
        self.ok_to_jump=False

    elif pl["mode"]==2:
      # mode 2 = ledge
      add_params({
        "whip":0,
        "dx":0,
        "dy":0,
        "spr":69,
        "frame":0,
        "frames":1
      },pl)

      if btn(2) and self.ok_to_jump: # UP = jump from ledge
        add_params({
          "mode":0,
          "spr":64,
          "frame":0,
          "frames":2,
          "dy":-1
        },pl)
        self.ok_to_jump=False

      if btn(3): self.drop_from_ledge() # DOWN = drop

    elif pl["mode"]==3:
      # mode 3 = fainted
      pl["whip"]=0
      pl["faint_timer"]-=1
      if pl["faint_timer"]==0:
        if pl["health"]>0:
          pl["spr"]=64
          pl["frames"]=2
          pl["ix"]=0
          pl["mode"]=0
        else:
          # dead
          pl["mode"]=4

    elif pl["mode"]==4:
      # mode 4 = dead
      pl["dead_timer"]+=1
      if btnp(5) and pl["dead_timer"]>15: # A = restart
        self.swap_state(self.title_state)
        return

    # Cache player position for hot loops
    px=pl["x"]
    py=pl["y"]
    pdir=pl["dir"]
    pwhip=pl["whip"]
    pitem=pl["item"]
    pmode=pl["mode"]

    # items loop
    items=self.items
    ents=self.entities
    for e in items[:]:
      ex=e["x"]
      ey=e["y"]
      if e.get("inair")==True:
        # check for impact with entities
        edx=e["dx"]
        edy=e["dy"]
        v2=edx*edx+edy*edy
        if v2>9: # v>3 squared
          ecool=e.get("cooldown",0)
          ename=e.get("name")
          for e2 in ents:
            if ecool==0 or e2!=pl:
              if abs(e2["x"]-ex)<5 and abs(e2["y"]-ey)<5:
                if not(ename=="rope" and e2==pl) and ename!=e2.get("name"):
                  self.damage_entity(e2,e)
                  if e.get("flip_on_hit",True): e["dx"]=-e2["dx"]/2

      # instant pickup?
      if e.get("can_take",False):
        if abs(px-ex)<4 and abs(py-ey)<4:
          val=e.get("value")
          if val is not None:
            sfx(7)
            if val==-2: self.add_bombs(3)
            if val==-1: self.add_ropes(3)
            if val>0: pl["money"]+=val
          if e in items: items.remove(e)
          continue

      if e!=pitem:
        # pickup item?
        if (pmode==0 and btn(3) and
            e.get("can_grab",False) and
            not pl.get("inair",False) and
            abs(px-ex)<5 and
            abs(py-ey)<5 and
            self.ok_to_crouch):
          if pl.get("stowed_item") is not None:
            items.append(pl["stowed_item"])
            self.set_item_to_player_pos(pl["stowed_item"])
            pl["stowed_item"]["inair"]=True
            pl["stowed_item"]=None
          if pl["holding"]==2:
            if pl["item"] in items: items.remove(pl["item"])
            pl["bombs"].append(pl["item"])
          if pl["holding"]==3:
            if pl["item"] in items: items.remove(pl["item"])
            pl["ropes"].append(pl["item"])

          pl["item"]=e
          pl["holding"]=1
          self.ok_to_crouch=False
          og=e.get("on_grab")
          if og: og(e)

        e["update"](e)

      # check whip
      if pwhip>0:
        if (abs(px+8*pdir-ex)<6 and
            abs(py-ey+2)<8 and e.get("on_hit")):
          e["on_hit"](e,True)
          pl["whip"]=0
          pwhip=0

    # entities loop
    whipx=px+8*pdir
    for e1 in ents[:]:
      e1x=e1["x"]
      e1y=e1["y"]

      # Only do e2e collision if near player (within ~96px)
      near_player=abs(e1x-px)<96 and abs(e1y-py)<96
      if near_player and e1.get("damage",1)>=0:
        e1w=e1["w"]
        e1h=e1["h"]
        e1col=e1.get("collides_with_player",True)
        for e2 in ents:
          if e1!=e2 and (e1col or e2.get("collides_with_player",True)):
            dx=abs(e2["x"]-e1x)
            if dx<16: # quick distance pre-check
              if (dx<(e2["w"]+e1w)/2-2 and
                  abs(e2["y"]-e1y)<(e2["h"]+e1h)/2-2):
                self.e2e_coll(e1,e2)

      # spikes?
      if e1.get("inair",False) and e1.get("health",0)>0 and e1.get("name")!="bat":
        if e1["dy"]>0:
          tx=flr(e1x/8)
          ty=flr((e1y+3)/8)
          if fget(mget(tx,ty),3):
            mset(tx,ty,36)
            self.damage_entity(e1,None,99)

      # check whip
      if e1!=pl and pwhip>0:
        if (abs(whipx-e1x)<6 and
            abs(py-e1y)<6 and
            e1.get("bleed_timer",0)==0):
          self.damage_entity(e1,None,1,pdir,-1)

      # Only run full physics for nearby entities, just animate far ones
      if near_player or e1==pl:
        e1["update"](e1)
      else:
        # minimal update: just animation tick
        e1["t"]+=1
        ef=e1["frames"]
        if ef>0:
          if e1["t"]%e1["fs"]==0: e1["frame"]+=1
          if e1["frame"]==ef: e1["frame"]=0

    if pl["item"]!=None:
      self.set_item_to_player_pos(pl["item"])

    # Only update nearby particles
    for e in self.particles[:]:
      e["update"](e)

    # add new items
    if self.new_items:
      items.extend(self.new_items)
      self.new_items=[]

  def bleed(self,x,y):
    if len(self.particles)>30: return  # cap particles
    e=self.make_entity(x,y,self.particles)
    add_params({
      "spr":99,
      "dx":rnd(4)-2,
      "dy":-1-rnd(1),
      "ix":0.95,
      "g":0.5,
      "fs":3+flr(rnd(3)),
      "frames":3,
      "col":False
    },e)
    e["life"]=e["fs"]*e["frames"]-1

  # e1 hits e2
  def e2e_coll(self,e1,e2):
    # no hit if already bleeding
    if e1.get("bleed_timer",0)>0 or e2.get("bleed_timer",0)>0: return

    over=e1
    under=e2
    if e2["y"]<e1["y"]:
      over=e2
      under=e1

    # if coming from above
    if (over.get("hits_from_above",False) and over.get("inair",False) and
        over["dy"]>0 and under.get("jumpable",True)):
      self.damage_entity(under,over,0,-3)
      if over.get("flip_on_hit",True): over["dy"]=-3
    else:
      pl=self.pl
      # regular hit only if player or boulder is involved
      if over==pl or over.get("name")=="boulder":
        self.damage_entity(over,under,1*sgn(over["x"]-under["x"]),-1)
      if under==pl or over.get("name")=="boulder":
        self.damage_entity(under,over,1*sgn(under["x"]-over["x"]),-1)

  def damage_entity(self,e1,e2,impact=0,dx=None,dy=None):
    if e2 is not None:
      e1["health"]-=e2.get("damage",1)
      if e1.get("flip_on_hit",True): e1["dx"]=3*sgn(e1["x"]-e2["x"])
    else:
      e1["health"]-=impact

    if dx is not None: e1["dx"]+=dx
    if dy is not None and e1.get("flip_on_hit",True):
      e1["inair"]=True
      e1["dy"]+=dy

    if e1.get("health",0)<=0 and e1!=self.pl:
      e1["ix"]=0.7
      self.pl["kills"]+=1

    e1["dy"]=-3
    e1["bleed_timer"]=30

    if e1==self.pl:
      if (e2 and e2.get("knock_down",False)) or self.pl["health"]<=0:
        self.player_faint()
      elif self.pl["mode"]==2:
        self.drop_from_ledge()
    sfx(1)

  def set_item_to_player_pos(self,e):
    pl=self.pl
    e["x"]=pl["x"]+pl["dir"]*3
    e["y"]=pl["y"]+pl["frame"]-1-e["h"]/2+4
    e["dir"]=pl["dir"]

  def switch_to_whip(self):
    self.pl["holding"]=1
    # use stowed item if any
    if self.pl.get("stowed_item") is not None:
      self.pl["item"]=self.pl["stowed_item"]
      self.pl["stowed_item"]=None
      self.items.append(self.pl["item"])
    else:
      self.pl["item"]=None

  def switch_item(self):
    pl=self.pl
    if pl["item"] and pl["item"].get("big"): return
    # handle current item
    if pl["holding"]==1:
      if pl["item"]!=None:
        # stow away
        if pl["item"] in self.items: self.items.remove(pl["item"])
        pl["stowed_item"]=pl["item"]
        pl["item"]=None
    if pl["holding"]==2:
      pl["bombs"].append(pl["item"])
      if pl["item"] in self.items: self.items.remove(pl["item"])
      pl["item"]=None
    if pl["holding"]==3:
      pl["ropes"].append(pl["item"])
      if pl["item"] in self.items: self.items.remove(pl["item"])
      pl["item"]=None

    # check for next item
    pl["holding"]+=1
    if pl["holding"]==2 and len(pl["bombs"])==0: pl["holding"]+=1
    if pl["holding"]==3 and len(pl["ropes"])==0: pl["holding"]+=1
    if pl["holding"]>3: pl["holding"]-=3

    # set next item
    if pl["holding"]==1:
      pl["item"]=None
      self.switch_to_whip()
    if pl["holding"]==2:
      pl["item"]=pl["bombs"][0]
      self.items.append(pl["item"])
      pl["item"]["tbl"]=self.items
      pl["bombs"].remove(pl["item"])
    if pl["holding"]==3:
      pl["item"]=pl["ropes"][0]
      self.items.append(pl["item"])
      pl["item"]["tbl"]=self.items
      pl["ropes"].remove(pl["item"])

  def draw_player(self,e=None):
    pl=self.pl
    self.draw_entity(pl)
    if pl["whip"]>0:
      s=122
      if pl["whip"]<9: s=123
      if pl["whip"]<8: s=124
      spr(s,pl["x"]+pl["dir"]*6-4,pl["y"]-4+pl["frame"]%2,1,1,pl["dir"]==-1)

  def draw_play(self):
    cls()
    pl=self.pl

    lx=pl["x"]-self.camx
    ly=pl["y"]-self.camy

    # pan camera
    if lx<48: self.camx-=2
    if lx>80: self.camx+=2
    if ly<48: self.camy+=(ly-48)*0.5
    if ly>80: self.camy+=(ly-80)*0.5

    sx=0
    sy=0
    if self.screenshake>0:
      self.screenshake-=1
      sx=rnd(self.screenshake_pwr)-self.screenshake_pwr/2
      sy=rnd(self.screenshake_pwr)-self.screenshake_pwr/2

    # lock camera inside map (and shake if needed)
    cx=min(208,max(self.camx,0))+sx
    cy=min(144,max(self.camy,0))+sy
    camera(cx,cy)

    # Only render visible tiles (camera viewport + 1 tile margin)
    tx=max(0,int(cx)//8)
    ty=max(0,int(cy)//8)
    tw=min(18,50-tx) # 128/8=16 tiles + 2 margin
    th=min(18,34-ty)
    map(tx,ty,tx*8,ty*8,tw,th,0)

    for e in list(self.entities):
      if abs(e["x"]-cx-64)<80 and abs(e["y"]-cy-64)<80:
        e["draw"](e)

    for e in list(self.items):
      if abs(e["x"]-cx-64)<80 and abs(e["y"]-cy-64)<80:
        e["draw"](e)

    for e in list(self.particles):
      if abs(e["x"]-cx-64)<80 and abs(e["y"]-cy-64)<80:
        e["draw"](e)

    # hud
    camera()
    self.spro(25,0,4,0)
    self.printo(str(len(pl["bombs"])),11,3,7,0)
    self.spro(41,21,0,0)
    self.printo(str(len(pl["ropes"])),31,3,7,0)
    self.spro(62,45,0,0)
    self.printo(str(pl["money"]*10),56,3,7,0)

    for i in range(1,pl["health"]+1):
      self.spro(42,128-i*9,2,0)

    # instructions, 10 seconds, first level
    if pl["t"]<300 and self.level==1:
      rectfill(0,114,127,127,1)
      # Thumby Color controls
      print("dpad-move  up-jump/climb",4,115,7)
      print("a-action b-switch item",4,122,7)

    # game over
    if pl["mode"]==4:
      y=max(44,128-pl["dead_timer"])
      self.printo("game over",46,y,7,1)
      self.printo("depth: "+str(self.level),42,y+20,7,1)
      self.printo(" gold: "+str(pl["money"]*10),42,y+28,7,1)
      self.printo("kills: "+str(pl["kills"]),42,y+36,7,1)

  def spro(self,id,dx,dy,oc):
    for i in range(16):
      pal(i,oc)
    spr(id,dx-1,dy)
    spr(id,dx+1,dy)
    spr(id,dx,dy-1)
    spr(id,dx,dy+1)
    pal()
    spr(id,dx,dy)

  # --------------------------------
  # title screen
  # --------------------------------

  def init_title(self):
    self.bgy=0
    self.t=0

  def update_title(self):
    self.bgy-=0.5
    if self.bgy<-256: self.bgy=0
    self.t+=1
    if btnp(5): self.swap_state(self.play_state) # A = start

  def draw_title(self):
    cls()
    map(112,0,0,int(self.bgy),16,32,0)
    map(112,0,0,int(self.bgy)+256,16,32,0)

    pal(4,2)
    spr(185,36,33,7,1)
    pal()
    spr(185,36,32,7,1)

    self.prints("-endless descent-",30,42,2,1)
    self.prints("press a",48,64,4 if self.t%32<16 else 2,1)
    self.prints("a demake by @johanpeitz",18,120,2,1)

  # --------------------------------
  # state swapping
  # --------------------------------

  def swap_state(self,s):
    self.next_state=s
    self.change_state=True

  # --------------------------------
  # main loop
  # --------------------------------

  def _update(self):
    if self.change_state:
      self.state=self.next_state
      self.change_state=False
      self.state["init"]()

    self.state["update"]()

  def _draw(self):
    self.state["draw"]()

  # --------------------------------
  # utilities
  # --------------------------------

  def is_solid(self,tx,ty):
    return fget(mget(tx,ty),0)

  def collide_side(self,e):
    ex=e["x"]
    ey=e["y"]
    eh3=e["h"]/3
    i=-eh3
    while i<=eh3:
      yi=ey+i
      t=mget((ex+4)/8,yi/8)
      if fget(t,0):
        e["odx"]=e["dx"]
        e["dx"]=0
        e["x"]=(flr((ex+4)/8))*8-4
        return {"tile":t,"tx":flr((e["x"]+4)/8),"ty":flr(yi/8)}
      t=mget((ex-4)/8,yi/8)
      if fget(t,0):
        e["odx"]=e["dx"]
        e["dx"]=0
        e["x"]=flr((ex-4)/8)*8+12
        return {"tile":t,"tx":flr((e["x"]-4)/8-1),"ty":flr(yi/8)}
      i+=2
    return None

  def should_fall(self,e):
    if e.get("inair",False): return True
    ex=e["x"]
    ew3=e["w"]/3
    newty=flr((e["y"]+e["h"]/2+1)/8)
    i=-ew3
    while i<=ew3:
      tile=mget((ex+i)/8,newty)
      if fget(tile,0) or fget(tile,1):
        return False
      i+=2
    return True

  def collide_floor(self,e):
    if e["dy"]<0:
      return False
    ex=e["x"]
    ey=e["y"]
    eh2=e["h"]/2
    ew3=e["w"]/3
    newty=flr((ey+eh2)/8)
    landed=False
    plmode=self.pl["mode"]
    lastty=e.get("lastty",-1)
    i=-ew3
    while i<=ew3:
      tile=mget((ex+i)/8,newty)
      if fget(tile,0):
        landed=True
        break
      if fget(tile,1) and plmode!=1:
        if lastty<newty:
          landed=True
          break
      i+=2

    if landed:
      e["ody"]=e["dy"]
      e["dy"]=0
      e["y"]=flr((ey+eh2)/8)*8-eh2

    return landed

  def collide_roof(self,e):
    ex=e["x"]
    ey=e["y"]
    eh2=e["h"]/2
    ew3=e["w"]/3
    top=(ey-eh2)/8
    collided=False
    i=-ew3
    while i<=ew3:
      if fget(mget((ex+i)/8,top),0):
        e["dy"]=0
        e["y"]=flr(top)*8+8+eh2
        collided=True
        break
      i+=2
    return collided

  def prints(self,s,x,y,c1,c2):
    print(str(s),x,y+1,c2)
    print(str(s),x,y,c1)

  def printo(self,s,x,y,c1,c2):
    s=str(s)
    print(s,x+1,y,c2)
    print(s,x,y+1,c2)
    print(s,x-1,y,c2)
    print(s,x,y-1,c2)
    print(s,x,y,c1)

  # --------------------------------
  # entities
  # --------------------------------

  def make_entity(self,x,y,t):
    e={
      "name":"unknown",
      "x":x,
      "y":y,
      "dx":0,
      "dy":0,
      "ix":0,
      "iy":1,
      "spr":0,
      "dir":1,
      "life":0,
      "col":True,
      "lastty":-1,
      "jumpable":True,
      "hits_from_above":False,
      "flip_on_hit":True,
      "knock_down":False,
      "collides_with_player":True,
      "health":1,
      "damage":1,
      "cooldown":0,
      "bleed_timer":0,
      "faint_timer":0,
      "draw":self.draw_entity,
      "update":self.update_entity,
      "t":0,
      "w":8,
      "h":8,
      "g":0,
      "tw":1,
      "th":1,
      "frame":0,
      "frames":0,
      "fs":4,
      "tbl":t
    }
    t.append(e)
    return e

  def update_entity(self,e):
    if e.get("cooldown",0)>0: e["cooldown"]-=1

    # inline update_entity_x
    e["x"]+=e["dx"]
    e["dx"]*=e["ix"]

    if e["col"]:
      d=self.collide_side(e)
      if d is not None:
        # stick to ledge?
        if (e.get("grab",False) and e["mode"]==0 and e.get("inair",False) and
            e["dy"]>0 and self.pl["grab_cooldown"]==0):
          f=fget(mget(d["tx"],d["ty"]-1))
          dist=abs(e["y"]-d["ty"]*8)
          if (band(f,1) or band(f,3)) and dist<2:
            e["y"]=d["ty"]*8
            e["dy"]=0
            e["mode"]=2

        # callback
        if e.get("on_sidecol") is not None: e["on_sidecol"](e)

    # store last tile y
    eh2=e["h"]/2
    e["lastty"]=flr((e["y"]+eh2-0.01)/8)

    # inline update_entity_y
    if e.get("inair",False) or not e["col"]:
      e["y"]+=e["dy"]
      e["dy"]=min(e["dy"]+e["g"],13)
      e["dy"]*=e["iy"]

    if e["col"]:
      ody=e["dy"]
      if self.collide_floor(e):
        if e.get("inair")==True and e.get("on_landed") is not None:
          e["ody"]=ody
          e["on_landed"](e)
        e["inair"]=False
      else:
        was_on_ground=e.get("inair",False)==False
        if was_on_ground and e["dy"]==0:
          if self.should_fall(e):
            on_air=e.get("on_air")
            if on_air is not None: on_air(e)
            e["inair"]=True
        else:
          if was_on_ground:
            on_air=e.get("on_air")
            if on_air is not None: on_air(e)
          e["inair"]=True

      if self.collide_roof(e):
        on_rh=e.get("on_roofhit")
        if on_rh: on_rh(e)

    # inline update_entity_a
    e["t"]+=1
    ef=e["frames"]
    if ef>0:
      if e["t"]%e["fs"]==0: e["frame"]+=1
      if e["frame"]==ef: e["frame"]=0
    el=e["life"]
    if el>0 and e["t"]>el:
      if e in e["tbl"]: e["tbl"].remove(e)

    if e.get("bleed_timer",0)>0:
      e["bleed_timer"]-=1
      if chance(0.5): self.bleed(e["x"],e["y"]+4)
      if e["bleed_timer"]<=0 and e.get("health",0)<=0:
        if e in e["tbl"]: e["tbl"].remove(e)

  def draw_entity(self,e):
    spr(e["spr"]+e["frame"]*e["tw"],
      e["x"]-e["w"]/2, e["y"]-e["h"]/2,
      e["tw"], e["th"],
      e["dir"]==-1)

  # --------------------------------
  # map generation
  # --------------------------------

  def make_map(self):
    # PICO-8 uses 1-indexed arrays, so we use 1-5 for x, 1-4 for y
    # m is a dict-of-dicts to match PICO-8's 1-indexed tables
    rx=1+flr(rnd(4))
    ry=1
    srx=rx
    sry=ry
    # m[1..4][1..4] = room types, m[5]=srx, m[6]=sry
    m={}
    for i in range(1,5):
      m[i]={}
      for j in range(1,5):
        m[i][j]=0
    m[5]=srx
    m[6]=sry

    done=False

    # start room
    m[rx][ry]=1

    while not done:
      lrx=rx
      lry=ry
      down=False

      # move to free spot
      tryagain=True
      while tryagain:
        tryagain=False
        r=flr(rnd(5))

        if r<2: rx-=1  # 0&1
        if r>2: rx+=1  # 3&4
        if r==2:
          ry+=1
          down=True

        if rx<1:
          rx=1
          ry+=1
          down=True
        if rx>4:
          rx=4
          ry+=1
          down=True

        if ry<=4 and m[rx][ry]!=0:
          rx=lrx
          ry=lry
          tryagain=True

      if ry>4:
        done=True
        continue

      if down:
        prev=m[lrx].get(lry-1,0) if lry>1 else 0
        if prev==2 or prev==5:
          if ry<5: m[lrx][lry]=5
        else:
          m[lrx][lry]=2
        m[rx][ry]=3
      else:
        m[rx][ry]=1

      if ry>4: done=True

    m[rx][4]=6

    return m

# --------------------------------
# Game loop (Thumby Color)
# --------------------------------

game=pico8()

# Set up state tables (need to reference bound methods)
game.title_state={
  "name":"title",
  "init":game.init_title,
  "update":game.update_title,
  "draw":game.draw_title
}
game.play_state={
  "name":"play",
  "init":game.init_play,
  "update":game.update_play,
  "draw":game.draw_play
}

game.state={}
game.next_state={}
game.change_state=False
game.screenshake=0
game.screenshake_pwr=0
game.camx=0
game.camy=0
game.entities=[]
game.items=[]
game.new_items=[]
game.particles=[]
game.level=1

game._init()

_gc_n=0

while loop:
  if engine.tick():
    game._update()
    game._draw()
    if button.MENU.is_just_pressed:
      loop=menu()
    _gc_n+=1
    if _gc_n>=3:
      gc.collect()
      _gc_n=0
