#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author: kakakaya, Date: Thu Apr 27 02:59:00 2017
# from pprint import pprint as p
import logging
from random import choice, random
import schedule
from mastodon import Mastodon
import time
import json
import requests


def make_credential(user_id, user_pw, api_base_url):
    Mastodon.create_app(
        "yurika-ramen", to_file="client.secret", api_base_url=api_base_url)
    m = Mastodon(client_id="client.secret", api_base_url=api_base_url)
    m.log_in(user_id, user_pw, to_file="user.secret")
    return m


def get_ramen(config):
    keyid = config["gurunavi_keyid"]
    prefs = requests.get(
        "https://api.gnavi.co.jp/master/PrefSearchAPI/20150630/",
        params={"keyid": keyid,
                "format": "json"}).json()["pref"]

    # 今回の県を選ぶ
    pref = choice(prefs)
    res = requests.get("http://api.gnavi.co.jp/RestSearchAPI/20150630/",
                       params={
                           "keyid": keyid,
                           "category_s": "RSFST08008",
                           "format": "json",
                           "pref": pref["pref_code"],
                           "hit_per_page": 100
                       })
    if not res.ok:
        # Bad result; skip this.
        return False, {}

    else:
        rests = res.json()['rest']
        if type(rests) is dict:
            rest = rests
        elif type(rests) is list:
            rest = choice(rests)
        else:
            print("Unknown type of rests: " + str(type(rests)))
            return False, {}

        if not (rest["pr"] and rest["pr"]["pr_short"]):
            return False, {}

        else:
            return True, rest


def eat_ramen(config, mastodon_client):
    ok, ramen = get_ramen(config)
    if not ok:
        return False, False
    # 正常系
    image_ids = []
    print(ramen["image_url"])
    for image_url in [
            ramen["image_url"]["shop_image1"],
            ramen["image_url"]["shop_image2"]
    ]:
        if len(image_url) < 10:
            continue
        image = requests.get(image_url, stream=True)
        if not image.ok:
            continue
        file_location = "/tmp/" + image.url.split("/")[-1]
        with open(file_location, "wb") as f:
            f.write(image.content)
        image_post = mastodon_client.media_post(file_location)
        print(image_post)
        image_ids.append(image_post["id"])

    if ramen["access"]["station"]:
        access = "アクセスは{line}{station}から{walk}分！\n".format(
            line=ramen["access"]["line"],
            station=ramen["access"]["station"],
            walk=ramen["access"]["walk"])
    else:
        access = ""
    message = """
{pref}にある{name}に来たわ！
PRポイントは「{pr}」みたいね。
{access}
URL: {url}""".format(
        pref=ramen["code"]["prefname"],
        name=ramen["name"].strip(),
        access=access,
        url=ramen["url"],
        pr=ramen["pr"]["pr_short"].replace("<BR>", ""))
    return message, image_ids


def post_ramen(mastodon_client, config, messages):
    for _ in range(10):
        message, media_ids = eat_ramen(config, mastodon_client)
        if message:
            break
    message = choice(messages) + message
    time.sleep(30 * 60 * random())
    mastodon_client.status_post(message, media_ids=media_ids)


def main():
    with open("config.json") as f:
        config = json.load(f)

    mastodon = make_credential(config["user_id"], config["user_pw"],
                               config["api_base_url"])

    schedule.every().day.at("09:00").do(
        post_ramen,
        mastodon_client=mastodon,
        config=config,
        messages=config["morning_messages"] + config["everytime_messages"])
    schedule.every().day.at("12:30").do(
        post_ramen,
        mastodon_client=mastodon,
        config=config,
        messages=config["noon_messages"] + config["everytime_messages"])
    schedule.every().day.at("19:00").do(
        post_ramen,
        mastodon_client=mastodon,
        config=config,
        messages=config["evening_messages"] + config["everytime_messages"])
    schedule.every().day.at("01:30").do(
        post_ramen,
        mastodon_client=mastodon,
        config=config,
        messages=config["midnight_messages"] + config["everytime_messages"])

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
