import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome import service as cs
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import cv2
import tempfile
import requests
import sys


def write_html(path, source):
    # Windows向けの変換
    html = source.encode('cp932', "ignore").decode('cp932')
    with open(path, mode='w') as f:
        f.write(html)


# 参考: https://hato.yokohama/scraping_sbi_investment/
def login(user_id, user_password, driver_path):
    options = Options()
    service = cs.Service(executable_path=driver_path)
    # ヘッドレスモード(chromeを表示させないモード)
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options, service=service)
    # 一度設定すると find_element 等の処理時に、
    # 要素が見つかるまで指定時間繰り返し探索するようになります。
    driver.implicitly_wait(10)

    # snapsnapのログインページを開く
    driver.get('https://snapsnap.jp/login')

    # ユーザーIDとパスワード
    input_user_id = driver.find_element(by=By.ID, value='email')
    input_user_id.send_keys(user_id)
    input_user_password = driver.find_element(by=By.ID, value='password')
    input_user_password.send_keys(user_password)

    # ログインボタンをクリック
    driver.find_element(by=By.CLASS_NAME, value='Button').click()

    # 遷移するまで待つ
    time.sleep(2)

    return driver


# Web上のファイルを直接cv2.imreadで読み込む
# 参考: https://qiita.com/lt900ed/items/891e162a5a1091bae912
def imread_web(url):
    # 画像をリクエストする
    res = requests.get(url)
    img = None
    # Tempfileを作成して即読み込む
    fp = tempfile.NamedTemporaryFile(dir='./', delete=False)
    fp.write(res.content)
    fp.close()
    img = cv2.imread(fp.name)
    os.remove(fp.name)
    return img


# img2にimg1の透かしがない部分をマージして，マージ後のimg1を返す
def merge_photos(offset_x, offset_y, max_x, max_y, width, img1, img2):
    for x in range(max_x):
        for y in range(max_y):
            # width*widthのサイズで切り出す
            if x % 3 == 0 and y % 3 == 0 or x % 3 == 2 and y % 3 == 1 or x % 3 == 1 and y % 3 == 2:
                piece_x = offset_x + x * width
                piece_y = offset_y + y * width
                # print(f'piece_x: {piece_x}, piece_y: {piece_y}')
                img2_piece = img2[piece_y:piece_y + width, piece_x:piece_x + width]
                # cv2.imshow('contourimg', img2_piece)
                # cv2.waitKey(0)
                # 切り出した画像をもう1枚の同じ場所に貼る
                img1[piece_y:piece_y + width, piece_x:piece_x + width] = img2_piece
    return img1


