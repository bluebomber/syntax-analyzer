import sys
import os
import os.path
from tkFileDialog import askopenfilenames
import re

import subprocess
from Tkinter import *
import Pmw
from MySimpleDialog import * # deleted Clue; resides now in site-packages
import zipfile
import datetime

import tkMessageBox
import tkSimpleDialog
from tkFileDialog import askdirectory
import shutil
import time
# from NewClue.clue_config import clue_config

def C_file_chooser(master): # chooses from current working directory
    L = ['*.c'] + glob.glob('*.c')
    if os.path.exists('Makefile'):
	L.append('Makefile')
    if os.path.exists('makefile'):
	L.append('makefile')
    X = List_Selection2(master,L,'Choose one or more files')
    K = list(X.result)
    if '*.c' in K:
	K = ['*.c']
    return K

def getTimeStamp(): # All platforms
    X = datetime.datetime
    return '%s-%s-%s_%s-%s' %(X.month,X.day,X.year,X.hour,X.minute)

def getDateStamp(): # All platforms
    X = datetime.date.today()
    return datetime.date.isoformat(X)

def getDateStamp2():
    X = datetime.date.today()
    return X.strftime("%A-%B-%d-%Y")


class getFontSize(Dialog2):  # Need to initialize with current fontsize
    def body(self,master):
        self.title = 'Xemacs Font Size'
        Label(master, text = 'New font size: ').grid(row=0,sticky=W)

        self.font_size = self.args[0]        
        self.fontsize_entry = Entry(master,width=10)
        self.fontsize_entry.insert(0,self.font_size)

        self.fontsize_entry.grid(row=0,column=1,sticky=W)
        
	self.fontsize_entry.focus_set()
        
    def apply(self):
        self.font_size = self.fontsize_entry.get()

def getOSname(): # Windows only; not currently used
    x = sys.getwindowsversion()[0:3]
    if x == (5,1,2600):
	return 'XP'
    if x == (6,0,6001):
	return 'Vista'
    if x == (6,1,7600):
	return 'Windows7'

class EditorSelector(object):
    def __init__(self,parent,configment):
        parent.configure(background = 'white')
	self.config = configment
        # Create and pack the simple ComboBox.
        self.EditorBox = Pmw.ComboBox(parent,
                label_text = 'Editor',
                labelpos = 'w',
                selectioncommand = self.changeText,
                scrolledlist_items = self.config.edict.keys(),
                dropdown = 1,
		listheight=20*len(self.config.edict.keys()),
        )

        self.EditorBox.pack(side=TOP,anchor=NW)

        # Display the first text.
        self.EditorBox.selectitem(self.config.current_ed)

    def changeText(self, text):
	self.config.current_ed = text

    def refresh(self):
        self.EditorBox._list.setlist(self.config.edict.keys())
	self.EditorBox._entryfield.setvalue(self.config.current_ed)

class CompilerSelector(object):
    def __init__(self,parent,configment):
        parent.configure(background = 'white')
	self.config = configment
        # Create and pack the simple ComboBox.
        self.CompilerBox = Pmw.ComboBox(parent,
                label_text = 'Compiler',
                labelpos = 'w',
                selectioncommand = self.changeText,
                scrolledlist_items = self.config.cmpdict.keys(),
                dropdown = 1,
		listheight=20*len(self.config.cmpdict.keys()),
        )

        self.CompilerBox.pack(side=TOP,anchor=NW)

        # Display the first text.
        self.CompilerBox.selectitem(self.config.current_compilerDir)

    def changeText(self, text):
	self.config.current_compilerDir = text

    def refresh(self):
        self.EditorBox._list.setlist(self.config.cmpdict.keys())
	self.EditorBox._entryfield.setvalue(self.config.current_compilerDir)

try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED


def zipFileList(zipfileName,fileList):
    zf = zipfile.ZipFile(zipfileName,mode='a')
    for nom in fileList:
        zf.write(nom)
    zf.close()
    return zf

def unzipFileList(zipfileName):
    zf = zipfile.ZipFile(zipfileName,'r')
    for nom in zf.namelist():
        with open(nom,'w') as f:
            f.write(zf.read(nom))

def fixEOL(f):
    with open(f,'r') as g:
	S = g.read()
	S = S.replace('\r\n','\n')
    with open(f,'w') as g:
	g.write(S)

def fixComments(fnom):
    with open(fnom,'r') as f:
    	S = f.read()
	S = S.replace('\r\n','\n')
    if '//' in S:
    	L = re.findall(r'//(.+)',S)
	for x in L:
    	    S = S.replace('//' +x, '/* '+ x + '*/')
    with open(fnom,'w') as f:
    	f.write(S)

def wipeDirectory(theDir):
    if sys.platform[:3] == 'win':
    	os.system('rmdir /S/Q %s' %theDir)
    else:
    	os.system('rm -r %s') %theDir

class List_Selection(Dialog2):
    def body(self,master):
        self.theList = self.args[0]
        self.prompt = self.args[1]
        Label(master,text=self.prompt).pack()
        self.listing = Pmw.ScrolledListBox(master)
        self.listing._listbox.config(selectmode=SINGLE)
        self.listing.pack()
        # self.theList.sort()
        self.listing.setlist(self.theList)
        self.result = None

    def apply(self):
        self.result = self.listing.getcurselection()[0]

