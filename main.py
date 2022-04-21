import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome import service as cs
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from bs4 import BeautifulSoup
import cv2
import tempfile
import requests
from requests.adapters import HTTPAdapter
import sys


# 参考: https://hato.yokohama/scraping_sbi_investment/
def login(user_id: str, user_password: str, driver_path: str):
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


# https://qiita.com/SKYS/items/cbde3775e2143cad7455
def imwrite(filename, img, params=None):
    try:
        ext = os.path.splitext(filename)[1]
        result, n = cv2.imencode(ext, img, params)

        if result:
            while True:
                with open(filename, mode='w+b') as f:
                    n.tofile(f)
                if os.path.exists(filename):
                    break
                print('File not exists!!! Retry!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


# Web上のファイルを直接cv2.imreadで読み込む
# 参考: https://qiita.com/lt900ed/items/891e162a5a1091bae912
def imread_web(url: str):
    # 画像をリクエストする
    headers_dic = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'}
    s = requests.Session()
    s.mount(url, HTTPAdapter(max_retries=5))
    res = s.get(url, headers=headers_dic)

    # res = requests.get(url, headers=headers_dic)
    img = None
    # Tempfileを作成して即読み込む
    fp = tempfile.NamedTemporaryFile(dir='./', delete=False)
    fp.write(res.content)
    fp.close()
    img = cv2.imread(fp.name)
    os.remove(fp.name)
    return img


# img2にimg1の透かしがない部分をマージして，マージ後のimg1を返す
def merge_photos(offset_x: int, offset_y: int, max_x: int, max_y: int, width: int, img1, img2):
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


def process_one_photo(driver, name: str, url: str, page: int, max_page: int):
    img1 = None
    img2 = None
    output_dir = f'./output/{name}/'
    os.makedirs(output_dir, exist_ok=True)

    if driver is not None:
        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        # 1枚目の写真
        img_tag = soup.select_one('img[class="viewer-move"]')
        photo_number = img_tag['src'].split('.jpg')[0].split(')/')[1].replace('/', '-')
        # print(img_tag['src'])

        if '-02.' in img_tag['src']:
            img2 = imread_web(img_tag['src'])
        else:
            img1 = imread_web(img_tag['src'])

        # 透かしをずらす
        driver.find_element(by=By.CLASS_NAME, value='editLogoBtn').click()

        # ID指定したページ上の要素が読み込まれるまで待機（10秒でタイムアウト判定）
        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'viewer-move')))

        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        # 2枚目の写真
        img_tag = soup.select_one('img[class="viewer-move"]')
        # print(img_tag['src'])
        if '-02.' in img_tag['src']:
            img2 = imread_web(img_tag['src'])
        else:
            img1 = imread_web(img_tag['src'])
    else:
        photo_number = '1-2'
        output_dir = './tmp/'
        img1 = cv2.imread('./tmp/1.jpg')
        img2 = cv2.imread('./tmp/2.jpg')

    # 画像サイズ取得
    height, width, channels = img1.shape[:3]
    # print(f'width: {str(width)}, height: {str(height)}')

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
    imwrite(f'{output_dir}{photo_number}.jpg', img1)

    if driver is not None:
        # disabled="disabled"という属性がついている場合は次の写真はない
        # Noneが返ってくる場合はdisabled="disabled"はないので次の写真がある
        if driver.find_element(by=By.CLASS_NAME, value='photosNext').get_attribute('disabled') is None:
            # 次の写真に遷移
            driver.find_element(by=By.CLASS_NAME, value='photosNext').click()
            # ID指定したページ上の要素が読み込まれるまで待機（10秒でタイムアウト判定）
            WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'viewer-move')))
            # 再帰処理
            process_one_photo(driver, name, url, page, max_page)
        else:
            # # 写真詳細表示を閉じる
            # driver.find_element(by=By.CLASS_NAME, value='close').click()
            page += 1
            if page <= max_page:
                if '?page=' in url:
                    url = url.split('?page=')[0]
                next_url = f'{url}?page={str(page)}'
                print(f'next_url: {next_url}')
                get_photo_list(driver, name, next_url)
    return


def get_photo_list(driver, name: str, url: str):
    max_page = 0
    if driver is not None:
        # 写真一覧ページへ遷移
        driver.get(url)

        # ID指定したページ上の要素が読み込まれるまで待機（10秒でタイムアウト判定）
        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'info')))

        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        max_page = int(soup.select_one('div[class="info"]').text.split('ページ中')[0])

        # 1枚目の写真を拡大
        driver.find_element(by=By.CLASS_NAME, value='wholeImage').click()

        # ID指定したページ上の要素が読み込まれるまで待機（10秒でタイムアウト判定）
        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'viewer-move')))

    # 写真を1枚ずつ順番に辿って処理する
    page = 1
    if 'page=' in url:
        page = int(url.split('page=')[1])
    process_one_photo(driver, name, url, page, max_page)


def input_urls():
    file_name = 'input_urls.txt'
    if os.path.exists(file_name):
        with open(file_name, 'r', errors='replace', encoding="utf_8") as file:
            line_list = file.readlines()
    else:
        line_list = None

    return line_list


def main():
    # 参考: https://algorithm.joho.info/programming/python/maximum-recursion-depth-exceeded-while-calling-a-python-object/
    sys.setrecursionlimit(10000)
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

    line_count = 0

    line_list = input_urls()
    for line in line_list:
        line_count += 1
        name = line.split(',')[0]
        url = line.split(',')[1].replace('\n', '')
        print(line_count, '/', len(line_list))

        get_photo_list(driver, name, url)


if __name__ == '__main__':
    main()
