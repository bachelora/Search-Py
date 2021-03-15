import urllib.request
from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import importlib,sys 
importlib.reload(sys)
import os,time
import csv
from multiprocessing import Pool
import functools
import time,threading
from concurrent.futures import ThreadPoolExecutor
import sys
import ast
import string
import gzip
from gzip import GzipFile
import io
import zlib
from urllib.parse import quote

RESULT_FAILED = "failed"

MAX_WORKER = 10


class Logger(object):
    def __init__(self, filename='default.log', stream=sys.stdout):
        self.terminal = stream
        self.log = open(filename, 'w')
 
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
 
    def flush(self):
        pass
   
sys.stdout = Logger('a.log', sys.stdout)
sys.stderr = Logger('a.log_file', sys.stderr)



def __gzip(data):
	buf = io.BytesIO(data)
	f = gzip.GzipFile(fileobj=buf)
	return f.read()
 
def __deflate(data):
	try:
		return zlib.decompress(data, -zlib.MAX_WBITS)
	except zlib.error:
		pass


def openDestUrl(link):
	headers = {
	'User-Agent': 'Mozilla/5.0 (compatible;Baiduspider-render/2.0; +http://www.baidu.com/search/spider.html;soso;360;sogou)'}
	req = urllib.request.Request(link,headers=headers)
	try:
		html = urllib.request.urlopen(req,data=None,timeout=5).read()

		soup = BeautifulSoup(html,'lxml')
	except Exception as e:#failed
		print(e)
		return RESULT_FAILED
	
	if soup.title == None:
		print(soup)
		return RESULT_FAILED
	
	title = soup.title.string

	if title == None:
		print(soup)
		return RESULT_FAILED
	print(title)
	time.sleep(60)
	return title

def getCurrentTime():
	return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def sogoSearch():
	pass

def getDomain(url):
	if url == None or len(url) < 1:
		return ''
	if '.' not in url:
		url = url + '.com'
	url = url.replace('...','')
	if url.startswith('www.'):
		url = 'http://' + url
	elif url.startswith('http'):
		pass
	else:
		url = 'http://www.' + url
	ret = urlparse(url).netloc
	array = ret.split('.')
	if len(array) > 1:
		return array[len(array)-2] + '.' + array[len(array)-1]
	return ''


BAIDU_BASE_URL = 'http://www.baidu.com'

def baiduSearchOnPC(baiduLink,dest_url,maxPage,timeSpan,currentPage=1):
	headers = {
	'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	'Accept-Encoding': 'gzip,deflate',
	'Accept-Language': 'zh-CN,zh;q=0.9',
	'Cache-Control': 'max-age=0',
	'Connection': 'keep-alive',
	'Host': 'www.baidu.com',
	'Cookie': 'WWW_ST=1615775864250',
	'is_referer': 'http://www.baidu.com/',
	'is_xhr': 1,
	'Upgrade-Insecure-Requests': 1,
	'X-Requested-With': 'XMLHttpRequest',
	'User-Agent': 'Mozilla/5.0 (Windows NT 9.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'}

	req = urllib.request.Request(baiduLink,headers=headers)

	try:
		response = urllib.request.urlopen(req,data=None,timeout=15)
		html = response.read()
		encoding = response.info().get('Content-Encoding')

		if encoding == 'gzip':
			print('gzip')
			html = __gzip(html)
		elif encoding == 'deflate':
			print('deflate')
			html = __deflate(html)

		soup = BeautifulSoup(html,'lxml')
	except Exception as e:#failed
		print(e)
		return RESULT_FAILED

	content_left = soup.find("div", {"id": "content_left"})
	if content_left == None:
		print('id=content_left none')
		print(response.read())
		#print(print('Data:', html.decode('utf-8')))
		print(soup.prettify())
		return

	divList = content_left.findChildren("div" , recursive=False)
	if len(divList) > 0:
		index = 1
		for div in divList:
			cTools = div.find('div', attrs={'class':'c-tools c-gap-left'})
			if cTools == None:
				index += 1
				continue
			dataTools = cTools.get('data-tools')
			dataToolsDict = ast.literal_eval(dataTools)
			title = dataToolsDict['title']
			baiduUrl = dataToolsDict['url']
			dest = ''

			cShow_url = div.find('a',attrs={'class':'c-showurl c-color-gray'})
			if cShow_url != None:
				text = cShow_url.text
				if text != None and len(text) > 0:
					dest = text

			result = (index,title,dest,getDomain(dest),baiduUrl)
			print(result)
			if getDomain(dest).lower() == dest_url:
				print('find--------------------------------------------------------------------------')
				time.sleep(timeSpan)
				openDestUrl(baiduUrl)
				return
			index += 1

	if maxPage > currentPage:
		baiduLink = '' #try to  find the url of next page
		page_inner = soup.select("div[id=page] > div[class=page-inner]")
		if page_inner == None or len(page_inner) < 1:
			print('no div[id = page-inner]')
			return

		pageButtons = page_inner[0].contents
		for button in pageButtons:
			if button == '\n':
				continue

			spanPC = button.find("span", {"class": "pc"})
			if spanPC == None:
				continue
			number = int(spanPC.text)
			if number == currentPage+1:
				href = button.get('href')
				if href != None and len(href) > 0:
					baiduLink = BAIDU_BASE_URL + href

		print('next page:%d  url:%s' %(currentPage+1,baiduLink))
		time.sleep(timeSpan)
		baiduSearchOnPC(baiduLink,dest_url,maxPage,timeSpan,currentPage+1)


