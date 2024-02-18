from asyncio.windows_events import NULL
import os, time, re, shutil, base64
from ctypes import windll
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from enum import Enum
import json
from logging import getLogger, config

URL_商品詳細ページ = 'https://jp.mercari.com/item/'
URL_商品編集ページ = 'https://jp.mercari.com/sell/edit/'
URL_商品出品ページ = 'https://jp.mercari.com/sell/create'
URL_商品取引ページ = 'https://jp.mercari.com/transaction/'
URL_下書きページ = 'https://jp.mercari.com/sell/draft/'

ROW_データ_開始 = 2

COL_対象 = 1
COL_商品URL = 2
COL_商品名 = 3
COL_出品日 = 4

class FilterResult(Enum):
    NO_FILTER = 0
    CONTINUE = 1
    BREAK = 2

class SalesItemCells:
    def __init__(self):
        self.対象 = None
        self.商品URL = None
        self.商品名 = None
        self.出品日 = None

    def get商品ID(self):
        return re.search('/item/.*', self.商品URL.value).group(0)[6:]

class MercariItem:
    def __init__(self):
        self.商品ID = None
        self.商品画像 = None
        self.カテゴリー1 = None
        self.カテゴリー2 = None
        self.カテゴリー3 = None
        self.サイズ = None
        self.ブランド = None
        self.商品の状態 = None
        self.商品名 = None
        self.商品の説明 = None
        self.配送料の負担 = None
        self.配送の方法 = None
        self.発送元の地域 = None
        self.発送までの日数 = None
        self.現在価格 = None

    def get参照URL(self):
        return "https://jp.mercari.com/item/" + self.商品ID

    def get編集URL(self):
        return "https://jp.mercari.com/sell/edit/" + self.商品ID
    
    def Equals(self, item):
        for i in range(len(self.商品画像)):
            if self.商品画像[i] != item.商品画像[i]:
                return False
        if (self.商品ID != item.商品ID or
            self.カテゴリー1 != item.カテゴリー1 or
            self.カテゴリー2 != item.カテゴリー2 or
            self.カテゴリー3 != item.カテゴリー3 or
            self.サイズ != item.サイズ or
            self.ブランド != item.ブランド or
            self.商品の状態 != item.商品の状態 or
            self.商品名 != item.商品名 or
            self.商品の説明 != item.商品の説明 or
            self.配送料の負担 != item.配送料の負担 or
            self.配送の方法 != item.配送の方法 or
            self.発送元の地域 != item.発送元の地域 or
            self.発送までの日数 != item.発送までの日数 or
            self.現在価格 != item.現在価格):
            return False
        return True


def getItemList(driver):
    # 商品詳細ページを表示
    getPage(driver, "https://jp.mercari.com/mypage/listings")
    list = getElement(driver, '//div[@id="currentListing"]')
    items = list.find_elements(By.XPATH, '//a[@location-2="item"]')

    mercaliItemList = []
    for item in items:
        mercaliItem = MercariItem()
        url = item.get_attribute('href')
        arr = url.split('/')
        mercaliItem.商品ID = arr[-1]
        mercaliItem.商品名 = item.accessible_name
        mercaliItemList.append(mercaliItem)
    
    return mercaliItemList

def getRowData(ws, rowNo):
    cells = SalesItemCells()
    cells.対象 = ws.cell(row=rowNo, column=COL_対象)
    cells.商品URL = ws.cell(row=rowNo, column=COL_商品URL)
    cells.商品名 = ws.cell(row=rowNo, column=COL_商品名)
    cells.出品日 = ws.cell(row=rowNo, column=COL_出品日)
    return cells

