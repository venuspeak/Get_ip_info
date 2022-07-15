# __author__ = 'techxsh'
# -*- coding : utf-8 -*-
import warnings
warnings.filterwarnings('ignore')
import requests
import socket
import re
import linecache
import sqlite3
from multiprocessing.dummy import Pool as ThreadPool
from requests.packages.urllib3.exceptions import InsecureRequestWarning     # 禁用ssl安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import json
import sys

proxy_charge = 'off'    #代理开关
http_proxy = 'http://1.1.1.1:8080'    #获取IP归属外网代理
signdbpath = 'assert.db'   #资产标记库，优先匹配
threadnum = 5   #多线程配置，查询内网IP时使用，由于外网接口查询频率限制，外网IP较多时不宜配置过高

signdic = {
    r'11.65.230.':'无线',
    r'12.92.': '运维业务',
    r"135.": "集团",
    r"145.": "DCN未录入",
    r"155.": "DCN未录入"
}   #资产标记json，包含关系，优先级低于db匹配，支持IP头标记

def getipaddr_jingwai(ip):
    ipaddr = get_match_name(ip)
    if ipaddr:
        return(str(ipaddr[0]).replace('\\r', '').replace(',','').replace('(','').replace(')','').replace(' ','').replace('\'',''))
    else:
        for signaddr in signdic:
            # print(format(signaddr))
            sign = re.findall('^' + format(signaddr) + '.*$', ip)
            if len(sign) > 0:
                return(signdic[signaddr])
    url = "http://ip-api.com/json/"+ip+"?lang=zh-CN"
    # url = "http://m.ip138.com/ip.asp?ip=" + ip
    try:
        if proxy_charge == 'on':
            data = requests.get(url, proxies={'http': http_proxy,'https': http_proxy}).content.decode('utf-8')
        else:
            data = requests.get(url).content.decode('utf-8')
        # print(data)
        jsondata = json.loads(data)
        try:
            country = jsondata['country']
        except:
            country = ''
        # area = jsondata['data']['city']
        try:
            region = jsondata['regionName']
        except:
            region = ''
        try:
            city = jsondata['city']
        except:
            city = ""
        try:
            isp = jsondata['isp']
        except:
            isp = ''
        return (country+region+city+isp)
        # return ipaddress
        # return(ip+'  '+ipaddress)
    except requests.HTTPError as e:
        print('外网查询接口异常1')
        return ''
    except requests.ConnectionError as e:
        print('外网查询接口异常2')
        return ''
    except ConnectionResetError as e:
        print('外网查询接口异常3')
        return ''
    except socket.error as e:
        print('外网查询接口异常4')
        return ''
    except Exception as ex:
        print('外网查询接口异常5'+str(ex))
        exit()

def get_match_name(ip):
    conn = sqlite3.connect(signdbpath)
    c = conn.cursor()
    c.execute('''
    select NAME FROM assert where  IP="'''+ip+'''";''')
    name_match = c.fetchall()
    conn.commit()
    conn.close()
    # print(format(name_match))
    return (name_match)

def main(ip):
    ip = ip.replace('\n', '')
    addr = getipaddr_jingwai(ip)
    print(ip + '|' + addr)
    with open('outips.txt', 'a', encoding='utf-8') as out:
        out.write(ip + '|' + addr +'\n')

if __name__ == "__main__":
    iplist = linecache.getlines('ip.txt')
    pool = ThreadPool(processes=threadnum)
    i = 1
    for _ in pool.imap_unordered(main, iplist):
        sys.stdout.write('检测IP总进度: %d/%d\r' % (i, len(iplist)))
        i += 1