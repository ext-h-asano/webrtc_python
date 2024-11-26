from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import argparse
import time
#引数のパーサーを作成
parser = argparse.ArgumentParser(description="幅と高さ")

parser.add_argument("width", help="width")
parser.add_argument("height", help="height")

args = parser.parse_args()

## geckodriverのパス指定
executable_path="/snap/bin/geckodriver"

options = Options()

### ユーザーエージェントの設定
user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0'
options.add_argument('--user-agent=' + user_agent)

### ブラウザの言語設定を日本語にする
options.set_preference("intl.accept_languages", "jpn")
options.set_preference("media.navigator.permission.disabled", True)

### その他optionsの指定
options.add_argument('--no-sandbox')  ## Sandboxの外でプロセスを動作させる
options.add_argument('--disable-dev-shm-usage')  ## /dev/shmパーティションの使用を禁止し、パーティションが小さすぎることによる、クラッシュを回避する。
options.add_argument('--headless')
# options.set_preference("media.navigator.streams.fake", True)

## driverの作成
service = FirefoxService(executable_path=executable_path)
driver = webdriver.Firefox(options=options,service=service)

driver.get("https://ext-h-asano.github.io/dev_answer_html/")
driver.execute_script("window.testlocalId = 'test'; window.testremoteId = 'test';")
driver.execute_script(f"window.v4l2width = '{args.width}'; window.v4l2height = '{args.height}';")
result = driver.execute_script("return window.testlocalId;")
print(result)

try:
 while True:
  time.sleep(1)
except KeyboardInterrupt:
 driver.quit()