def process_one_photo(driver, url, page, max_page):
    img1 = None
    img2 = None
    output_dir = './output/'

    if driver is not None:
        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        # 1枚目の写真
        img_tag = soup.select_one('img[class="viewer-move"]')
        photo_number = img_tag['src'].split('.jpg')[0].split(')/')[1].replace('/', '-')
        print(img_tag['src'])

        if '-02.' in img_tag['src']:
            img2 = imread_web(img_tag['src'])
        else:
            img1 = imread_web(img_tag['src'])

        # 透かしをずらす
        driver.find_element(by=By.CLASS_NAME, value='editLogoBtn').click()

        # 遷移するまで待つ
        time.sleep(2)

        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        # 2枚目の写真
        img_tag = soup.select_one('img[class="viewer-move"]')
        print(img_tag['src'])
        if '-02.' in img_tag['src']:
            img2 = imread_web(img_tag['src'])
        else:
            img1 = imread_web(img_tag['src'])
    else:
        photo_number = '1-2'
        output_dir = './tmp/'
        img1 = cv2.imread('./tmp/1.jpg')
        img2 = cv2.imread('./tmp/2.jpg')
        # photo_number = '3-2'
        # output_dir = './tmp/'
        # img1 = cv2.imread('./tmp/3.jpg')
        # img2 = cv2.imread('./tmp/4.jpg')

    # offset_x = 70
    # offset_y = 0
    # width = 124
    # offset_x2 = offset_x - int(width / 2)
    # offset_y2 = int(width / 2)
    # for x in range(20):
    #     piece_x = offset_x + x * width
    #     cv2.line(img2,
    #              pt1=(piece_x, 0),
    #              pt2=(piece_x, 1350),
    #              color=(255, 255, 255),
    #              thickness=1,
    #              lineType=cv2.LINE_4,
    #              shift=0)
    #
    # for y in range(11):
    #     piece_y = offset_y + y * width
    #     cv2.line(img2,
    #              pt1=(0, piece_y),
    #              pt2=(1800, piece_y),
    #              color=(255, 255, 255),
    #              thickness=1,
    #              lineType=cv2.LINE_4,
    #              shift=0)
    # # cv2.imshow('test', img2)
    # # cv2.waitKey(0)
    # cv2.imwrite('./tmp/2-test.jpg', img2)

    # for x in range(20):
    #     piece_x = offset_x2 + x * width
    #     cv2.line(img2,
    #              pt1=(piece_x, 0),
    #              pt2=(piece_x, 1800),
    #              color=(255, 255, 255),
    #              thickness=1,
    #              lineType=cv2.LINE_4,
    #              shift=0)
    #
    # for y in range(11):
    #     piece_y = offset_y2 + y * width
    #     cv2.line(img2,
    #              pt1=(0, piece_y),
    #              pt2=(1350, piece_y),
    #              color=(255, 255, 255),
    #              thickness=1,
    #              lineType=cv2.LINE_4,
    #              shift=0)
    # # cv2.imshow('test', img2)
    # # cv2.waitKey(0)
    # cv2.imwrite('./tmp/2-test2.jpg', img2)

    # for x in range(20):
    #     piece_x = offset_x + x * width
    #     cv2.line(img1,
    #              pt1=(piece_x, 0),
    #              pt2=(piece_x, 1350),
    #              color=(255, 255, 255),
    #              thickness=1,
    #              lineType=cv2.LINE_4,
    #              shift=0)
    #
    # for y in range(11):
    #     piece_y = offset_y + y * width
    #     cv2.line(img1,
    #              pt1=(0, piece_y),
    #              pt2=(1800, piece_y),
    #              color=(255, 255, 255),
    #              thickness=1,
    #              lineType=cv2.LINE_4,
    #              shift=0)
    # # cv2.imshow('test', img1)
    # # cv2.waitKey(0)
    # cv2.imwrite('./tmp/1-test.jpg', img1)

    # 画像サイズ取得
    height, width, channels = img1.shape[:3]
    print(f'width: {str(width)}, height: {str(height)}')

    # 横画像の場合
    if width == 1800 and height == 1350:
        offset_x1 = 62
        offset_y1 = 24
        area_size = 124
        offset_x2 = offset_x1 - int(area_size / 2)
        offset_y2 = int(area_size / 2)
        img1 = merge_photos(offset_x1, offset_y1, 15, 10, area_size, img1, img2)
        img1 = merge_photos(offset_x2, offset_y2, 15, 10, area_size, img1, img2)
    # 縦画像の場合
    elif width == 1350 and height == 1800:
        offset_x1 = 70
        offset_y1 = 0
        area_size = 123
        offset_x2 = offset_x1 - int(area_size / 2)
        offset_y2 = int(area_size / 2)
        img1 = merge_photos(offset_x1, offset_y1, 10, 15, area_size, img1, img2)
        img1 = merge_photos(offset_x2, offset_y2, 10, 15, area_size, img1, img2)
    else:
        print('Check photo size!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    cv2.imwrite(f'{output_dir}{photo_number}.jpg', img1)

    if driver is not None:
        # disabled="disabled"という属性がついている場合は次の写真はない
        # Noneが返ってくる場合はdisabled="disabled"はないので次の写真がある
        if driver.find_element(by=By.CLASS_NAME, value='photosNext').get_attribute('disabled') is None:
            # 次の写真に遷移
            driver.find_element(by=By.CLASS_NAME, value='photosNext').click()
        else:
            # # 写真詳細表示を閉じる
            # driver.find_element(by=By.CLASS_NAME, value='close').click()
            page += 1
            if page <= max_page:
                next_url = f'{url}?page={str(page)}'
                get_photo_list(driver, next_url)

        # 遷移するまで待つ
        time.sleep(2)
        # 再帰処理
        process_one_photo(driver, url, page, max_page)


def get_photo_list(driver, url):
    max_page = 0
    if driver is not None:
        # 写真一覧ページへ遷移
        driver.get(url)

        # 遷移するまで待つ
        time.sleep(2)

        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        max_page = int(soup.select_one('div[class="info"]').text.split('ページ中')[0])

        # 1枚目の写真を拡大
        driver.find_element(by=By.CLASS_NAME, value='wholeImage').click()

        # 遷移するまで待つ
        time.sleep(2)

    # 写真を1枚ずつ順番に辿って処理する
    process_one_photo(driver, url, 1, max_page)


def main():
    # 参考: https://algorithm.joho.info/programming/python/maximum-recursion-depth-exceeded-while-calling-a-python-object/
    sys.setrecursionlimit(10000)
    url = os.environ.get('URL')
    user_id = os.environ.get('ID')
    user_password = os.environ.get('PASSWORD')
    driver_path = os.environ.get('DRIVER_PATH')
    debug = os.environ.get('DEBUG')
    debug_bool = False
    if debug == 'True':
        debug_bool = True
    if debug_bool:
        driver = None
    else:
        driver = login(user_id, user_password, driver_path)

    get_photo_list(driver, url)

    if not debug_bool:
        time.sleep(10000)


if __name__ == '__main__':
    main()
