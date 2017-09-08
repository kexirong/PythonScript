# -*- coding:utf-8 -*- -
from bs4 import BeautifulSoup
import urllib2,socket
import time
 
import sys
 
 
host_name = 'http://www.qu.la/book/11309/'
 
def html_process(html_file,url):

    soup = BeautifulSoup(html_file,"html.parser")

    text = 'wcfjl.txt'
    file = open(text,'a+')
    file.write( soup.find('title').get_text()+ '\r\n')
    file.write( soup.find('div',id='content').get_text() + '\r\n')
    print soup.find('title').get_text()
    file.close()
 
    link = soup.find_all('a',class_='next')[0]
    
   
    if None == link:
        print 'next link is None'
        exit(0)
    
    next_href = host_name + link['href']
    print next_href
    return next_href
 
 
def html_get(url):
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0"
    headers = {'User-Agent':user_agent}
    req = urllib2.Request(url,headers = headers)
    try:
        page = urllib2.urlopen(req,timeout=50).read()
        return page
    except urllib2.URLError,e:
        print "error while loading" + url
        exit(1)
    except socket.timeout:
        time.sleep(10)
        return html_get(url)
 
def test(url):
    while None != url:
        html_file = html_get(url)
        if None == html_file:
            print 'ERROR OF READING ',url
            exit(1)
        url = html_process(html_file,url)
        #time.sleep(10)
 
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding( "utf-8" )
    
    test("http://www.qu.la/book/11309/22515448.html")
