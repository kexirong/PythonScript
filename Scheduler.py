#!/bin/env python
import os
import time
import Queue
import threading
import select
import sys
import socket
import json
import logging

VAL_QUEUE=Queue.Queue()
PATH= "./pyplugin"

logging.basicConfig(level=logging.DEBUG,  
                    filename=r'SchecdOut.log',  
                    filemode='w+',  
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')  


PLUGINMAP={}



class Plugin(object):
    __slots__ = {"name",'interval','instan'}
    def __init__(self):
        self.name = None
        self.interval = None
        self.instan = None
       


    

def instance_add(plugin):
    if not isinstance(plugin,Plugin):
        return False
    if not isinstance(plugin.interval,int) and plugin.interval <= 0 :
        return  False
    if not isinstance(plugin.name,str) and plugin.name  in  [None,'']:
        return  False
    if not hasattr(plugin.instan,"getvalue"):
        return  False
    if PLUGINMAP.get(plugin.interval):
        PLUGINMAP[plugin.interval].append(plugin)
    else:
        PLUGINMAP[plugin.interval]=[plugin]
    return True


def instance_del(plugin):
    
    if PLUGINMAP.get(plugin.interval):
        PLUGINMAP[plugin.interval].append(plugin)
    else:
        PLUGINMAP[plugin.interval]=[plugin]
    return True

 
def plugin_run(instan):
    try:
        values=getattr(instan.instan,"getvalue")()
        for i in values:
            if i['hostname'].startswith("localhost"):
                logging.error("hostname not allow localhost:%s",i)
                return
            VAL_QUEUE.put(json.dumps(i))
        
    except AttributeError:
        logging.error(dir(instan))
        
    except Exception,e:
         logging.error("%s:%s",instan.name,e)
       
 
 
class Cron(object):
    _instance = None
    
    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(Cron, cls).__new__(cls, *args, **kw)  
        return cls._instance  
        
    def __init__(self):
        self.timerec={k:int(time.time()) for k in PLUGINMAP}
    
    def cron(self):
        while True:
           # timesec=int(time.time())
            
            for i in PLUGINMAP: # key is int type,so...
                timewant=int(time.time())-self.timerec[i]
    
                
                if timewant < i:
                    time.sleep(0.1)
                    continue

                    
                self.timerec[i]=int(time.time())
                for j in PLUGINMAP[i]:
                    t =threading.Thread(target=plugin_run,args=(j,))
                    t.setDaemon(1)
                    t.start()
                    
    def up_timerec(self):
        if set(PLUGINMAP)==set(self.timerec):
            return
        comp=set(PLUGINMAP)-set(self.timerec)
        for i in comp:
            self.timerec[i]=0
        
    


            
            
class  AFUNIX_TCP(object):
    def __init__(self):
        self.sock=socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        #self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.setblocking(0)
        self.epoll=select.epoll()
    
    def conn(self,path='agent.sock'):
        while True:
            if os.path.exists(path):
                try:
                    self.sock.connect(path)
                except socket.error:
                    logging.error("coonect server failed")
                    self.__init__()
                    continue
                break
            else:
                logging.warning("waiting server...")
                time.sleep(5)

    def send(self,msg):
        n = self.sock.send(msg+"\n")
        return n
        
         
    def recv(self):
        return self.sock.recv(1024)
        
        
    def colse(self):       
        self.sock.close()

   
    def transfer(self):

        while True:
            self.conn()
            self.epoll.register(self.sock.fileno(),select.EPOLLIN|select.EPOLLOUT)

            while True:
                events = self.epoll.poll(15)

                if not events :
                    break
                logging.debug("select.EPOLL events: %s",events)
                for fileno, event in events:
                    if event&select.EPOLLIN:
                        rec=self.recv()
                        logging.debug("select.EPOLLIN is turue %s",rec)
                        if len(rec) != 0:
                            do(parse(rec))

                    if event&select.EPOLLOUT:

                        while not VAL_QUEUE.empty():
                            msg=VAL_QUEUE.get()
                            n=self.send(msg)
                            logging.info("----sendmsg---:%s,%s" %(msg,n))

                        #   continue
                        time.sleep(0.5)


                    if event&select.EPOLLHUP :
                        logging.warning("select.EPOLL:EPOLLHUP")
                        self.epoll.unregister(fileno)
                        self.sock.close()
                        break
                        
                
       

def do(cmd):
    if cmd is None:
        return
    if cmd["op"]=="addplugin":
        if not cmd.get('plugins'):
            return
            
        for i in cmd['plugins']:
            plugin=loadplugin(i)
            if plugin:
                instance_add(plugin)
        Cron().up_timerec()   
        
    return 'done' 
        
        
    
def parse(recv):
    try:
        cmd=json.loads(recv)
    except ValueError:
        logging.error(recv)
        cmd=None
    return cmd
    
def loadplugin(name):
    try:
        plugin=Plugin()
        
        plugin.instan=__import__(name)
        plugin.name=plugin.instan.NAME
        plugin.interval=plugin.instan.interval
    except Exception,e:
        logging.error(e) 
        plugin=None
        
    return plugin
    

def mian():
    sys.path.append(PATH) 
    dirlist=os.listdir(PATH)
    logging.info("curdir:%s",dirlist)
    for i in dirlist:
        if not i.endswith(".py"):
            continue
        plugin=loadplugin(i[0:-3])
        if plugin:
            instance_add(plugin)
   
    logging.info( 'start AFUNIX_TCP client ')
    t=threading.Thread(target=AFUNIX_TCP().transfer) 
    t.setDaemon(1)
    t.start()
    logging.info('run cron... ')
    
    Cron().cron()
    
        

if __name__ == '__main__':

    mian()
