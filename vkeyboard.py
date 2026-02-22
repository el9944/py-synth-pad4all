import time
import tkinter as tk
import math as math
from PIL import ImageTk, Image
from rtmidi.midiutil import open_midioutput
import rtmidi
from config import FILES,LOOPMIDINAME

mo = None
bpm = 140  # Initialisation du BPM

def up():
    global bpm
    if (bpm<245):
        bpm += 5
    bpm_label_value.config(text=str(bpm))  
    print(([153,42,1],1))
    if mo:
        mo.send_message([153,42,1])
def down():
    global bpm 
    if (bpm>5):
        bpm -= 5
    bpm_label_value.config(text=str(bpm))
    print(([153,41,1],1))
    if mo:
        mo.send_message([153,41,1])

def start_metronome():
    print(([153,40,1],0))
    if mo:
        mo.send_message([153,40,1])   


root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
#screen_width = 810
#screen_height = 440

pimage=Image.open(FILES[6])
pimage = pimage.resize((math.ceil(screen_width/5),math.ceil(screen_width/5)))
tk_pimage = ImageTk.PhotoImage(pimage)
pag=Image.open(FILES[5])
tk_pag = ImageTk.PhotoImage(pag)
gap=Image.open(FILES[2])
tk_gap = ImageTk.PhotoImage(gap)


root.geometry(f'{screen_width}x{screen_height}')

listenote=[]
octact=0
MP=1
last_switch_time = 0
debounce_delay = 1  # 100 ms
fs=1
# buttonplus = Button(23)
# buttonmoins = Button(24)
# interrupteur = Button(16)

def zoneclick(event):
    print("Coordonnées du click : " + str(event.x)+"," + str(event.y))
    trace(screen_width/16,[screen_width/16,screen_height/7],[event.x,event.y])
    for i in range (len(testhexa(screen_width/16,[screen_width/16,screen_height/7],[1,1]))):
        x=cut(screen_width/16,[screen_width/16,screen_height/7],[event.x,event.y],i)
        if mo:
            mo.send_message(x[0])
        time.sleep(0.001)


def ishexagone(x,y,c,xt,yt):
    global MP
    #x et y sont les coordonnées du centre de l'hexagone, c est la valeur des cotés, xt et yt sont les valeurs que l'on veut tester (dans l'héxa ou non)
    if (abs(x-xt)<=math.ceil((math.sqrt(3)/2)*c)+MP*(screen_width/16)/4 and abs(y-yt)<=math.ceil(0.5*c)) or (abs(y-yt)>=c/2 and abs(abs(y-yt)-c/2)+(abs(x-xt)*((c/2)/(math.sqrt(3)*c/2)))<=c/2+MP*(screen_width/16)/4):
        return True
    else:
        return False



def liste(c,hexai):
    allhexa=[]
    hexa=[0,0]
    d=(math.sqrt(3)/2)*c
    for i in range (24) :
        if i<4 :
            hexa[0]=hexai[0]+round(d*2)*i
            hexa[1]=hexai[1]
        if i>=4 and i<10 :
            hexa[0]=hexai[0]+round(d*2)*(i-4)+round(d)
            hexa[1]=hexai[1]+round(c*(3/2))
        if i>=10 and i<17 :
            hexa[0]=hexai[0]+round(d*2)*(i-10)+round(d*2)
            hexa[1]=hexai[1]+c*3
        if i>=17 and i<23 :
            hexa[0]=hexai[0]+round(d*2)*(i-17)+round(d*5)
            hexa[1]=hexai[1]+round(c*(9/2))
        if i==23 :
            hexa[0]=hexai[0]+round(d*12)
            hexa[1]=hexai[1]+c*6
        allhexa.append(hexa.copy())
    return(allhexa)




def testhexa(c,hexai,co):
    global listenote
    global octact
    allhexa=liste(c,hexai)
    t=[]
    a=[]
    dat=[]
    note=["sol0","si0","sol1","si1","sol#0","do1","mi1","sol#1","do2","mi2","fa0","la0","do#1","fa1","la1","do#2","ré2","fa#0","la#0","ré1","fa#1","la#1","ré#2","ré#1"]
    num=[55,59,67,71,56,60,64,68,72,76,53,57,61,65,69,73,74,54,58,62,66,70,75,63]
    if co ==[1,1] :
        for d in range (len(listenote)) :
            dat.append([([128,listenote[d],0],0),60,note])
        if (len(listenote)==0):
            return ([[([128,0,0],0),69,note]])
        else:
            return (dat)
    
    elif co ==[0,0] :
        return ([[([128,0,0],0),69,note]])
    else :
        listenote=[]
        for j in range (len(allhexa)):
            if ishexagone(allhexa[j][0],allhexa[j][1],c,co[0],co[1])==True:
                t.append(num[j]+octact*12)
                a.append(j)

            if j==23 and len(t)==0:
                #print("le point n'est pas sur le clavier")
                return ([[([128,0,0],0),69,note]])
        if len(t)>0 and j==23:
            for b in range (len(a)) :
                dat.append([([144,t[b],0],0),a[b],note])
            listenote=t
            return(dat)