class List_Selection2(Dialog2):
    def body(self,master):
        self.theList = self.args[0]
        self.prompt = self.args[1]
        Label(master,text=self.prompt).pack()
        self.listing = Pmw.ScrolledListBox(master)
        self.listing._listbox.config(selectmode=EXTENDED,width=50)
        self.listing.pack()
        # self.theList.sort()
        self.listing.setlist(self.theList)
        self.result = None

    def apply(self):
        self.result = self.listing.getcurselection()

def getMakeTargets(mkfile):
    targets = []
    with open(mkfile,'r') as f:
	L = f.readlines()
    for k in L:
	if k != '' and not k.startswith('\t'):
	    targets.append(k.split(':')[0].strip())
    return targets

def getOutputLines(cmd):
    X = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    S = X.communicate()[0]
    if sys.platform.startswith('win'):
        return S.split('\r\n')
    else:
        return S.split('\n')

def getOutput(cmd):
    X = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    S = X.communicate()[0]
    return S

def getOutputLine(cmd,lastpart):
    L = getOutputLines(cmd)
    for pth in L:
	if pth.endswith(lastpart):
	    pth = pth.replace(lastpart,'')	    
	    return pth.strip()
    return ''


##################
#Windows specific#
##################
def getTimeStamp():
    cmd = 'date /T'
    X = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    retcode = X.wait() #??
    date_string = X.communicate()[0].strip()
    date_string = date_string.replace('/','-')
    date_string = date_string.replace(' ','_')

    cmd = 'time /T'
    X = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    retcode = X.wait()
    time_string = X.communicate()[0].strip()
    time_string = time_string.replace('/','-')
    time_string = time_string.replace(' ','-')
    time_string = time_string.replace(':','-')
    timestamp = date_string+'_'+time_string
    return timestamp


def has_main(fname):
   if fname == '' or not os.path.exists(fname):
	return False
   f = open(fname,'r')
   aline = f.readline()
   t = re.search(r'int\s+main\s*\(',aline)
   while aline != '' and t == None:
   	aline = f.readline() 
	t = re.search(r'int\s+main\s*\(',aline)

   return t != None

def have_main(flist):
    if flist == []:
   	return -1
    mainfiles = []
    for fnom in flist:
	if has_main(fnom):
       	    mainfiles.append(fnom)
    return mainfiles


##################
#Windows specific#
##################
def doubler(S):
    L = re.findall(r'\\([^\\]+)',S)

    K = re.findall(r'([^\\]+)\\',S)
    start = K[0]+'\\\\'
    return start + '\\\\'.join(L)

##################
#Windows specific#
##################
def correctForSpace(thePath):
    # thePath is an absolute path, so just in case:
    thePath = os.path.abspath(thePath)
    if sys.platform[:3] != 'win' or thePath == '':
        return thePath

    if '/' in thePath:
	thePath = thePath.replace('/','\\')

#    if thePath.startswith('\\'):
#	thePath = 'C:'+thePath

    if os.path.isfile(thePath):
        thedir = os.path.dirname(thePath)
        fname = os.path.basename(thePath)

    else:
        thedir = thePath
        fname = ''

    originalDir = thedir

    comps = thedir.split('\\')
    partialPath = comps[0]+ '\\'
    if ' ' in comps[1]:
        cmd = 'dir /X %s' %partialPath
	dirline = getOutputLine(cmd,comps[1])
    	partialPath += dirline.split()[-1]
    else:
	partialPath += comps[1]

    for i in range(2,len(comps)):
 	if ' ' not in comps[i]:
	    nextPart = '\\'+comps[i]
	    partialPath += nextPart
	    continue

	cmd = 'dir /X '+ partialPath
      	dirline = getOutputLine('dir /X %s' %partialPath,comps[i])
        if dirline == '':
	    print 'BAD PATH'
	    return thePath

	newcomp = dirline.split()[-1]
        nextPart = '\\'+newcomp
   	partialPath += nextPart

    if fname == '':
	return partialPath

    retval = partialPath + '\\' + fname
    if ' ' not in fname:
        return retval
    else:
        return '"%s"' %retval 
    

def C_fileChooser(firstdir):
    typelist = [('C Files','.c'),('C Files','Makefile'),('C Files','makefile')]
    myroot = Tk()
    myroot.withdraw()
    L = str(askopenfilenames(title='Choose compile target(s)',filetypes=typelist,initialdir=firstdir))
    myroot.destroy()

    if '{' in L:
	flist =  re.findall(r'{([^}]+)',L)
    else:
	flist = [L]
    flist = [correctForSpace(k) for k in flist]  # Windows specific
    return flist

class PleaseWait(object):
    def __init__(self,master,msg):
        self.tl = Toplevel(master)
        ltext = '  %s: this may take a while, please be patient  ' %msg
        Label(self.tl,text=ltext,font=('Arial',12,'bold')).pack(side=TOP)
     
            
if __name__ == '__main__':
   root = Tk()
   S = getDateStamp()
   print S
   T = getDateStamp2()
   print T
#    L = []
#    L.append("one")
#    L.append("two")

#    X = List_Selection(root,L,"Do it")
#    print X.result
   root.mainloop()
