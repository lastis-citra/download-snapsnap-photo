# download-snapsnap-photo
## 利用方法

`input_urls.txt`に画像一覧のURLを入力する

例:
```commandline
https://snapsnap.jp/events/xxxx/albums/xxxx/photos
```

## 透かしが残る場合

2枚の画像を`tmp`フォルダに入れ，環境変数で`DEBUG=True`を渡す

`process_one_photo`で上記の2枚の画像名を指定して実行する

gridが斜め一列に透かしあり，なしになるようオフセットを調整する
