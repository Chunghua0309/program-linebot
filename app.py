from flask import Flask, request, abort
import requests
from bs4 import BeautifulSoup

# Line Bot SDK v3
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction,
    CarouselColumn,
    CarouselTemplate,
    URIAction
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    PostbackEvent
)
# 建立 Flask 應用
app = Flask(__name__)

# 設定 LINE Bot Token & Secret
configuration = Configuration(access_token='7frhXh1e19q+ndOKuOnq7M/BSfg9mVj5ggEFnwtk1dphEtI/4Ss/9y9ey/5ScXEj0SkKrG5MCmkAYBlXt54g7FPXTY7kenoAiWV5Xo1KbulsX+DOXVdEsjBUMx1NgbXy+yoqukqPkBAn9SUs+/n52wdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('6c769c95cda433561660af945462844b')


@app.route("/callback", methods=['POST'])
def callback():
    # 確保這個請求來自 LINE
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        # 嘗試簽名連線
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


# 監聽文字訊息
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_msg = event.message.text

    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            if "PTT" in user_msg:
                reply_text = get_ptt_hot()
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )

            elif "News" in user_msg:
                reply_template = get_yahoo_news_hot()
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[reply_template]
                    )
                )
            elif user_msg != None:
                reply_template = get_stock_news(user_msg)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[reply_template]
                    )
                )

            else:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="我聽不懂，可以輸入 PTT 或 News 試試看")]
                    )
                )

    except Exception as e:
        app.logger.error(f"LINE API Error: {e}")


# 爬蟲函數：PTT 熱門文章
def get_ptt_hot():
    url = "https://www.ptt.cc/bbs/hotboards.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    }
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")


    # 把前 5 個熱門看板抓出來
    boards = [b.get_text(strip=True) for b in soup.select(".board-title")[:5]]

    return "🔥 PTT 熱門看板：\n" + "\n".join(boards)
# 爬財經(關鍵字可隨意改)新聞
def get_stock_news(word):
    query = word.strip() or "財經快訊"
    url = f'https://www.google.com/search?q={query}&tbm=nws'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    }
    response_google = requests.get(url, headers=headers)
    soup = BeautifulSoup(response_google.text, "html.parser")
    all_google_title = soup.find_all('div',attrs={'class':"n0jPhd ynAwRc MBeuO nDgy9d"})
    all_goole_href = soup.find_all('a', attrs={'class':"WlydOe"})
    
    columns = []

    for a, b in zip(all_google_title[:3], all_goole_href[:3]):
        title_google = a.get_text(strip=True)
        href_google = b['href']
        image_url_init = "https://photos.fife.usercontent.google.com/pw/AP1GczPqrR3bgE3Zo2-8osP1NWOhfy8X_VFWt79wK7bnboveg8J5sn6w5PLuLg=s237-no?authuser=0" # 預設圖片防呆

        google_res = requests.get(href_google, headers=headers, timeout=5)
        google_soup = BeautifulSoup(google_res.text, "html.parser")
        


        columns.append(
            CarouselColumn(
                # clthumbnail_image_url=image_url,
                title=title_google[:10],
                text='閱讀全文請點下方按鈕',
                actions=[
                    URIAction(label="閱讀原文", uri=href_google)
                ]
            )
        )

    carousel_template = CarouselTemplate(columns=columns)

    template_message = TemplateMessage(
        alt_text=query,
        template=carousel_template
    )

    return template_message
    
    


def get_yahoo_news_hot():
    url = "https://tw.news.yahoo.com/"
    image_url_init = "https://photos.fife.usercontent.google.com/pw/AP1GczPqrR3bgE3Zo2-8osP1NWOhfy8X_VFWt79wK7bnboveg8J5sn6w5PLuLg=s237-no?authuser=0" # 預設圖片防呆
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    all_title_news = soup.find_all(
        'a',
        attrs={'class': "D(ib) Ov(h) Whs(nw) C($c-fuji-grey-l) C($c-fuji-blue-1-c):h Td(n) Fz(16px) Tov(e) Fw(700)"}
    )

    columns = []

    for a in all_title_news[:3]:
        title = a.get_text(strip=True)
        href  = a.get('href')
        # 內文的爬蟲
        news_res = requests.get(href, headers=headers, timeout=5)
        news_soup = BeautifulSoup(news_res.text, "html.parser")
        paragraph = news_soup.find_all(
            'p',
            attrs={'class':'mb-module-gap break-words leading-[1.4] text-px20 lg:text-px18 lg:leading-[1.8] text-batcave'},
            limit=5
        )
        # 讀取圖片縮圖
        photo_image = news_soup.find('img', attrs={'class':"rounded-lg"})
        image_url = photo_image['src'] if photo_image else image_url_init
        # 讀取摘要
        summary = "（無法擷取摘要）"
        for p in paragraph:
            text = p.get_text(strip=True)
            if any(k in text for k in ["報導", "記者", "中心／", "新聞網", "FTNN"]):
                continue
            summary = text
            break
        summary_25 = summary[:25] + '....'

        # 建立 Carousel 卡片
        columns.append(
            CarouselColumn(
                thumbnail_image_url=image_url,
                title=title[:10],
                text=summary_25,
                actions=[
                    URIAction(label="閱讀原文", uri=href)
                ]
            )
        )

    carousel_template = CarouselTemplate(columns=columns)

    template_message = TemplateMessage(
        alt_text="Yahoo 熱門新聞",
        template=carousel_template
    )

    return template_message


if __name__ == "__main__":
    app.run(port=5000)