canvas = tk.Canvas(root,width=screen_width, height=screen_height, background="gray11")
canvas.pack()
frame1=tk.Frame(root, width=math.ceil(screen_width/6.75), height=math.ceil(screen_height/2.58823529412-math.ceil(screen_height/(44/3))))
frame2=tk.Frame(root, width=math.ceil(screen_height/(44/3)), height=math.ceil(screen_height/(44/3)))


def text(xi,yi,t):

    canvas.create_text(xi+8, yi+7, text=t, fill="black", font=(f'Helvetica {math.ceil(screen_width/54)} bold'))
    #T.place(x=xi,y=yi)


def chatot(x):
    global octact
    if  x==1 and octact<2 :
        octact = octact + 1
    if x==0 and octact>-2 :
        octact = octact - 1






def cut(c,hexai,co,long):
    if (testhexa(c,hexai,co)[0][1]!=69):
        print(testhexa(c,hexai,co)[long][0])
        return(testhexa(c,hexai,co)[long][0])

def trace(c,hexai,co):
    global MP
    allhexa=liste(c,hexai)
    if MP == 1 :
        Coup=["#8271D4","#CA72D9","#8271D4","#CA72D9","#597EE3","#78C4FD","#43BC86","#597EE3","#78C4FD","#43BC86","#FFEC72","#FFB62D","#54D7D5","#FFEC72","#FFB62D","#54D7D5","#F37F79","#F0D331","#F98D0E","#F37F79","#F0D331","#F98D0E","#FA745B","#FA745B"]
    if MP == 0 :
        Coup=["#5502B0","#A02CC7","#5502B0","#A02CC7","#3168A6","#148BAD","#02C472","#3168A6","#148BAD","#02C472","#FFDF00","#FFA229","#25BAB3","#FFDF00","#FFA229","#25BAB3","#DC1701","#FBC200","#FC6A2C","#DC1701","#FBC200","#FC6A2C","#C40000","#C40000"]
    canvas.delete('all')
    for h in range (24):
            pt=[]
            for z in range (6):
                pt.append(allhexa[h][0]+c*math.sin(math.pi/3*z))
                pt.append(allhexa[h][1]+c*math.cos(math.pi/3*z))
            canvas.create_polygon(pt, outline = "white", fill = Coup[h], width = 2)
            text(allhexa[h][0]-10,allhexa[h][1]-5,testhexa(c,hexai,co)[0][2][h])

            for k in range (len(testhexa(c,hexai,co))) :
                if testhexa(c,hexai,co)[k][1]==h:
                    canvas.create_polygon(pt, outline = "white", fill = "antique white", width = 2)
                    text(allhexa[h][0]-10,allhexa[h][1]-5,testhexa(c,hexai,co)[0][2][h])
    canvas.create_image(screen_width-math.ceil(tk_pimage.width()*0.55),screen_height-math.ceil(tk_pimage.height()*0.35), image=tk_pimage)
    canvas.create_window(screen_width-math.ceil(screen_width/6.75),0,window=frame1, anchor="nw", width=math.ceil(screen_width/6.75), height=math.ceil(screen_height/2.58823529412-math.ceil(screen_height/(44/3))))
    canvas.create_window(0,math.ceil(screen_height-math.ceil(screen_height/(44/3))),window=frame2, anchor="nw", width=math.ceil(screen_height/(44/3)), height=math.ceil(screen_height/(44/3)))
    #print(testhexa(c,hexai,co))
trace(screen_width/16,[screen_width/16,screen_height/7],[0,0])

def monopoly(y):
    global MP, last_switch_time
    now = time.time()
    if now - last_switch_time > debounce_delay:
        if y == 1 and MP == 0:
            MP = 1
            trace(screen_width/16, [screen_width/16, screen_height/7], [0, 0])
        elif y == 0 and MP == 1:
            MP = 0
            trace(screen_width/16, [screen_width/16, screen_height/7], [0, 0])
        last_switch_time = now