def loopMain(func1, func2, driver, wb, logger):

    ws = wb.active

    cntAll = 0
    for num in range(2):

        cntCur = 0
        rowNo = ROW_データ_開始 - 1
        while True:

            rowNo = rowNo + 1

            cells = getRowData(ws, rowNo)
            
            result = func1(cells)
            if result == FilterResult.BREAK:
                break
            if result == FilterResult.CONTINUE:
                continue
            
            cntCur = cntCur + 1

            if num == 1:
                # ログ出力
                logger.info("■{0}　({1:3d}/{2:3d})".format(cells.get商品ID(), cntCur, cntAll))
                # 処理
                func2(driver, wb, cells, logger)
                # ログ出力
                logger.info('　完了')

        cntAll = cntCur

def getItemListFilePath():
    return  os.getcwd() + '\\item_list.xlsx'

def get商品ID(商品URL):
    return re.search('/item/.*', 商品URL).group(0)[6:]
    
def getDefaultLogger():
    with open(os.getcwd() + '\\log_config.json', 'r') as f:
        log_conf = json.load(f)

    config.dictConfig(log_conf)

    return getLogger("default")

def logInfo(msg):
    getLogger("default").info(msg)

def openChromeDriver():
    userdata_dir = 'D:\\\\UserData'
    options = webdriver.ChromeOptions()
    options.add_argument('--user-data-dir=' + userdata_dir)
    #options.add_argument('--headless')
    #options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)

def clickAndWait(driver, element):
    element.click()
    getElement(driver, "//*")

def getPage(driver, url):
    retry = 3
    while True:
        if retry == 0:
            break
        try:
            driver.get(url)
            break
        except Exception as e:
            logInfo('★Exception')
            driver.implicitly_wait(10)
            retry = retry - 1
            continue
    
    getElement(driver, "//*")

def getElement(driver, xpath):
    driver.implicitly_wait(10)
    element = driver.find_element(By.XPATH, xpath)
    time.sleep(1)
    return element

def getPrice(text):
    return int(text.replace('¥','').replace(',',''))

def getDateFromJpFormat(text):
    return text.replace('年','/').replace('月','/').replace('日','')

def getMercariItem(driver, logger, page_edit):

    item = MercariItem()
    itemDir = os.getcwd() + '\\temp'

    # 商品画像
    logger.info('　　商品画像')
    resetFolder(itemDir)
    item.商品画像 = []
    tags_wk = page_edit.find_elements(By.XPATH, '//div[contains(@data-testid, "image-list-item")]')
    imgCounter = 0
    for tag_wk in tags_wk:
        imgCounter = imgCounter + 1
        imgElem = tag_wk.find_element(By.XPATH, 'div/div//img')
        imgData = imgElem.get_attribute('src')
        fileFullPath = '{}\\{:0>2}.jpg'.format(itemDir, imgCounter)
        with open(fileFullPath, "wb") as f:
            f.write(base64.b64decode(imgData.split('base64,')[1]))
        item.商品画像.append(fileFullPath)
    driver.implicitly_wait(10)

    # カテゴリー1～3
    logger.info('　　カテゴリー1～3')
    tag_wk = page_edit.find_element(By.XPATH, '//div[@class="merBreadcrumbList"]')
    tags_wk = tag_wk.find_elements(By.XPATH, 'div')
    item.カテゴリー1 = tags_wk[0].text
    item.カテゴリー2 = tags_wk[1].text
    item.カテゴリー3 = tags_wk[2].text

    # サイズ
    if item.カテゴリー2 != "アクセサリー":
        element = getElement(driver, '//*[@id="main"]//select[@name="size"]')
        if element is not None:
            item.サイズ = element.get_attribute('selectedIndex')

    # 商品の状態
    logger.info('　　商品の状態')
    tag_wk = page_edit.find_element(By.XPATH, '//select[@name="itemCondition"]')
    item.商品の状態 = tag_wk.get_attribute('selectedIndex')

    # 商品名
    logger.info('　　商品名')
    tag_wk = page_edit.find_element(By.XPATH, '//input[@name="name"]')
    item.商品名 = tag_wk.get_attribute('value')

    # 商品の説明
    logger.info('　　商品の説明')
    tag_wk = page_edit.find_element(By.XPATH, '//textarea[@name="description"]')
    item.商品の説明 = tag_wk.get_attribute('value')

    # 配送料の負担
    #element = page_edit.find_element(By.XPATH, '/form/section[4]//div[@class=\"mer-select\"]/select')
    #item.配送料の負担 = element.get_attribute('selectedIndex')

    # 配送の方法
    #element = page_edit.find_element(By.XPATH, '/form/section[4]//div[@data-testid=\"shipping-method-link\"]/p')
    #item.配送の方法 = element.text

    # 発送元の地域
    #element = page_edit.find_element(By.XPATH, '/form/section[4]/mer-select[1]//div[@class=\"mer-select\"]/select')
    #item.発送元の地域 = element.get_attribute('selectedIndex')

    # 発送までの日数
    #element = page_edit.find_element(By.XPATH, '/form/section[4]/mer-select[2]//div[@class=\"mer-select\"]/select')
    #item.発送までの日数 = element.get_attribute('selectedIndex')

    # 現在価格
    logger.info('　　現在価格')
    tag_wk = page_edit.find_element(By.XPATH, '//input[@name="price"]')
    item.現在価格 = tag_wk.get_attribute('value')

    return item

