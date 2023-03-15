import config
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)
import urllib.parse
import json
import requests
import random

app = Flask(__name__)

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)
    
def Budget_to_Code(budget):
    budget = int(budget)
    if budget <= 500:
        code = "B009"
    elif 500<budget<=1000:
        code = "B010"
    elif 1000<budget<=1500:
        code = "B011"
    elif 1500<budget<=2000:
        code = "B001"
    elif 2000<budget<=3000:
        code = "B002"
    elif 3000<budget<=4000:
        code = "B003"
    elif 4000<budget<=5000:
        code = "B008"
    elif 5000<budget<=7000:
        code = "B004"
    elif 7000<budget<=10000:
        code = "B005"
    elif 10000<budget<=15000:
        code = "B006"
    elif 15000<budget<=20000:
        code = "B012"
    elif 20000<budget<=30000:
        code = "B013"
    elif budget>=30000:
        code = "B014"
    return code


    
def RailAPI(station, pref):
    station_url =urllib.parse.quote(station)
    pref_url =urllib.parse.quote(pref)
    api='http://express.heartrails.com/api/json?method=getStations&name={station_name}&prefecture={pref_name}'
    url=api.format(station_name=station_url, pref_name=pref_url)
    response=requests.get(url)
    result_list = json.loads(response.text)['response']['station']
    lng=result_list[0]['x']
    lat=result_list[0]['y']
    return lat, lng

def HotpepperAPI(lat, lng, free_drink=0, code=None):
    api_key="" #APIキー 
    if code:
        api = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/?" \
                "key={key}&lat={lat}&lng={lng}&budget={code}&free_drink={free_drink}&range=3&count=200&order=1&format=json"
    else:
        api = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/?" \
                "key={key}&lat={lat}&lng={lng}&free_drink={free_drink}&range=3&count=200&order=1&format=json"
    url=api.format(key=api_key,lat=lat, lng=lng, code=code, free_drink=free_drink)
    response = requests.get(url)
    result_list = json.loads(response.text)['results']['shop']
    shop_datas=[]
    for shop_data in result_list:
        shop_datas.append([shop_data["name"],shop_data["address"],shop_data["urls"]['pc'],shop_data["free_drink"], shop_data["budget"]['average'],shop_data["open"]])
    shop_datas = random.sample(shop_datas, 3)
    return shop_datas


@app.route("/callback", methods=['POST'])
def callback():
    # 署名の検証
    signature = request.headers['X-Line-Signature']
 
   
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
 

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
 
    return 'OK'




@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #テキストメッセージを取得
    text = event.message.text.split()
    if len(text) == 4:
        pref = text[0]
        station = text[1]
        budget = text[2]
        drink = 1
        
        #予算のコード変換
        budget = Budget_to_Code(budget)
        #apiで検索
        lat, lng = RailAPI(station, pref)
        shop_datas = HotpepperAPI(lat, lng, free_drink=drink, code=budget)
        
    elif len(text) == 3:
        pref = text[0]
        station = text[1]
        budget= text[2]
        
        budget = Budget_to_Code(budget)
        lat, lng = RailAPI(station, pref)
        shop_datas = HotpepperAPI(lat, lng, code=budget)
        
    elif len(text) == 2:
        pref = text[0]
        station = text[1]
        
        lat, lng = RailAPI(station, pref)
        shop_datas = HotpepperAPI(lat, lng)
    else:
        #形式に合っていない場合はエラー
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="正しい形式で入力してください")
        )
        return
    
    shop1 = shop_datas[0]
    shop2 = shop_datas[1]
    shop3 = shop_datas[2]    
    
    #店舗情報を返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"{shop1[0]}\n住所:{shop1[1]}\nURL:{shop1[2]}\n{shop2[0]}\n住所:{shop2[1]}\nURL:{shop2[2]}\n{shop3[0]}\n住所:{shop3[1]}\nURL:{shop3[2]}\n")
    )
