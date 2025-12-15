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


# デバッグ用に画像にグリッド線を引く
def write_grid(filename, offset_x, offset_y, area_size, postfix):
    img = cv2.imread(f'./tmp/{filename}.jpg')
    height, width = img.shape[:2]

    # 横線を引く：offset_yからheightの手前までarea_sizeおきに白い(BGRすべて255)横線を引く
    img[offset_y:height:area_size, :, :] = 0
    # 縦線を引く：offset_xからwidthの手前までarea_sizeおきに白い(BGRすべて255)縦線を引く
    img[:, offset_x:width:area_size, :] = 0

    cv2.imwrite(f'./tmp/{filename}_{postfix}.jpg', img)


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
#  0  1  2  3  4  5（offset_y = 0の場合，この行は存在しない
#  6  7  8  9 10 11
# 12 13 14 15 16 17
# 0～5はオフセット部分なので，ここは1枚目がそのまま残る（つまり上端まで透かしがある場合，offset_yは0にする必要がある）
def merge_photos(offset_x: int, offset_y: int, max_x: int, max_y: int, width: int, img1, img2, set = 1):
    if set == 1:
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
    elif set == 2:
        for x in range(max_x + 1):
            for y in range(max_y + 1):
                # width*widthのサイズで切り出す
                if x % 3 == 1 and y % 3 == 1 or x % 3 == 2 and y % 3 == 0 or x % 3 == 0 and y % 3 == 2:
                    piece_x = offset_x + (x - 1) * width
                    piece_y = offset_y + (y - 1) * width
                    if piece_x < 0:
                        piece_x = 0
                    if piece_y < 0:
                        piece_y = 0
                    # print(f'piece_x: {piece_x}, piece_y: {piece_y}')
                    img2_piece = img2[piece_y:piece_y + width, piece_x:piece_x + width]
                    # cv2.imshow('contourimg', img2_piece)
                    # cv2.waitKey(0)
                    # 切り出した画像をもう1枚の同じ場所に貼る
                    img1[piece_y:piece_y + width, piece_x:piece_x + width] = img2_piece
    elif set == 3:
        for x in range(max_x):
            for y in range(max_y):
                # width*widthのサイズで切り出す
                if x % 6 == 4 and y % 3 == 0:
                    piece_x = offset_x + x * width
                    piece_y = offset_y + y * width
                    # print(f'piece_x: {piece_x}, piece_y: {piece_y}')
                    img2_piece = img2[piece_y:piece_y + width, piece_x:piece_x + width]
                    # cv2.imshow('contourimg', img2_piece)
                    # cv2.waitKey(0)
                    # 切り出した画像をもう1枚の同じ場所に貼る
                    img1[piece_y:piece_y + width, piece_x:piece_x + width] = img2_piece
    return img1


def process_one_photo(driver, name: str, url: str, page: int, max_page: int, whole_image_elements, count: int):
    img1 = None
    img2 = None
    img3 = None
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
        photo_number = '9-2'
        output_dir = './tmp/'
        img1 = cv2.imread('./tmp/9.jpg')
        img2 = cv2.imread('./tmp/10.jpg')
        img3 = cv2.imread('./tmp/black.jpg')

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
    # 横画像の場合
    elif width == 1800 and round(height / 100) * 100 == 1200:
        offset_x1 = 0
        offset_y1 = 0
        area_size = 124
        # write_grid('7', offset_x1, offset_y1, area_size, 'grid')
        # write_grid('8', offset_x1, offset_y1, area_size, 'grid')
        offset_x2 = offset_x1 - int(area_size / 2)
        offset_y2 = int(area_size / 2)
        img1 = merge_photos(offset_x1, offset_y1, 15, 10, area_size, img1, img2)
        img1 = merge_photos(offset_x2, offset_y2, 15, 10, area_size, img1, img2)
    elif round(width / 100) * 100 == 1200 and height == 1800:
        offset_x1 = 124
        offset_y1 = 50
        area_size = 124
        # write_grid('9', offset_x1, offset_y1, area_size, 'grid')
        # write_grid('10', offset_x1, offset_y1, area_size, 'grid')
        offset_x2 = offset_x1 - int(area_size / 2)
        offset_y2 = int(area_size / 2)
        # write_grid('9', offset_x2, offset_y2, int(area_size / 2), 'grid2')
        # write_grid('10', offset_x2, offset_y2, int(area_size / 2), 'grid2')
        img2_1 = img2.copy()
        img4 = merge_photos(offset_x1, offset_y1, 10, 15, area_size, img2, img1, 2)
        img4 = merge_photos(offset_x2, offset_y2, 10, 15, area_size, img4, img1, 2)
        img2 = merge_photos(offset_x2, offset_y2, 30, 2, int(area_size / 2), img4, img2_1, 3)
        img1 = img2.copy()
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
            process_one_photo(driver, name, url, page, max_page, whole_image_elements, count + 1)
        else:
            print('count: ' + str(count) + ', len(whole_image_elements): ' + str(len(whole_image_elements)))
            # uchinokoのURLの場合，NEXTで辿ってもすべてを表示しきれないので，まだ写真が残っていればそこから再帰処理を再開する
            if len(whole_image_elements) - 1 > count:
                # 写真詳細表示を閉じる
                driver.find_element(by=By.CLASS_NAME, value='close').click()
                whole_image_elements[count + 1].click()
                # ID指定したページ上の要素が読み込まれるまで待機（10秒でタイムアウト判定）
                WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'viewer-move')))
                process_one_photo(driver, name, url, page, max_page, whole_image_elements, count + 1)
            else:
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
        element = soup.select_one('div[class="info"]')
        max_page = 1
        if element:
            max_page = int(element.text.split('ページ中')[0])

        # 1枚目の写真を拡大
        # driver.find_element(by=By.CLASS_NAME, value='wholeImage').click()
        whole_image_elements = driver.find_elements(by=By.CLASS_NAME, value='wholeImage')
        whole_image_elements[0].click()

        # ID指定したページ上の要素が読み込まれるまで待機（10秒でタイムアウト判定）
        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'viewer-move')))

        # 写真を1枚ずつ順番に辿って処理する
        page = 1
        if 'page=' in url:
            page = int(url.split('page=')[1])
        process_one_photo(driver, name, url, page, max_page, whole_image_elements, 0)


def input_urls():
    file_name = 'input_urls.conf'
    line_list2 = []

    if os.path.exists(file_name):
        with open(file_name, 'r', errors='replace', encoding="utf_8") as file:
            line_list = file.readlines()
    else:
        line_list = None

    for line in line_list:
        if line.startswith(';'):
            continue
        line_list2.append(line)

    return line_list2


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
