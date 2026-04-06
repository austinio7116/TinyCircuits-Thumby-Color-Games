#Thumby Color functions for PICO-8 converted code
import engine_main
import engine
import engine_draw
import engine_audio
import engine_io as button
import engine_save
from engine_resources import TextureResource, WaveSoundResource, FontResource
from math import cos as m_cos, sin as m_sin, atan2 as m_atan2, floor as flr, sqrt, pi, ceil
import random
from time import ticks_ms, ticks_us, ticks_diff, time as time_time
from ubinascii import hexlify
import sys
import gc
gc.enable()
gc.collect()
sys.stdout.write(f"{gc.threshold()=}\n")
gc.threshold(32768) #65536)
random.seed(ticks_ms())
engine.freq(250_000_000) #(150_000_000)

import time
def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = ticks_us()
        result = f(*args, **kwargs)
        delta = ticks_diff(ticks_us(), t)
        sys.stdout.write('Function {} Time = {:6.3f}ms\n'.format(myname, delta/1000))
        return result
    return new_func

def sin(a): #expects values from 0-1
    return -m_sin(a*(pi+pi))
  
def cos(a): #expects values from 0-1
    return m_cos(a*(pi+pi))

#ATAN2(DX, DY)
#Converts DX, DY into an angle from 0..1
#As with cos/sin, angle is taken to run anticlockwise in screenspace.
#eg ATAN(0, -1) returns 0.25
def atan2(x, y): #a bit hacky, may need reworking!
  if x==y==0: #special case, see https://pico-8.fandom.com/wiki/Atan2
    return 0.25
  return (1.0-m_atan2(y,x)/(2*pi)) % 1 #from https://www.lexaloffle.com/bbs/?tid=49048

#SFX(N, [CHANNEL], [OFFSET], [LENGTH]) https://www.lexaloffle.com/dl/docs/pico-8_manual.html#SFX
def sfx(n, channel=0, offset=0, length=1):
  if n>=len(sounds):
    sys.stdout.write(f"sfx missing {n=}\n")
    return
  if sounds[n]==None:
    #sys.stdout.write(f"sfx not loaded {n=}\n")
    return
  if channel>=3: channel=2
  channels[channel]=engine_audio.play(sounds[n], channel, False)
  return

#MUSIC(N, [FADE_LEN], [CHANNEL_MASK])
#ToDo: Handle fading
# And perhaps channel_mask - always plays on channel 3 for now and any sfx set to 3 use 2 instead!
def music(n=0, fade_len=None, channel_mask=None):
  if n==-1:
    engine_audio.stop(3)
  elif n>=len(tunes):
    sys.stdout.write(f"music missing {n=}\n")
  elif tunes[n]==None:
    sys.stdout.write(f"music not loaded {n=}\n")
  else:
    channels[3]=engine_audio.play(tunes[n],3,True)
    #ch.gain=1.0 #Doesn't make it noticeably louder than default!

channels=[None]*4
stats={46:0, 47:1, 48:2, 49:3} #PICO-8 Audio Channels to check for which SFX is playing by channel
def stat(n):
    if n in stats:
        if channels[stats[n]]!=None:
            return channels[stats[n]].source
    return None

@micropython.viper
def getSpritePixel(x:int,y:int)->int:
  ss:ptr8=ptr8(sprite_sheet.data)
  addr:int=(x>>1)|(y<<6)
  if x & 1:
    #return int(ss[addr]>>4)
    return int(ss[addr] & 0b00001111)
  else:
    #return int(ss[addr] & 0b00001111)
    return int(ss[addr]>>4)
#SGET(X, Y)
#SSET(X, Y, [COL])
#Get or set the colour (COL) of a sprite sheet pixel.
#When X and Y are out of bounds, SGET returns 0. A custom value can be specified with:
#POKE(0x5f36, 0x10)
#POKE(0x5f59, NEWVAL)
def sget(x,y):
  i=0
  if 0<=x<128 and 0<=y<128:
    i=getSpritePixel(int(x), int(y))
  return i