if __name__ == '__main__':
	print('begin:' + getCurrentTime())
	csvFile = open('./input.csv', "r")
	reader = csv.reader(csvFile)
	inputData = []

	for item in reader:
		if reader.line_num == 1:
			continue
		inputData.append(item)
	csvFile.close()

	for row in inputData:
		keyword = row[0]
		dest_url = row[1]
		maxPage = int(row[2])
		timeSpan = int(row[3])

		if keyword == None or dest_url == None:
			continue

		baiduLink = BAIDU_BASE_URL + '/s?wd=' + keyword.replace(' ','%20') #空格替换成%20
		baiduLink = quote(baiduLink, safe=string.printable)
		#baiduLink = 'http://www.baidu.com/s?ie=utf-8&mod=1&isbd=1&isid=FCBD1F6E80C71170&ie=utf-8&f=8&rsv_bp=1&tn=baidu&wd=python%E5%AD%97%E7%AC%A6%E4%B8%B2%20%E5%88%86%E5%89%B2&oq=python%25E5%25AD%2597%25E7%25AC%25A6%25E4%25B8%25B2%2520%25E5%2588%2586%25E5%2589%25B2&rsv_pq=cd350ba1000203b8&rsv_t=2d359GW7%2FtKC42wOxKOTE%2F4jF3eLpiorUs7VYNBY7Dtsf3KSXUFR1wh8eoQ&rqlang=cn&rsv_dl=tb&rsv_enter=0&rsv_btype=t&bs=python%E5%AD%97%E7%AC%A6%E4%B8%B2%20%E5%88%86%E5%89%B2&rsv_sid=undefined&_ss=1&clist=&hsug=&f4s=1&csor=0&_cr1=34322'
		print('baiduLink  :'+baiduLink)
		#baiduLink = 'http://www.baidu.com'
		#baiduLink = 'http://www.baidu.com/s?ie=utf-8&mod=1&isbd=1&isid=80b0b12600026efe&ie=utf-8&f=8&rsv_bp=1&rsv_idx=1&tn=baidu&wd=urban&fenlei=256&oq=urban&rsv_pq=80b0b12600026efe&rsv_t=daaft%2FlkP9azrKJVkq86xDclsNNm7zoyxg%2FXLCx8iaNSdYwuKmpXzu%2Blxn4&rqlang=cn&rsv_enter=0&rsv_dl=tb&rsv_btype=t&rsv_sug3=5&rsv_sug1=4&rsv_sug7=100&rsv_sug4=6152&rsv_sug=1&bs=urban&rsv_sid=33272_31254_33594_33570_26350&_ss=1&clist=2f40c870495d3711&hsug=&f4s=1&csor=5&_cr1=34370'
		baiduSearchOnPC(baiduLink,getDomain(dest_url).lower(),maxPage,timeSpan)

	'''
	with ThreadPoolExecutor(max_workers=MAX_WORKER) as t: #10个线程同时开跑
		for domain in domainSet:
			t.submit(checkDomain, domain).add_done_callback(threadCallBack)
	'''

	#os.system("explorer.exe " + os.getcwd())
