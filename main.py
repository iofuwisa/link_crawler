import requests
from requests import Response
from bs4 import BeautifulSoup
import re
import datetime
from dateutil.relativedelta import relativedelta
import math
import random
import time
import logging
import csv
import os
from requests.exceptions import Timeout

# アクセス禁止ドメインリスト
protectList = []

# クローリングサイトリスト
siteList = []

# アクセス禁止ドメインリストを取得
def getProtectList():
    # ルートリスト取得
    if os.path.isfile("protectlist.csv"):
        with open ("protectlist.csv", mode="r") as f :
            protectList.clear()
            reader = csv.reader(f)
            for row in reader:
                protectList.append(row[0])

# 登録済みサイトリストからランダムサイトを一つ返す
def nextRoot():
    # ルートリスト取得
    if os.path.isfile("sitelist.csv"):
        with open ("sitelist.csv", mode="r") as f :
            rootList = []
            reader = csv.reader(f)
            for row in reader:
                rootList.append(row[0])
            return rootList[math.floor(random.random()*len(rootList))]
    return ""

def getRoot(path):
    reResult=re.match("^(http(s)?:\/\/)[A-Z|a-z|0-9|\-|.]+", path)
    if reResult == None:
        logging.error("Faild to get damaine neme '%s'" % (path))
        return ""
    return reResult.group()

# 追加(既存の場合は最終アクセス時刻をアップデート)
def add(fullPath, root = "", lastAccess = datetime.datetime.now()):
    if root =="":
        root = getRoot(fullPath)
    if root =="":
        return


    isExist = False
    for site in list(filter(lambda s: s['FullPath']==fullPath, siteList)):
        isExist = True
        if site['LastAccess'] < lastAccess:
            site['LastAccess'] = lastAccess
        break
    if (not isExist) and (not isProtect(root)):
        siteList.append({'FullPath': fullPath, 'Root': root, 'LastAccess': lastAccess})

def access(targetPath):

    # ルートパス取得
    root = getRoot(targetPath)
        
    # 対象ルートの最終アクセス時刻取得
    # アクセス記録がなければ[2000/01/01 00:00:00]とする
    lastAccess = datetime.datetime(2000, 1, 1, 0, 0, 0)
    for site in list(filter(lambda s: s['Root']==root, siteList)):
        if lastAccess < site['LastAccess']:
            lastAccess = site['LastAccess']
    
    # 最終アクセスが現在時刻から2秒以内ならリターン
    if lastAccess >= datetime.datetime.now() - relativedelta(seconds=2):
        logging.error("Last access is after 2 sec ago '%s'" % (lastAccess.strftime('%Y-%m-%d %H:%M:%S')))
        return

     # リトライは1回まで
    for i in range(2):
        try:
            response: Response = requests.get(targetPath, timeout=(2.0, 5.0))
        except Timeout:
            logging.error("GET request timeout '%s'" % (targetPath))
            return
        if response.status_code==200:
            break
        # 失敗時は2秒後にリトライ
        time.sleep(2)

    # 対象ページのレコードを更新
    add(targetPath)

    # アクセス失敗
    if response.status_code!=200:
        logging.error("Faild to access '%s'" % (targetPath))
        return

    # パース
    soup: BeautifulSoup = BeautifulSoup(response.text, features="lxml")

    # metaの"noindex"チェック
    # for metatag in soup.find_all("meta", content="noindex"):

    # metaの"nofollow"チェック
    for metatag in soup.find_all("meta", content="nofolow"):
        return

    # https:// http:// を登録(nofollow は除外)
    for atag in soup.find_all("a", href=re.compile("^(http(s)?:\/\/)"), rel=re.compile("^(?!(nofollow))")):
        add(atag['href'], lastAccess=datetime.datetime(2020, 1, 1, 0, 0, 0))

    # // を登録(プロトコル継続の別ドメイン)(nofollow は除外)
    for atag in soup.find_all("a", href=re.compile("^(//)"), rel=re.compile("^(?!(nofollow))")):
        fullPath = re.match("^(http(s)?:)", targetPath).group()
        fullPath = fullPath + atag['href']
        add(fullPath, lastAccess=datetime.datetime(2020, 1, 1, 0, 0, 0))

    # 内部リンクを登録(nofollow は除外)
    for atag in soup.find_all("a", href=re.compile("^((?!((http(s)?:\/\/)|#|\/\/)))"), rel=re.compile("^(?!(nofollow))")):
        # リンク元から「?」と「#」を削除
        fullPath = re.match("^[a-z|A-Z|0-9|\-|_|.|!|'|(|)|%|:|\/]+", targetPath).group()
        # 「/」が連続するのを防ぐ
        # リンク元の末尾に「/」が無ければ追加
        if not re.match(".*\/$", fullPath):
            fullPath += "/"
        # リンク先頭に「/」があれば削除
        if re.match("^\/", atag['href']):
            fullPath = fullPath[0:len(fullPath)-1]
        # リンクパス結合
        fullPath = fullPath + atag['href']
        add(fullPath, lastAccess=datetime.datetime(2020, 1, 1, 0, 0, 0))

def store():
    # 重複なしのルートリスト作成
    rootList = []
    if os.path.isfile("sitelist.csv"):
        with open ("sitelist.csv", mode="r") as f :
            reader = csv.reader(f)
            for row in reader:
                rootList.append(row[0])
            for site in siteList:
                rootList.append(site['Root'])
            rootList = list(set(rootList))

    # 書き込み
    with open ("sitelist.csv", mode="w") as f :
        for root in rootList:
            f.write("%s\n" % root)
        
def isProtect(path):
    for word in protectList:
        if word in path:
            return True
    return False

def main():

    # スクレイピング禁止サイトリスト取得
    getProtectList()

    for i in range(20):
        # 初期サイト設定
        n = nextRoot()
        siteList.append({'FullPath': n, 'Root': n, 'LastAccess': datetime.datetime(2020, 1, 1, 0, 0, 0)})

        print("next: %s" % n)

        # 初期サイトをベースに10回リンクをたどる
        for j in range(10):
            # クローリングサイトリストからランダムなサイトを指定
            targetIndex = math.floor(random.random()*len(siteList))

            print("  target: %s" % siteList[targetIndex]['FullPath'])

            # アクセス
            access(siteList[targetIndex]['FullPath'])

            # クローリングサイトリストの要素数が1以下なら終了
            if len(siteList) <= 1:
                break

        # クローリングサイトリストを登録
        store()

        # クローリングサイトリストをクリア
        siteList.clear()

if __name__ == "__main__":
    main()