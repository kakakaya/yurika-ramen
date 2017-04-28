#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author: kakakaya, Date: Thu Apr 27 02:59:00 2017
# from pprint import pprint as p
from random import choice
import schedule
from mastodon import Mastodon
import json
import requests


def make_credential(user_id, user_pw, api_base_url):
    Mastodon.create_app(
        "yurika-ramen", to_file="client.secret", api_base_url=api_base_url)
    m = Mastodon(client_id="client.secret", api_base_url=api_base_url)
    m.log_in(user_id, user_pw, to_file="user.secret")
    return m


def eat_ramen(mastodon_client, config, messages):
    keyid = config["gurunavi_keyid"]
    prefs = requests.get(
        "https://api.gnavi.co.jp/master/PrefSearchAPI/20150630/",
        params={"keyid": keyid,
                "format": "json"}).json()["pref"]

    # 今回の県を選ぶ
    pref = choice(prefs)
    res = requests.get(
        "http://api.gnavi.co.jp/RestSearchAPI/20150630/",
        params={
            "keyid": keyid,
            "freeword": "ラーメン",
            "format": "json",
            "pref": pref["pref_code"],
            "hit_per_page": 100
        })
    if not res.ok:
        message = choice(messages)+"……と思ったけど、ファンがいるから退散するわ！"
    else:
        rests = res.json()['rest']
        if type(rests) is dict:
            rest = rests
        elif type(rests) is list:
            rest = choice(rests)
        else:
            print("Unknown type of rests: "+str(type(rests)))
            return
        message = choice(messages)

        image_urls = []
        for image_url in [rest["image_url"]["shop_image1"], rest["image_url"]["shop_image2"]]:
            if len(image_url) < 10:
                continue
            image = requests.get(image_url, stream=True)
            if not image.ok:
                continue
            file_location = "/tmp/"+image.url.split("/")[-1]
            with open(file_location, "wb") as f:
                f.write(image.content)
            image_post = mastodon_client.media_post(file_location)
            image_urls.append(image_post["text_url"])

        image_urls = " ".join(image_urls)
        message += """
{pref}にある{name}に来たわ！
PRポイントは「{pr}」みたいね。

アクセスは{line}{station}から{walk}分！
URL: {url} {image_url}""".format(
            pref=rest["code"]["prefname"],
            name=rest["name"].strip(),
            line=rest["access"]["line"],
            station=rest["access"]["station"],
            walk=rest["access"]["walk"],
            url=rest["url"],
            image_url=image_urls,
            pr=rest["pr"]["pr_short"]
        )

    # print(message)
    mastodon_client.toot(message)


def main():
    with open("config.json") as f:
        config = json.load(f)

    mastodon = make_credential(config["user_id"], config["user_pw"],
                               config["api_base_url"])

    schedule.every().day.at("09:00").do(eat_ramen,
                                        mastodon_client=mastodon,
                                        config=config,
                                        messages=config["morning_messages"]+config["everytime_messages"])
    schedule.every().day.at("12:30").do(eat_ramen,
                                        mastodon_client=mastodon,
                                        config=config,
                                        messages=config["noon_messages"]+config["everytime_messages"])
    schedule.every().day.at("19:00").do(eat_ramen,
                                        mastodon_client=mastodon,
                                        config=config,
                                        messages=config["evenenig_messages"]+config["everytime_messages"])
    schedule.every().day.at("01:30").do(eat_ramen,
                                        mastodon_client=mastodon,
                                        config=config,
                                        messages=config["midnight_messages"]+config["everytime_messages"])


if __name__ == "__main__":
    main()
