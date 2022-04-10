import re
import urllib.parse
URL_FUNC_DICT = dict()
def route(url):  
    def set_func(func):  
        URL_FUNC_DICT[url] = func  
        def call_func():  
            pass  
    return set_func


@route(r"/add/(\d+)\.html")
def add_func(ret):
	arg = ret.group(1)
	print("add...." + str(arg))
	return "OK"

def application(file_name):
	file_name = urllib.parse.unquote(file_name)
	for url, func in URL_FUNC_DICT.items():
		ret = re.match(url,file_name)
		if ret:
			return func(ret)
		else:
			return "ERROR..."