# buttonplus.when_pressed = partial(chatot, 1)
# buttonmoins.when_pressed = partial(chatot, 0)
# interrupteur.when_pressed = partial(monopoly, 0)
# interrupteur.when_released = partial(monopoly, 1)

def relache(event):
    #print("Button Released")
    trace(screen_width/16,[screen_width/16,screen_height/7],[1,1])
    for i in range (len(testhexa(screen_width/16,[screen_width/16,screen_height/7],[1,1]))):
        x=cut(screen_width/16,[screen_width/16,screen_height/7],[1,1],i)
        if mo:
            mo.send_message(x[0])
        time.sleep(0.001)
canvas.bind('<ButtonRelease-1>', relache)


running = tk.BooleanVar(value=False)
def metro():
    global screen_height
    global screen_width
    global bpm_label_value

    #Étiquette pour le tempo
    bpm_label = tk.Label(frame1, text="Tempo (BPM):")
    bpm_label.place(x=0, y=0, height=math.ceil(screen_height/22), width= math.ceil(screen_width/6.75))
    # Étiquette qui affiche le BPM actuel
    bpm_label_value = tk.Label(frame1, text=str(bpm))
    bpm_label_value.place(x=0, y=math.ceil(screen_height/22), height=math.ceil(screen_height/22), width= math.ceil(screen_width/6.75))
    # Bouton de démarrage/arrêt
    start_button = tk.Button(frame1, text="ON/OFF", command=start_metronome)
    start_button.place(x=0, y=math.ceil(screen_height/(44/9)), height=math.ceil(screen_height/8.8), width= math.ceil(screen_width/6.75))
    # Bouton pour augmenter le BPM
    up_button = tk.Button(frame1, text="  +  ", command=up)
    up_button.place(x=math.ceil(screen_width/13.5), y=math.ceil(screen_height/11), height=math.ceil(screen_height/8.8), width= math.ceil(screen_width/13.5))
    # Bouton pour diminuer le BPM
    down_button = tk.Button(frame1, text="  -  ", command=down)
    down_button.place(x=0, y=math.ceil(screen_height/11), height=math.ceil(screen_height/8.8), width= math.ceil(screen_width/13.5))




root.attributes("-fullscreen", True)
def fullscreen () :
    global fs
    global screen_height
    global screen_width
    global pimage
    global tk_pimage
    if fs == 1 :
        screen_height = math.ceil(0.8*root.winfo_screenheight())
        screen_width = math.ceil(0.8*root.winfo_screenwidth())
        pimage=Image.open(FILES[6])
        pimage = pimage.resize((math.ceil(screen_width/5),math.ceil(screen_width/5)))
        tk_pimage = ImageTk.PhotoImage(pimage)
        root.attributes("-fullscreen", False)
        root.geometry(f'{screen_width}x{screen_height}')
        fs = 0
        close_button = tk.Button(frame2, image=tk_pag, command=fullscreen)
        close_button.place(x=0, y=0, height=math.ceil(screen_height/(44/3)), width= math.ceil(screen_height/(44/3)))
    else :
        screen_height = math.ceil(root.winfo_screenheight())
        screen_width = math.ceil(root.winfo_screenwidth())
        pimage=Image.open(FILES[6])
        pimage = pimage.resize((math.ceil(screen_width/5),math.ceil(screen_width/5)))
        tk_pimage = ImageTk.PhotoImage(pimage)
        root.attributes("-fullscreen", True)
        root.geometry(f'{screen_width}x{screen_height}')
        fs = 1
        close_button = tk.Button(frame2, image=tk_gap, command=fullscreen)
        close_button.place(x=0, y=0, height=math.ceil(screen_height/(44/3)), width= math.ceil(screen_height/(44/3)))
    trace(screen_width/16,[screen_width/16,screen_height/7],[0,0])
    metro()
# Bouton de sortiefullscreen


close_button = tk.Button(frame2, image=tk_gap, command=fullscreen)
close_button.place(x=0, y=0, height=math.ceil(screen_height/(44/3)), width=math.ceil(screen_height/(44/3)))

canvas.bind("<Button-1>",zoneclick)


def find_output():
    global mo
    midi = rtmidi.MidiOut()
    ports = midi.get_ports()
    midi.close_port() 
    for i, name in enumerate(ports):
        if LOOPMIDINAME.lower() in name.lower():
            mo, _ = open_midioutput(i)
            port_found = True
        else:
            port_found = False
    if not port_found:
        mo, _ = open_midioutput(use_virtual=True)

metro()
find_output()




root.mainloop()
