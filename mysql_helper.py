class mysql_helper(object):
    def __init__(self,host,port,user,passwd,db,charset="utf8"):
        try:  
            self._conn=MySQLdb.connect(host=host,port=port,user=user,passwd=passwd,db=db)  
            self._conn.set_character_set(charset)  
            self.cursor=None
        except MySQLdb.Error as e:
            print ('MySql Error : %d %s' %(e.args[0],e.args[1])) 
        
    #def getCursor(self,cursorclass = MySQLdb.cursors.DictCursor):  
    def getCursor(self,cursorclass = None ):
        self.cursor=self._conn.cursor(cursorclass)
        return self.cursor
        
    def switchDB(self,db):
        try:
            self._conn.select_db(db)
        except MySQLdb.Error as e:  
            print ('MySql Error : %d %s' %(e.args[0],e.args[1])) 
            
    def insert_dict(self,table,Ddata): # 表名,字典
        fields=','.join(map(lambda x :x,Ddata))
        values=','.join(map(lambda x :'%('+x+')s',Ddata))
        sql=('INSERT INTO %s ( %s ) VALUES(%s)' %(table,fields,values))
        try:  
            rows=self.cursor.execute(sql,Ddata)               
            self.commit()
            return rows;
        except MySQLdb.Error as e:  
            print('MySql Error: %s SQL: %s'%(e,sql))
            
    def update_on_primi(self,table,set_cond,Ddata):#表名,set语句,字典(用字典游标select出来就是字典)
        w_cond=" and ".join(map(lambda x : '%s=%%(%s)s' %(x,x) ,Ddata))
        sql="update %s set %s where %s" %(table,set_cond,w_cond)
        print("sql:" ,sql)
        try:
            a=self.cursor.execute(sql,Ddata)
            print("row:",a)
            self.commit()
        except MySQLdb.Error as e:  
            print('MySql Error: %s SQL: %s'%(e,sql)) 
        
        
        
    def commit(self):  
        self._conn.commit()  
      
    def close_cur(self): 
        if self.cursor is not None:
            self.cursor.close()  
  