def sset(x,y,col=None): #ToDo: implement sset in sprites list and sprite_sheet (in case using sspr)?
  global last_col, sprite_sheet, sprites
  if col==None:
    col=last_col
  if 0<=x<128 and 0<=y<128:
    x=int(x)
    y=int(y)
    addr=(x>>1)+(y<<6)
    b=sprite_sheet.data[addr]
    n=x//8+(y//8)*16
    offset=(x//2) % 4+(y % 8)*4
    c=sprites[n].data[offset]
    if (x % 2)==1:
      #sprite_sheet.data[addr]=(b & 0b00001111) | (col % 16)<<4
      #sprites[n].data[offset]=(c & 0b00001111) | (col % 16)<<4
      sprite_sheet.data[addr]=(b & 0b11110000) | (col % 16)     
      sprites[n].data[offset]=(c & 0b11110000) | (col % 16)
    else:
      #sprite_sheet.data[addr]=(b & 0b11110000) | (col % 16)     
      #sprites[n].data[offset]=(c & 0b11110000) | (col % 16)     
      sprite_sheet.data[addr]=(b & 0b00001111) | (col % 16)<<4
      sprites[n].data[offset]=(c & 0b00001111) | (col % 16)<<4
    last_col=col
  #sys.stdout.write(f"sset {x=}, {y=}, {col=} {n=}, {offset=} {addr=} {x%2} {sprite_sheet.data[addr]=} before={b}\n")
#Draw sprite N (0..255) at position X,Y
#SPR(N, X, Y, [W, H], [FLIP_X], [FLIP_Y])
@micropython.native
def spr(n, x, y, w=1, h=1, flip_x=False, flip_y=False):    
  if 0<=n<len(sprites):
    x=x-cam_x;y=y-cam_y
    if w==h==1 and not(flip_x or flip_y):
      engine_draw.blit(sprites[int(n)], int(x), int(y), colours[trans_index], 1)
      return
    if flip_x or flip_y:
      sspr((int(n) % 16)*8, (int(n)//16)*8, w*8, h*8, x, y, None, None, flip_x, flip_y)
      return
    b=0
    while b<h:
      a=0
      while a<w:
        engine_draw.blit(sprites[int(n)+a+(b<<4)], int(x)+(a<<3), int(y)+(b<<3), colours[trans_index], 1)
        a+=1
      b+=1

@micropython.viper
def sspr_noscale(sx:int, sy:int, sw:int, sh:int, dx:int, dy:int): # -> int: #special case no scaling, no flipping
  addr:int=(sx>>1)+(sy<<6) #sx//2+sy*64
  #addr:int=sx//2+sy*64
  offset:int=sx%2
  #count:int=0
  y:int=0
  while y<sh:
    x:int=0
    while x<sw:
      #if int(offset) & (int(x) % int(2)):
      if (offset + x) % 2:
        pixels:int= int(sprite_sheet.data[addr+((offset+x)>>1)+(y<<6)]) #had addr+1
        #pixel:int=(pixels >> 4)
        pixel:int=pixels & 0b1111
      else:
        pixels:int= int(sprite_sheet.data[addr+((offset+x)>>1)+(y<<6)])
        #pixel:int=pixels & 0b1111
        pixel:int=(pixels >> 4)
      if pixel!=int(trans_index): #ToDo: check which colours are considered transparent. Implement PALT
        engine_draw.pixel(colours[pixel],dx+x,dy+y,1) #This works for pal changes
        #count+=1
      x+=1
    y+=1
  #return count

#SSPR(SX, SY, SW, SH, DX, DY, [DW, DH], [FLIP_X], [FLIP_Y]]
#Stretch a rectangle of the sprite sheet (sx, sy, sw, sh) to a destination rectangle on the screen (dx, dy, dw, dh). In both cases, the x and y values are coordinates (in pixels) of the rectangle's top left corner, with a width of w, h.
#Colour 0 drawn as transparent by default (see PALT())
#dw, dh defaults to sw, sh
#When FLIP_X is TRUE, flip horizontally.
#When FLIP_Y is TRUE, flip vertically.
#Uses:
#sspr(32-(self.hp*8),0,8,8,self.x,self.y,self.sw,self.sh,self.fx,self.fy)
#sspr(61,96,67,32,lx,96)
def sspr(sx, sy, sw, sh, dx, dy, dw=None, dh=None, flip_x=False, flip_y=False):
  if dw==dh==None and flip_x==flip_y==False and sw==8 and sh==8 and sx//8==sx/8 and sy//8==sy/8:
    #n=sx//8+sy*2
    n=(sx>>3)+(sy<<1)
    #sys.stdout.write(f"noscale sspr spr({n}, {int(dx)}, {int(dy)})\n")
    spr(n,int(dx),int(dy))
    return
  sx=int(sx)
  sy=int(sy)
  addr=(sx>>1)+(sy<<6) #sx//2+sy*64
  offset=sx%2
  n=sx//8+sy*2
  if dw==dh==None and flip_x==flip_y==False:
    #Something wrong with this, seems to do one pixel too much in x (or starts 1 pixel in?) 
    #sys.stdout.write(f"noscale sspr {n=} {addr=}, {offset=}, {sx=}, {sy=}, {sw=}, {sh=}, {dx=}, {dy=}\n")
    #count=
    sspr_noscale(sx, sy, sw, sh, int(dx), int(dy)) #optimisation for no scaling/flipping 27fps (was 8fps)
    #sys.stdout.write(f"  {count=}\n")
    '''
    regs[0]=sx
    regs[1]=sy
    regs[2]=sw
    regs[3]=sh
    regs[4]=dx
    regs[5]=dy
    sspr_asm(regs, sprite_sheet.data) #needs colours array too
    '''
    return
  addr=(sx>>1)+(sy<<6) #sx//2+sy*64
  offset=sx%2
  if dw==None: dw=sw
  if dh==None: dh=sh
  d_dx=dw/sw
  d_dy=dh/sh
  s_dx=1/d_dx
  s_dy=1/d_dy
  if d_dx>s_dx:
    d_dx=1
  else:
    s_dx=1
  if d_dy>s_dy:
    d_dy=1
  else:
    s_dy=1
  start_a=start_b=0
  if flip_x: start_a=sw-d_dx;d_dx=-d_dx
  if flip_y: start_b=sh-d_dy;d_dy=-d_dy
  y=0;b=start_b
  while y<sh:
    x=0;a=start_a
    while x<sw:
      if (offset + int(x))%2:
        pixels= sprite_sheet.data[addr+((offset+int(x))>>1)+(int(y)<<6)]
        #pixel=(pixels >> 4)
        pixel=pixels & 0b1111
      else:
        pixels= sprite_sheet.data[addr+((offset+int(x))>>1)+(int(y)<<6)]
        #pixel=pixels & 0b1111
        pixel=(pixels >> 4)
      if pixel!=trans_index: #ToDo: check which colours are considered transparent. Implement PALT
        #engine_draw.pixel(colours[pixel],dx+int(a),dy+int(b),1)
        engine_draw.pixel(colours[pixel],int(a+dx),int(b+dy),1)
      x+=s_dx;a+=d_dx
    y+=s_dy;b+=d_dy

#0=Left, 1=Right, 2=Up, 3=Down, 4=B, 5=A
buttons=[{0:button.LEFT, 1:button.RIGHT, 2:button.UP, 3:button.DOWN, 4:button.B, 5:button.A},
         {0:button.LB, 1:False, 2:button.LB, 3:False, 4:False, 5:button.LB}, #LB presses Left and Up and A
         {0:False, 1:button.RB, 2:button.RB, 3:False, 4:False, 5:button.RB}] #RB presses Right and Up and A
def btn(id=None, player=0):
  if id==None:
    bits=button.LEFT.is_pressed
    bits+=2*button.RIGHT.is_pressed
    bits+=4*button.UP.is_pressed 
    bits+=8*button.DOWN.is_pressed
    bits+=16*button.B.is_pressed
    bits+=32*button.A.is_pressed
    return bits
  if id in buttons[0]:
    return (buttons[0][id].is_pressed or
            (buttons[1][id]!=False and buttons[1][id].is_pressed) or
            (buttons[2][id]!=False and buttons[2][id].is_pressed)) #allow shoulder buttons for Left and Right
  return False

def btnp(id=None, player=0):
  if id==None:
    bits=button.LEFT.is_just_pressed
    bits+=2*button.RIGHT.is_just_pressed
    bits+=4*button.UP.is_just_pressed 
    bits+=8*button.DOWN.is_just_pressed
    bits+=16*button.B.is_just_pressed
    bits+=32*button.A.is_just_pressed
    return bits
  if id in buttons[player]:
    return buttons[player][id].is_just_pressed
  return False

#RND(X)
#Returns a random number n, where 0 <= n < x
#If you want an integer, use flr(rnd(x)). If x is an array-style table, return a random element between table[1] and table[#table].
def rnd(n):
  if type(n) is int or type(n) is float:
      return random.uniform(0, n)
  if type(n) is list:
      i=random.randrange(1,len(n))
      return n[i]
  else:
      sys.stdout.write(f"Error in rnd, unhandled type {type(n)}, should be int, float or list\n")
  #return random.random()*n

#SRAND(X)
#Sets the random number seed. The seed is automatically randomized on cart startup.
def srand(n):
  random.seed(int(n))

#Could probably be a named tuple isntead of a class? Assuming I still need it!
#from collections import namedtuple
#ang_rng = namedtuple('ANG_RNG', ['ang', 'rng'])
class ANG_RNG():
    def __init__(self, angle, range):
        self.ang=angle
        self.rng=range

#SUB(STR, POS0, [POS1])
#Grab a substring from string str, from pos0 up to and including pos1.
#When POS1 is not specified, the remainder of the string is returned.
#When POS1 is specified, but not a number, a single character at POS0 is returned.
#S = "THE QUICK BROWN FOX"
#PRINT(SUB(S,5,9))    --> "QUICK"
#PRINT(SUB(S,5))      --> "QUICK BROWN FOX"
#PRINT(SUB(S,5,TRUE)) --> "Q"
def sub(s, pos0, pos1=None):
  result=None
  if pos1==None:
    result=s[pos0-1:]
  elif pos0==pos1 or (not (pos1 is int or pos1 is float)):
    result=s[pos0-1]
  else:
    result=s[pos0-1:pos1]
  #sys.stdout.write(f"sub {pos0=}, {pos1=} {result=}\n")
  return result

colours=[ #PICO-8 16 colour palette converted to R5G6B5 using https://rgbcolorpicker.com/565
  0x0000, #0  000000 black
  0x216a, #1  1D2B53 dark-blue
  0x792a, #2  7E2553 dark-purple
  0x042a, #3  008751 dark-green
  0xaa87, #4  AB5236 brown
  0x62aa, #5  5F574F dark-grey
  0xc618, #6  C2C3C7 light-grey
  0xff9c, #7  FFF1E8 white
  0xf809, #8  FF004D red
  0xfd00, #9  FFA300 orange
  0xff45, #10 FFEC27 yellow
  0x0707, #11 00E436 green
  0x2d7f, #12 29ADFF blue
  0x83b3, #13 83769C lavender
  0xfbb4, #14 FF77A8 pink
  0xfe55  #15 FFCCAA light-peach
  ]

def cls(col=None):
  if col==None: col=0
  engine_draw.clear(colours[int(col) % 16])
  
#PAL(C0, C1, [P]) https://www.lexaloffle.com/dl/docs/pico-8_manual.html#PAL
#PAL() swaps colour c0 for c1 for one of three palette re-mappings (p defaults to 0):   
def pal(c0=None, c1=None, p=None): #Probably can't make it do screen wide changes quickly when p=1
  global palettes, colours, trans_index
  if c0==None and c1==None and p==None: #pal()
    reset_palette(palettes[0]) #This resets OK for doing pal changes later and affecting blitted sprites
    #ignore other palettes for now for speed
    #reset_palette(palettes[1]) #palettes[1]=default_palette[:]
    #reset_palette(palettes[2]) #palettes[2]=default_palette[:]
    reset_colours(default_palette)
    trans_index=0
    #trans_colour=0x0000
    #Needs to reset transparencies too
    return
  if 0<=c0<=2 and c1==None and p==None: #pal(p)
    reset_palette(palettes[c0]) #palettes[c0]=default_palette[:]
    reset_colours(default_palette)
    return
  if p==None: p=0
  if type(c0) is int and type(c1) is int: #pal(c0, c1)
    c0=c0 % 16; c1=c1 % 16
    a=palettes[p][2*c1]
    b=palettes[p][2*c1+1]
    #tmp=b*256+a
    tmp=(b<<8) | a
    palettes[p][2*c0]=a; palettes[p][2*c0+1]=b
    colours[c0]=tmp
    
    #if p==1: remap visible screen
  #need to cope with pal(table, [p])

def reset_colours(pal_bytearray):
  for i in range(0,len(pal_bytearray)//2):
    a=pal_bytearray[2*i]
    b=pal_bytearray[2*i+1]
    #tmp=b*256+a
    tmp=(b<<8) | a
    colours[i]=tmp

def reset_palette(pal_bytearray):
  for i in range(0,len(pal_bytearray)//2):
    a=default_palette[2*i]
    b=default_palette[2*i+1]
    pal_bytearray[2*i]=a
    pal_bytearray[2*i+1]=b

trans_index=0
#trans_colour=0x0000
#PALT(C, [T])
#Set transparency for colour index to T (boolean) Transparency is observed by SPR(), SSPR(), MAP() AND TLINE()
#PALT() resets to default: all colours opaque except colour 0
#When C is the only parameter, it is treated as a bitfield used to set all 16 values. For example: to set colours 0 and 1 as transparent
#PALT(0B1100000000000000)
def palt(c=None, t=None): #Only partially works, sets one colour index to be transparent via trans_index
  global trans_index #, trans_colour
  if c==None and t==None:
    trans_index=0
    #trans_colour=0x0000
    return
  if t==None:
    return #ToDo: read bitfield to set transparencies. How to decide which to use, since can have only one for engine_draw.blit?
  if t==True:
    c=c % 16
    trans_index=c
    #tmp=palettes[0][2*c:2*c+2]
    #tmp=int.from_bytes(tmp, 'big').to_bytes(len(tmp), 'little')
    #tmp2="0x"+hexlify(tmp).decode()
    #trans_colour=int(tmp2, 16)

#about as fast as drawing the pixel using engine_draw.pixel
@micropython.viper
def getPixel(x:int,y:int)->int:
  fb:ptr16=ptr16(engine_draw.front_fb_data())
  addr:int=x|(y<<7)
  return int(fb[addr])

#fastest so far, but still slow!
def pget(x,y):
  pixel=getPixel(int(x-cam_x), int(y-cam_y))
  i=0
  if pixel in colours:
      i=colours.index(pixel)
  return i, pixel

#PSET(X, Y, [COL])
#Sets the pixel at x, y to colour index COL (0..15).
#When COL is not specified, the current draw colour is used.
def pset(x,y,col=None):
  global last_col
  if col==None:
    col=last_col
  engine_draw.pixel(colours[col],x,y,1)
  last_col=col

#Returns the middle value of parameters
#eg MID(7,5,10) returns 7 
@micropython.viper
def mid(x,y,z):
    if x<=y<=z or z<=y<=x:
        return y
    if y<=x<=z or z<=x<=y:
        return x
    if y<=z<=x or x<=z<=y:
        return z

def color(n):
  global last_col
  last_col=n
  
def print(text, x=None, y=None, col=None):
  global last_col, print_last_x, print_last_y, cam_x, cam_y
  if col==None:col=last_col
  if x==None:x=print_last_x
  if y==None:y=print_last_y
  if not isinstance(text, str): #Try to prevent Hard Fault if not a string 
    text=str(text)
  #Optimisation: only draw if character to print will be on screen
  if -8<=x-cam_x<135 and -6<=y-cam_y<135:
      font=p8scii
      if text.startswith("\^w\^t"): #Handle double width and height control codes using X2 font
          font=p8sciiX2
          text=text[6:]
      engine_draw.text(font, text, colours[int(col) % 16], x-cam_x, y-cam_y, 0, 0, 1)
  last_col=col
  print_last_x=x #ToDo: return next x print position? https://NerdyTeachers.com/PICO-8/Guide/PRINT
  print_last_y=y+6
'''
def print(text, x=None, y=None, col=None):
  global last_col, print_last_x, print_last_y
  if col==None:col=last_col
  if x==None:x=print_last_x
  if y==None:y=print_last_y
  if not isinstance(text, str): #Try to prevent Hard Fault if not a string 
    text=str(text)
  engine_draw.text(p8scii, text, colours[int(col) % 16], int(x), int(y), 0, 0, 1)
  last_col=col
  print_last_x=x
  print_last_y=y+6
'''
#CARTDATA(ID) https://www.lexaloffle.com/dl/docs/pico-8_manual.html#CARTDATA
#Opens a permanent data storage slot indexed by ID that can be used to store and retrieve up to 256 bytes (64 numbers) worth of data using DSET() and DGET().
def cartdata(id):
  sys.stdout.write(f"cartdata {id}\n")
  #engine_save.set_location("save.data")
  pass

#DGET(INDEX)
#Get the number stored at INDEX (0..63)
#Use this only after you have called CARTDATA()
def dget(n):
  sys.stdout.write(f"dget {n=}\n")
  saves_dir=engine_save.saves_dir()
  if saves_dir!=None:
    try:
      val= engine_save.load(str(n))
      sys.stdout.write(f"dget {val=}\n")
      if val==None: return 0
      return val
    except:
      return 0

#DSET(INDEX, VALUE)
#Set the number stored at index (0..63)
#Use this only after you have called CARTDATA()
def dset(n,val):
  sys.stdout.write(f"dset {n=}\n")
  saves_dir=engine_save.saves_dir()
  if saves_dir!=None:
    engine_save.save(str(n),val)

#Sprite Flags
#The 8 coloured circles are sprite flags for the current sprite. These have no particular meaning, but can be accessed using the FGET() / FSET() functions. They are indexed from 0 starting from the left.
#FGET(N, [F])
#Get the value (VAL) of sprite N's flag F.
#F is the flag index 0..7.
#VAL is TRUE or FALSE.
#The initial state of flags 0..7 are settable in the sprite editor, so can be used to create custom sprite attributes. It is also possible to draw only a subset of map tiles by providing a mask in MAP().
#When F is omitted, all flags are retrieved/set as a single bitfield.
def fget(n,f=None):
  if f==None:
      return sprite_flags[n]
  return ((sprite_flags[n]>>f) & 1)==1

#FSET(N, [F], VAL)
#Set the value (VAL) of sprite N's flag F.
#F is the flag index 0..7.
#VAL is TRUE or FALSE.
#The initial state of flags 0..7 are settable in the sprite editor, so can be used to create custom sprite attributes. It is also possible to draw only a subset of map tiles by providing a mask in MAP().
#When F is omitted, all flags are retrieved/set as a single bitfield.
def fset(n, f, val):
  return 



cart_time=time_time()
#TIME()
#T()
#Returns the number of seconds elapsed since the cartridge was run.
#This is not the real-world time, but is calculated by counting the number of times
def time():
  return time_time()-cart_time

#The PICO-8 map is a 128x32 grid of 8-bit values, or 128x64 when using the shared memory. When using the map editor, the meaning of each value is taken to be an index into the sprite sheet (0..255). However, it can instead be used as a general block of data.
#MGET(X, Y)
#Get map value (VAL) at X,Y
#When X and Y are out of bounds, MGET returns 0
def mget(x,y):
  global map_data
  if 0<=x<128 and 0<=y<64:
    addr=(int(x)+int(y)*128)
    return map_data[addr]
  return 0

#MSET(X, Y, VAL)
#Set map value to (VAL) at X,Y
def mset(x,y,val):
  global map_data
  if 0<=x<128 and 0<=y<64:
    addr=(int(x)+int(y)*128)
    map_data[addr]=val

#MAP(TILE_X, TILE_Y, [SX, SY], [TILE_W, TILE_H], [LAYERS])
#Draw section of map (starting from TILE_X, TILE_Y) at screen position SX, SY (pixels).
@micropython.viper
def map(tile_x:int, tile_y:int, sx:int, sy:int, tile_w:int, tile_h:int, layers):
  global map_data, icam_x, icam_y
  #tile_x=0;tile_y=0;sx=0;sy=0;tile_w=16;tile_h=16;layers=None
  addr:int=tile_x+(tile_y<<7)
  sx-=int(icam_x)
  sy-=int(icam_y)
  y:int=sy
  #y1:int=0
  x_end=(tile_w<<3)+sx
  y_end=(tile_h<<3)+sy
  while y<y_end:
    x:int=sx
    x1:int=0
    while x<x_end:

      id:int=int(map_data[addr+x1])
      if int(layers)>0:
        if id and fget(id) & layers:
          engine_draw.blit(sprites[id], x, y, colours[trans_index], 1)
      else:
        if id>0:
          engine_draw.blit(sprites[id], x, y, colours[trans_index], 1)
      x+=8
      x1+=1
    y+=8
    addr+=128

def camera(x=0,y=0):
  global cam_x, cam_y, icam_x, icam_y  
  cam_x=x
  cam_y=y
  icam_x=int(x)
  icam_y=int(y)

#LINE(X0, Y0, [X1, Y1, [COL]])
#Draw a line from (X0, Y0) to (X1, Y1)
#If (X1, Y1) are not given, the end of the last drawn line is used.
#LINE() with no parameters means that the next call to LINE(X1, Y1) will only set the end points without drawing
def line(x0=None,y0=None,x1=None,y1=None,col=None):
  global line_last_x, line_last_y, last_col
  if col==None:
    col=last_col
  if x1==None or y1==None:
    x1=line_last_x
    y1=last_line_y
  engine_draw.pixel(colours[col],x0-cam_x,y0-cam_y,1) #Fix for bug in Thumby Color engine_draw.line
  engine_draw.line(colours[col],x0-cam_x,y0-cam_y,x1-cam_x,y1-cam_y,1)
  last_col=col
  line_last_x=x1
  line_last_y=y1

#RECTFILL(X0, Y0, X1, Y1, [COL])
#Draw a rectangle or filled rectangle with corners at (X0, Y0), (X1, Y1).
@micropython.native
def rect(x0,y0,x1,y1,col=None):
  global last_col
  if col==None:
    col=last_col
  x0=x0-cam_x;y0=y0-cam_y
  if x0+x1<0 or x0>127 or y0+y1<0 or y0>127:
    return
  engine_draw.rect(colours[col], x0-cam_x, y0-cam_y, x1-x0, y1-y0, True, 1)

#this wrapper + viper ends up being slower than leaving as normal or native!
#Mainly due to having to convert the floating point values to int, which it can't do in viper for some reason?

'''
def rectfill(x0,y0,x1,y1,col=None):
  global last_col
  if col==None:
    col=last_col
  #sys.stdout.write(f"rectfill {x0=}, {y0=}, {x1=}, {y1=}, {col=}, {cam_x\n")
  rectfill_fast(int(x0),int(y0),int(x1),int(y1),int(col))

@micropython.viper
def rectfill_fast(x0:int,y0:int,x1:int,y1:int,col:int):
  global icam_x, icam_y
  x:int=x0-int(icam_x);y:int=y0-int(icam_y)
  #Optimisation ignore if off screen
  if x+x1<0 or x>127 or y+y1<0 or y>127:
    return
  engine_draw.rect(colours[col], x, y, x1-x+1, y1-y+1, False, 1) #Have to add 1 for some reason!
'''
@micropython.native #Is this any faster? Hard to tell - need to average fps over 10 seconds or something
def rectfill(x0,y0,x1,y1,col=None):
  if col==None:
    global last_col
    col=last_col
  #Optimisation ignore if off screen
  if x0+x1<0 or x0>127 or y0+y1<0 or y0>127:
    return
  if x1==y1==1:
    engine_draw.pixel(colours[col],x0-cam_x,y0-cam_y,1)
  else:
    #engine_draw.rect(colours[int(col)], int(x0), int(y0), int(x1-x0+1), int(y1-y0+1), False, 1) #Have to +1 for some reason!
    engine_draw.rect(colours[int(col)], x0-cam_x, y0-cam_y, x1-x0+1, y1-y0+1, False, 1) #Have to +1 for some reason!

#debug max poss speed
#def rectfill(x0,y0,x1,y1,col=None):
#    pass

#CIRC(X, Y, R, [COL])
#Draw a circle  at x,y with radius r
#If r is negative, the circle is not drawn.
#When bits 0x1800.0000 are set in COL, and 0x5F34 & 2 == 2, the circle is drawn inverted.
@micropython.native
def circ(x,y,r,col=None):
  global last_col
  if col==None:
    col=last_col
  x=x-cam_x; y=y-cam_y
  #Optimisation: only draw if circle bounds are on screen
  if ((0<=x-r<=127 and 0<=y-r<=127) or
      (0<=x+r<=127 and 0<=y-r<=127) or
      (0<=x-r<=127 and 0<=y+r<=127) or
      (0<=x+r<=127 and 0<=y+r<=127)):
      engine_draw.circle(colours[col],x,y,r,True,1)
  last_col=col

@micropython.native
def circfill(x, y, r, col=None):
  global last_col
  if col==None:
    col=last_col
  x=x-cam_x; y=y-cam_y
  #Optimisation: only draw if circle bounds are on screen
  if ((0<=x-r<=127 and 0<=y-r<=127) or
      (0<=x+r<=127 and 0<=y-r<=127) or
      (0<=x-r<=127 and 0<=y+r<=127) or
      (0<=x+r<=127 and 0<=y+r<=127)):
      engine_draw.circle(colours[col % 16], x, y, r, False, 1)
  last_col=col

def menu():
  global snapshot, has_bg
  for i in range(0,4):engine_audio.stop(i)
  for bt in range(0,len(snapshot.data)):
    snapshot.data[bt]=engine_draw.front_fb_data()[bt]
  #snapshot.data=engine_draw.front_fb_data()[:]
  #engine_draw.set_background(snapshot)
  paused=True
  loop=True
  rumble(0)
  choice=0
  ink=colours[7]
  while paused:
    if engine.tick():
      engine_draw.rect(colours[0], 23, 47, 82, 34, False, 0.67)
      engine_draw.rect(ink, 24, 48, 79, 31, True, 1)
      engine_draw.text(None, ">CONTINUE"[(choice!=0):], ink, 30, 50, 1, 1, 1)
      engine_draw.text(None, ">SCREENSHOT"[(choice!=1):], ink, 30, 60, 1, 1, 1)
      engine_draw.text(None, ">RESET"[(choice!=2):], ink, 30, 70, 1, 1, 1)
      b=btnp()
      if (b & 16):b=32;choice=0
      if (b & 32):paused=False;
      if (b & 8):choice=(choice+1)%3
      if (b & 4):choice=(choice+2)%3
  loop=(choice!=2)
  if choice==1:
      #save screenshot
      try:
        f=open("bmpheader.bin", 'rb')
        header=f.read()
        f.close
        f=open("screenshot.bmp", 'wb')
        f.write(header)
        size=len(snapshot.data)
        for i in range(size-256, -1, -256): #write each horizontal scan line in reverse order (BMP format)
          tmp=snapshot.data[i:i+256]
          f.write(tmp)
        f.close
      except:
        sys.stdout.write(f"Error: saving screenshot failed. Check there's enough room on device and bmpheader.bin in folder.\n")  
  while b==32:
    if engine.tick():
      b=btn()
  lo=colours[0] % 256;hi=colours[0] //256
  for bt in range(0,len(snapshot.data),2):
    snapshot.data[bt]=lo
    snapshot.data[bt+1]=hi
  has_bg=False
  return loop

#PICO-8 helper function to return a string from whatever var is
def add_str(var): 
  if type(var) is str:
    return var
  return str(var)

#PICO-8 helper function to make range use end value and cope with floats
def rng(start,end,step=1):
  if start<=end:
    end+=step
  else:
    start+=step
    end+=step
  return range(int(start),int(end),int(step))

#PICO-8 function to replicate foreach
def foreach(iterable,fn):
  #for x in iterable:
  for x in reversed(list(iterable)): #changed this to do in reverse, so doesn't leave some behind when destroying them in Celeste!
    fn(x)

#PICO-8 function to flip framebuffer
#We're already copying the displayed screen (front_fb) to snapshot.data at end of main engine_tick loop
#This does the following:
#1. Copies back_fb to snapshot.data
#2. Updates (swaps back_fb with front_fb and clears back_fb to black)
#3. Copies snapshot.data to back_fb ready for more changes
#NB Can't access Menu using Menu button when doing flip until hands control back to engine_tick loop
#  But could probably add something inside flip function perhaps? Taking a screenshot might mess it up!
def flip(): 
  global snapshot
  now=ticks_ms()
  copy_bytearray(engine_draw.back_fb_data(),snapshot.data)
  engine_draw.update()
  copy_bytearray(snapshot.data,engine_draw.back_fb_data())
  while ticks_diff(ticks_ms(),now)<33:
    pass
'''
@micropython.viper
def copy_bytearray(source:ptr8, dest): #Would be faster copying using ptr16 or ptr32, but messes up!
  b:int=0
  while b<32768:
    dest[b]=source[b]
    b+=1
'''
#This works, and is now faster than the micropython.viper version above
def copy_bytearray(source, dest):
  #dest=bytearray(source) #Only a shallow copy
  #dest=source.copy() #Doesn't exist in micropython's bytearray
  #a=bytearray()
  #dest=a+source #Concatenation should make a copy? Nope!
  dest[:]=source[:] #this seems to be the fastest to make a new copy, but dest[]=source[:] doesn't
  #Could probably be made a little faster by doing in line rather than as a function?

#SPLIT(STR, [SEPARATOR], [CONVERT_NUMBERS])
#Split a string into a table of elements delimited by the given separator (defaults to ","). When separator is a number n, the string is split into n-character groups. When convert_numbers is true, numerical tokens are stored as numbers (defaults to true). Empty elements are stored as empty strings.
def split(st, sep=",", convert_numbers=True):
  parts=st.split(sep)
  if convert_numbers:
    for i in range(0, len(parts)):
        try:
            n=int(parts[i])
            parts[i]=n
        except:
            try:
                n=float(parts[i])
                parts[i]=n
            except:
                pass
  return parts

#https://NerdyTeachers.com/PICO-8/Guide/UNPACK
#UNPACK(TABLE, [FIRST], [LAST])
#TABLE  a numbered table of elements (list)
#FIRST  (optional) the first number of the table to return
#LAST   (optional) the last number of the table to return
def unpack(table, first=None, last=None):
    if first==None: first=0
    if last==None: last=len(table)
    return tuple(table[first:last])

def tonum(n):
  result=None
  try:
    result=float(n)
  except:
    try:
      result=int(n)
    except:
      pass
  return result
      
#Bitwise operations
def band(x, y):
  if type(x) is float: x=int(x)
  if type(y) is float: y=int(y)
  if type(x) is int and type(y) is int:
    return x & y
  else:
    return 0

def bor(x, y):
  if type(x) is float: x=int(x)
  if type(y) is float: y=int(y)
  if type(x) is int and type(y) is int:
    return x | y
  else:
    return 0

def bxor(x, y):
  if type(x) is float: x=int(x)
  if type(y) is float: y=int(y)
  if type(x) is int and type(y) is int:
    return x ^ y
  else:
    return 0

def bnot(x):
  if type(x) is float: x=int(x)
  if type(x) is int:
    return ~x
  else:
    return 0

#COUNT(TBL, [VAL])
#Returns the length of table t (same as #TBL) When VAL is given, returns the number of instances of VAL in that table
#NB Only counts numeric keys and val is value not the key
def count(tbl, val=None):
    if val==None:
        return len(tbl) #May want len(tbl.keys())?
    else:
        sys.stdout.write(f"WARNING Ignoring {val=} in count")
        pass

#PAIRS(TBL) https://www.lexaloffle.com/dl/docs/pico-8_manual.html#PAIRS
#Used in FOR loops to iterate over table TBL, providing both the key and value for each item. Unlike ALL(), PAIRS() iterates over every item regardless of indexing scheme. Order is not guaranteed.
def pairs(tbl): #Not tested yet!
    return k,v in tbl

#IPAIRS(TBL) https://pico-8.fandom.com/wiki/IPairs
#This iterator produces only the values in the table which are considered part of its indexed sequence. It will not produce values associated with non-numeric keys, and it will not produce values for any indices greater than #table.
#It is guaranteed that the indices will be produced in ascending order.
def ipairs(tbl): #Not tested yet!
    indexed_only={}
    for i in range(0, len(tbl)):
        if i in tbl:
            indexed_only[i]=tbl[i]
    return k, v in indexed_only
        
    
#CLIP(X, Y, W, H, [CLIP_PREVIOUS])
#Sets the clipping rectangle in pixels. All drawing operations will be clipped to the rectangle at x, y with a width and height of w,h.
#CLIP() to reset.
#When CLIP_PREVIOUS is true, clip the new clipping region by the old one.
def clip(x=None,y=None,w=None,h=None,clip_previous=False):
  #sys.stdout.write(f"WARNING Ignoring clip({x},{y},{w},{h},{clip_previous}), clip function still needs to be written!\n")
  pass

#Custom Rumble function for Thumby Color
#Ideally would have a duration, so doesn't rumble too long
def rumble(amount):
  amount=amount/30
  if amount<0: amount=0
  if amount>0.5: amount=0.5
  button.rumble(amount)
#End of Thumby specifics
  
#Init and game loop
#More Thumby Boilerplate code
print_last_x=print_last_y=0
cam_x=cam_y=0
icam_x=icam_y=0
random.seed(ticks_ms())
p8scii=FontResource("P8SCII.BMP")
last_col=colours[0]
#Load sprite sheet
sprite_sheet=TextureResource("sprites.bmp", True)
sprites=[None]*256
default_palette=sprite_sheet.colors[:]
#default_palette=get_palette(sprite_sheet)
palettes=[]
palettes.append(default_palette[:]) #need this for changing draw palette=palettes[0]
palettes.append(default_palette[:]) #not sure how useful palettes[1] and [2] are
palettes.append(default_palette[:])
reset_colours(default_palette)
sprite_sheet.colors=palettes[0]
for i in range(0,256):
  sprites[i]=TextureResource(8,8,0,4)
  for y in range(0,8):
    for x in range(0,4):
      sprites[i].data[4*y+x]=sprite_sheet.data[(i%16)*4+(i//16)*512+64*y+x]
      sprites[i].colors=palettes[0]

#Loading screen
cls(0)
print("delunky",48,6,9)
print("delunky",47,5,4)
print("pico-8 version by",30,36,6)
print("johan peitz (@johanpeitz)",14,46,6)
print("demakejam 2018",36,56,6)
print("unofficial thumby color port",6,76,12)
print("loading...",44,120,7)
engine_draw.update()

#Load sprite flags
sprite_flags=bytearray(256)
f=open("sprite_flags.bin", 'rb')
f.readinto(sprite_flags)
f.close

#Load map data
map_data=bytearray(8192)
f=open("map.bin", 'rb')
f.readinto(map_data)
f.close
sys.stdout.write(f"{map_data[0]=}\n")

#Copy 2nd half of sprite data to 2nd half of map data
for i in range(0, 4096):
    a=sprite_sheet.data[4096+i]
    map_data[4096+i]=((a >> 4) & 0b00001111) | ((a<<4) & 0b11110000)
#Load SFX
sounds=[None]*64
for i in range(0,len(sounds)):
  try:
    sounds[i]=WaveSoundResource("sfx"+str(i)+".wav", False)
  except:
    sounds[i]=None

#Load Music
tunes=[None]*41
for i in range(0,len(tunes)):
  try:
    tunes[i]=WaveSoundResource("music"+str(i)+".wav", False)
  except:
    tunes[i]=None
#engine_audio.set_volume(1.0) #Doesn't make it noticeably louder than default!

#test sub function for sunstrings
#S = "THE QUICK BROWN FOX"
#sys.stdout.write(sub(S,5,9)+"\n")    #"QUICK"
#sys.stdout.write(sub(S,5)+"\n")      #"QUICK BROWN FOX"
#sys.stdout.write(sub(S,5,True)+"\n") #"Q"

engine.fps_limit(30)
#engine_save.set_location("save.data")
snapshot=TextureResource(128,128,colours[0])
engine_draw.set_background(snapshot)
has_bg=False
loop=True
cls(0)
engine_draw.update()
