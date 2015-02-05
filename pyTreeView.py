# pyTreeView.py
# Python (data cube) Tree view
# chrislee@cs.uoregon.edu

import copy, math
from turtle import *

class cuboids:
    up =[]
    down =[] 
    value=0
    def __init__(self):
        del self.up[:]
        del self.down[:]
        value = 0

class lattice:
    l_down = []
    l_up=[]
    l_pos=[]
     #c = init_link()
    #cu = cuboids()
    def __init__(self):
        dimension=4
        screen_width=650
        screen_height=300
        
        level_pos=[0,0,0,0,0,0]
        mask_up=[]
        mask_up.append(14);mask_up.append(13);mask_up.append(11);mask_up.append(7);
        mask_down=[]
        mask_down.append(8);mask_down.append(4);mask_down.append(2);mask_down.append(1);        
        for x in range(0,16):
            cu = cuboids()
            cu.value = x
            for y in range(0,4):
                up_temp=str(bin(mask_up[y]&x))
                down_temp=str(bin(mask_down[y]|x))
                if bin(mask_up[y]&x)!=bin(x) and bin(mask_up[y]&x) not in cu.up:
                    cu.up.append(bin(mask_up[y]&x))
                if bin(mask_down[y]|x)!=bin(x) and bin(mask_down[y]|x) not in cu.down:
                    cu.down.append(bin(mask_down[y]|x))
            #print(cu.value)
            #print('up',cu.up)
            #print('down',cu.down)
            #print()
            level=str(bin(x)).count('1')
            C=int((math.factorial(dimension)/(math.factorial(level)*math.factorial(dimension-level))))
            #if level==2: print(cu.value,'in',level,'have',C)
            temp=level_pos.pop(level)
            level_pos.insert(level,temp+(screen_width/(C+1)))
            self.l_pos.append([int(level_pos[level])-300,int(screen_height-level*(screen_height/dimension+1))-200])
            self.l_up.append(copy.deepcopy(cu.up))
            self.l_down.append(copy.deepcopy(cu.down))
            #if level==2: print('pos',level_pos[level])
        #print('down',self.l[x].down)
        return
    
def translate(i):
    clist=[]
    mask=list(["Time","Item","Location","Suppier"])
    i=i.lstrip('0b')
    if len(i)<4:
        temp=len(i)
        for x in range(0,4-len(i)):
            i='0'+i
    s = list(i)
    for y in range(0,4):
        if s[y]=='1':
            clist.append(mask[y])
    return ",".join(clist)

def drawlattice(l):
    up()
    goto(-100,0)
    down()
    for x in range(0,16):
        up()
        goto(l.l_pos[x])
        down()
        dot(10,'gray')
        namepart = '['+ translate(bin(x)) + ']'
        write(namepart, font=('Arial', 8, 'normal'))
    for y in range(0,16):
        up()
        goto(l.l_pos[y])
        down()
        temp=0
        for z in l.l_down[y]:
            goto(l.l_pos[int(l.l_down[y][temp],2)])
            goto(l.l_pos[y])
            #print(int(l.l_down[y][temp],2))
            temp=temp+1


# Add main and module by daveti
'''
l=lattice()
#print(int(l.l_down[0][2],2))
drawlattice(l)

#int(l.l_down[y],2)
'''
def main():
	l=lattice()
	drawlattice(l)

if __name__ == '__main__':
	main()

