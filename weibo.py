# -*-coding:utf8-*-

import re
import string
import sys
import os
import urllib
import urllib2
import shutil
from bs4 import BeautifulSoup
import requests
from lxml import etree

import pdb

reload(sys)
sys.setdefaultencoding('utf-8')
cookie = {"Cookie": ""}


def get_url(user_id, page=1):
    if user_id.isdigit():
        url='http://weibo.cn/u/%s?filter=1&page=%d' % (user_id, page) #user_id is number.
    else:
        url='http://weibo.cn/%s?filter=1&page=%d' % (user_id, page) #user_id is string.
    return url


def get_page_count(user_id):
    html = requests.get(get_url(user_id, 1), cookies=cookie).content
    selector = etree.HTML(html)
    pageNum = (int)(selector.xpath('//input[@name="mp"]')[0].attrib['value'])
    return pageNum

#pdb.set_trace()


def get_label_by_url(url, label_name, regex=None):
    lxml = requests.get(url, cookies=cookie).content
    # 图片爬取
    soup = BeautifulSoup(lxml, "lxml")
    urllist = soup.find_all(label_name, href=re.compile(regex, re.I))
    return urllist


def get_real_url(html_url, cookie):
    request = requests.get(html_url, cookies=cookie).content
    soup = BeautifulSoup(request, 'lxml')
    for s in soup.find_all('a'):
        if u'原图' in s:
            return "http://weibo.cn%s" % s['href']
    return ""


if __name__ == '__main__':
    user_id = ''
    if len(sys.argv) >= 2:
        user_id = sys.argv[1]
    else:
        user_id = raw_input(u"请输入user_id: ")

    pageNum = get_page_count(user_id)


    result = ""
    urllist_set = set()
    word_count = 1
    image_count = 1

    print u'爬虫准备就绪...'

    for page in range(1, pageNum+1):

        # 获取lxml页面
        url = get_url(user_id, page)
        lxml = requests.get(url, cookies=cookie).content

        # 文字爬取
        selector = etree.HTML(lxml)
        content = selector.xpath('//span[@class="ctt"]')
        for each in content:
            text = each.xpath('string(.)')
            if word_count >= 4:
                text = "%d :" % (word_count - 3) + text + "\n\n"
            else:
                text = text + "\n\n"
            result = result + text
            word_count += 1

        # 图片爬取
        soup = BeautifulSoup(lxml, "lxml")
        # http://ww1.sinaimg.cn/wap360/79db9a58jw1f6b2l2z6o0j20qd0ghwip.jpg
        urllist = soup.find_all('a', href=re.compile(r'^http://weibo.cn/mblog/pic', re.I))
        first = 0
        for imgurl in urllist:
            redirect_img_url = imgurl['href']
            real_url = get_real_url(redirect_img_url, cookie)
            urllist_set.add(real_url)
            image_count += 1

    # fo = open("/Users/Personals/%s"%user_id, "wb")
    with open("/Users/jakoo/workspace/weibo/document/%s" % user_id, "wb") as f:
        f.write(result)
    word_path = os.getcwd() + '/%s' % user_id
    print u'文字微博爬取完毕'

    link = ""
    # fo2 = open("/Users/Personals/%s_imageurls"%user_id, "wb")
    with open("/Users/jakoo/workspace/weibo/document/%s_imageurls" % user_id, "wb") as f:
        for eachlink in urllist_set:
            link = link + eachlink + "\n"
        f.write(link)
    print u'图片链接爬取完毕'
    image_path = ''

    if not urllist_set:
        print u'该页面中不存在图片'
    else:
        # 下载图片,保存在当前目录的pythonimg文件夹下
        image_path = os.getcwd() + '/weibo_image'
        if os.path.exists(image_path) is False:
            os.mkdir(image_path)
        for i, imgurl in enumerate(urllist_set):
            temp = image_path + '/%s.jpg' % i
            print u'正在下载第%s张图片' % i
            #import pdb; pdb.set_trace()
            try:
                print imgurl
                r1 = requests.get(imgurl, cookies=cookie, allow_redirects=False)
                r = requests.get(r1.headers['Location'], stream=True)
                if r.status_code == 200:
                    with open(temp, 'wb') as f:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)
            except Exception as e:
                print u"该图片下载失败:%s (%s)" % (imgurl, e)
                x += 1

    print u'原创微博爬取完毕，共%d条，保存路径%s' % (word_count - 4, word_path)
    print u'微博图片爬取完毕，共%d张，保存路径%s' % (image_count - 1, image_path)
