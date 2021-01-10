# -*- coding: utf-8 -*-

import re
import json
import requests
from html.parser import HTMLParser

'''
浜松市コロナサイトのお知らせ部分からnews.jsonを作成する
[浜松市コロナサイト](https://www.city.hamamatsu.shizuoka.jp/koho2/emergency/korona.html)

<div class="outline">
    <ul>
        <li>6月2日
        <ul>
            <li>新型コロナウイルスに関するPCR検査実施状況（6月2日現在）　<strong>2月14日～6月2</strong><strong>日　979件</strong> </li>
            <li><a href="/koho2/emergency/korona_event2006.html">イベント開催中止・延期</a> </li>
        </ul>
        </li>
        <li>6月1日
        <ul>
            <li><a href="/koho2/emergency/korona_shisetsu.html">公共施設の状況について</a> </li>
        </ul>
        </li>
    </ul>
</div>
このDOM要素を以下のJSONに変換する
{
  "newsItems": [
    {
      "date": "2020\/04\/03",
      "url": "https://www.city.hamamatsu.shizuoka.jp/koho2/emergency/20200403_1.html",
      "text": "新型コロナウイルス感染症による患者確認について【3例目】"
    },
  ]
}
'''

class NewsParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.BASE_URL = 'https://www.city.hamamatsu.shizuoka.jp'
        self.inContents = False
        self.inDay = False
        self.ulInDay = False
        self.listInDay = False
        self.link = False
        self.news = []
        self.currentDate = ''
        self.supplement = ''
        self.starttag = ''
        self.endtag = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.starttag = tag
        # <div class="outline">
        if tag == "div" and "class" in attrs and attrs['class'] == "outline":
            self.inContents = True
            return
        # <li>x月y日
        if tag == "li" and self.inContents and not self.inDay:
            self.inDay = True
            return
        # <li>x月y日<ul>
        if tag == "ul" and self.inDay:
            self.ulInDay = True
            return
        # <li>x月y日<ul><li>
        if tag == "li" and self.ulInDay:
            self.listInDay = True
            return
        # <li>x月y日<ul><li><a href="xxxx.html">yyyyyyyy</a>
        if tag == "a" and self.listInDay:
            self.link = True
            if attrs["href"].startswith("http"):
                self.news.append({"date": self.currentDate,"url": attrs["href"]})
            else:
                self.news.append({"date": self.currentDate,"url": self.BASE_URL + attrs["href"]})
            return


    def handle_endtag(self, tag):
        self.endtag = tag
        if tag == "a" and self.link:
            self.link = False
            return
        if tag == "li" and self.listInDay:
            self.listInDay = False
            return
        if tag == "ul" and self.ulInDay:
            self.ulInDay = False
            return
        if tag == "li" and self.inDay:
            self.inDay = False
            return
        if tag == "div" and self.inContents:
            self.inContents = False
            return

    def handle_data(self, data):
        if self.listInDay and not self.link:
            data = data.strip().rstrip("／")
            if data and self.lasttag == 'li':
               self.news.append({"date": self.currentDate,"url":"","text": data})
               return
            if data:
               text = self.news[-1].get("text")
               self.news[-1].update({"text": text + data.strip()})
               return
        if self.link:
            self.news[-1].update({"text": data.strip() + self.supplement})
            return
        if self.inDay and not self.ulInDay:
            data = data.strip()
            if data:
                m = re.match(r'([0-9]{1,2})月([0-9]{1,2})日', data)
                if m:
                    month, day = m.groups()
                    self.currentDate = "2021/{}/{}".format(month.zfill(2),day.zfill(2))
                else:
                    m = re.match(r'([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日', data)
                    year, month, day = m.groups()
                    self.currentDate = "{}/{}/{}".format(year, month.zfill(2),day.zfill(2))
            return

def main():
    response = requests.get('https://www.city.hamamatsu.shizuoka.jp/koho2/emergency/korona.html')
    response.encoding = response.apparent_encoding
    parser = NewsParser()
    parser.feed(response.text)
    parser.close()

    print(json.dumps({"newsItems": parser.news}, indent=2, ensure_ascii=False))
if __name__ == '__main__':
    main()