def setMercariItem(driver, item, logger, page_create):

    # 商品画像
    logger.info('　　商品画像')
    tag_wk = page_create.find_element(By.XPATH, '//input[@data-testid="photo-upload"]')
    tag_wk.send_keys('\n'.join(item.商品画像))

    # カテゴリー1～3
    tag_wk = page_create.find_element(By.XPATH, '//a[@href="/sell/categories"]')
    clickAndWait(driver, tag_wk)
    logger.info('　　カテゴリー1')
    selectCategory(driver, item.カテゴリー1)
    logger.info('　　カテゴリー2')
    selectCategory(driver, item.カテゴリー2)
    logger.info('　　カテゴリー3')
    selectCategory(driver, item.カテゴリー3)

    page_create = getElement(driver, '//*[@id="main"]')

    # サイズ
    if item.カテゴリー2 != "アクセサリー":
        logger.info('　　サイズ')
        tag_wk = page_create.find_element(By.XPATH, '//select[@name="size"]')
        if tag_wk is not None:
            selem = Select(tag_wk)
            selem.select_by_index(item.サイズ)

    # 商品の状態
    logger.info('　　商品の状態')
    tag_wk = page_create.find_element(By.XPATH, '//select[@name="itemCondition"]')
    if tag_wk is not None:
        selem = Select(tag_wk)
        selem.select_by_index(item.商品の状態)

    # 商品名
    logger.info('　　商品名')
    tag_wk = page_create.find_element(By.XPATH, '//input[@name="name"]')
    tag_wk.send_keys(item.商品名)

    # 商品の説明
    logger.info('　　商品の説明')
    tag_wk = page_create.find_element(By.XPATH, '//textarea[@name="description"]')
    tag_wk.send_keys(item.商品の説明)

    # 現在価格
    logger.info('　　現在価格')
    tag_wk = page_create.find_element(By.XPATH, '//input[@name="price"]')
    tag_wk.send_keys(item.現在価格)

    return page_create

def selectCategory(driver, category):
    tag_main = getElement(driver, '//*[@id="main"]')
    a_tags = tag_main.find_elements(By.XPATH, '//a[contains(@data-location, "listing_category_select")]')
    for a_tag in a_tags:
        if a_tag.text == category:
            clickAndWait(driver, a_tag)
            break

def resetFolder(path):
    shutil.rmtree(path)
    os.makedirs(path)

def sleepMilliSec(msec):
    # タイマー精度を1msec単位にする
    windll.winmm.timeBeginPeriod(1)

    # Sleep
    time.sleep(msec)

    # タイマー精度を戻す
    windll.winmm.timeEndPeriod(1)