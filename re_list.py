import sys, io, os, base64, shutil
from tkinter.messagebox import NO
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import chromedriver_binary
import openpyxl as xl
from datetime import datetime
import common

#--------------------------------------------------
# 実行判定
#--------------------------------------------------
def filter(cells):

    if cells.対象.value is None:
        return common.FilterResult.CONTINUE
    if cells.対象.value == 'end':
        return common.FilterResult.BREAK
    if cells.対象.value != '■':
        return common.FilterResult.CONTINUE
    if cells.商品URL.value is None:
        return common.FilterResult.CONTINUE
        
    return common.FilterResult.NO_FILTER

#----------------------------------------------------------------------------------------------------
# 商品再出品
#----------------------------------------------------------------------------------------------------
def execute(driver, wb, cells, logger):

    商品ID = cells.get商品ID()

    #--------------------------------------------------
    # いいねボタンを押す
    #--------------------------------------------------
#    logger.info('　いいねボタンを押す')
#
#    # 商品詳細ページを表示
#    common.getPage(driver, common.URL_商品詳細ページ + 商品ID)
#    page_view = common.getElement(driver, '//div[@id="item-info"]')
#
#    # いいねボタンを押す
#    tag_wk = page_view.find_element(By.XPATH, '//div[@data-testid="icon-heart-button"]')
#    checked = tag_wk.get_attribute('checked')
#    if checked is None:
#        common.clickAndWait(driver, tag_wk)

    #--------------------------------------------------
    # 旧商品情報を取得
    #--------------------------------------------------
    logger.info('　旧商品情報を取得')

    # 商品編集ページを表示
    common.getPage(driver, common.URL_商品編集ページ + 商品ID)

    # 商品情報の取得
    page_edit = common.getElement(driver, '//*[@id="main"]')
    itemA = common.getMercariItem(driver, logger, page_edit)

    #--------------------------------------------------
    # 旧商品を公開停止
    #--------------------------------------------------
#    logger.info('　旧商品を公開停止')
#
#    # 出品を一時停止する
#    tag_wk = page_edit.find_element(By.XPATH, '//button[@data-testid="suspend-button"]')
#    common.clickAndWait(driver, tag_wk)

    #--------------------------------------------------
    # 新商品の下書きを作成
    #--------------------------------------------------
    logger.info('　新商品の下書きを作成')

    # 商品出品ページを表示
    common.getPage(driver, common.URL_商品出品ページ)
    
    # 商品情報をセット
    page_create = common.getElement(driver, '//*[@id="main"]')
    page_create = common.setMercariItem(driver, itemA, logger, page_create)

    # 下書き保存 → 下書き一覧画面に遷移
    tag_wk = page_create.find_element(By.XPATH, '//button[@data-testid="save-draft"]')
    common.clickAndWait(driver, tag_wk)

    #--------------------------------------------------
    # 新旧商品の一致チェック
    #--------------------------------------------------
    logger.info('　新旧商品の一致チェック')

    # 下書きを開く
    page_dlist = common.getElement(driver, '//*[@id="main"]')
    tag_wk = page_dlist.find_element(By.XPATH, '//a[@data-location="draft_listing:listings:listing_row"]')
    common.clickAndWait(driver, tag_wk)

    # 商品情報の取得
    page_edit = common.getElement(driver, '//*[@id="main"]')
    itemB = common.getMercariItem(driver, logger, page_edit)

    # チェックOKなら出品
    新商品ID = ""
    if itemA.Equals(itemB):
        logger.info('　下書き作成　完了')

#        # 出品
#        logger.info('　新商品を出品')
#        tag_wk = page_edit.find_element(By.XPATH, '//div[@data-testid="list-draft-button"]/button')
#        common.clickAndWait(driver, tag_wk)
#
#        # 新商品IDの取得
#        tag_main = common.getElement(driver, '//*[@id="main"]')
#        tag_wk = tag_main.find_element(By.XPATH, '//a[@data-location="listing_complete:item"]')
#        url = tag_wk.get_attribute('href')
#        新商品ID = url.split('/')[-1]
#
#        # 古い商品の削除
#        logger.info('　旧商品を削除')
#        common.getPage(driver, common.URL_商品編集ページ + 商品ID)
#
#        # 一時停止中（1番上のボタンが"再開"）の場合
#        tag_main = common.getElement(driver, '//*[@id="main"]')
#        tag_wk = tag_main.find_element(By.XPATH, '//button[@data-testid="activate-button"]')
#        if '再開' in tag_wk.text:
#            # 削除ボタンクリック
#            tag_wk = tag_main.find_element(By.XPATH, '//button[@data-testid="delete-button"]')
#            common.clickAndWait(driver, tag_wk)
#            # 確認画面でも削除ボタンクリック
#            tag_wk = tag_main.find_element(By.XPATH, '//div[@data-testid="dialog-action-button"]/button')
#            common.clickAndWait(driver, tag_wk)
#        else:
#            logger.info('　エラー：旧商品が公開停止中でない')
#            return
    else:
        logger.info('　エラー：旧商品と新商品(下書き)に差異あり')
        return

    # 商品リストの更新
    logger.info('　エクセルを更新')
    cells.商品URL.value = common.URL_商品詳細ページ + 新商品ID
    cells.商品名.value = itemA.商品名
    cells.出品日.value = datetime.now().strftime('%Y/%m/%d')
    cells.対象.value = None
    wb.save(common.getItemListFilePath())

#--------------------------------------------------
# メイン処理
#--------------------------------------------------

# ロガーの取得
defaultLogger = common.getDefaultLogger()

# 開始ログ
defaultLogger.info("＝＝＝＝＝　プログラム開始　＝＝＝＝＝")

# エクセルを開く
workbook = xl.load_workbook(common.getItemListFilePath())

# ブラウザを起動
chromeDriver = common.openChromeDriver()

# 行単位処理
common.loopMain(filter, execute, chromeDriver, workbook, defaultLogger)

# ブラウザを閉じる
chromeDriver.close()
chromeDriver.quit()

# エクセルを閉じる
workbook.close()

# 終了ログ
defaultLogger.info("＝＝＝＝＝　プログラム終了　＝＝＝＝＝")
