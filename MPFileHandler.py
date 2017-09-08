from  logging import FileHandler
import time,os
class MPFileHandler(FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=0):
        self.suffix = "%Y-%m-%d"
        self.suffix_time = self.get_currentTime()
        _filename=filename+'.'+self.suffix_time
        FileHandler.__init__(self, _filename, mode, encoding, delay)

    def get_currentTime(self):
        timeTuple = time.localtime()
        return time.strftime(self.suffix, timeTuple)

    def emit(self, record):
        """
        Emit a record.
        Always check time
        """
        try:
            if self.check_baseFilename():
                self.build_baseFilename()
            FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def check_baseFilename(self):
        if self.suffix_time != self.get_currentTime() or not os.path.exists(self.baseFilename+'.'+self.suffix_time):
            return 1
        else:
            return 0

    def build_baseFilename(self):
        if self.stream:
            self.stream.close()
            self.stream = None
       
        if self.suffix_time != "":
            index = self.baseFilename.find("."+self.suffix_time)
            if index == -1:
                index = self.baseFilename.rfind(".")
            self.baseFilename = self.baseFilename[:index]
     
        self.suffix_time = self.get_currentTime()
        self.baseFilename  = self.baseFilename + "." + self.suffix_time

        if not self.delay:
            self.stream = self._open()
            
            
'''
#一份参考配置
##############################################
[loggers]
keys=root,monitor, debug

[logger_root]
level=INFO
handlers=root

[logger_monitor]
level=INFO
handlers=handler01
propagate=0
qualname=monitor

[logger_debug]
level=DEBUG
handlers=handler01
qualname=debug

##############################################
[handlers]
keys=root,handler01

[handler_root]
class=StreamHandler
level=NOTSET
formatter=form02
args=(sys.stdout,)

[handler_handler01]
#class=logging.handlers.TimedRotatingFileHandler
class=extends.MPFileHandler
formatter=form01
args=('./log/monitor.log','a')

##############################################
[formatters]
keys=form01,form02

[formatter_form01]
format=%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s %(process)d %(message)s
datefmt=[%Y-%m-%d %H:%M:%S]

[formatter_form02]
format=%(asctime)s  %(filename)s [line:%(lineno)d] %(process)d %(message)s
datefmt=[%Y-%m-%d %H:%M:%S]

##############################################
  
'''


