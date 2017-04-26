#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author: kakakaya, Date: Thu Apr 27 02:59:00 2017
# from pprint import pprint as p
from random import choice
import json
import schedule
from mastodon import Mastodon


def make_credential(user_id, user_pw, api_base_url):
    Mastodon.create_app(
        "yurika-ramen",
        to_file="client.secret",
        api_base_url=api_base_url
    )
    m = Mastodon(client_id="client.secret", api_base_url=api_base_url)
    m.log_in(user_id, user_pw, to_file="user.secret")
    return m


def eat_ramen(mastodon_client, messages):
    print(choice(messages))


def main():
    with open("config.json") as f:
        config = json.load(f)

    mastodon = make_credential(config["user_id"], config["user_pw"], config["api_base_url"])

    schedule.every().day.at("09:00").do(eat_ramen, mastodon_client=mastodon, messages=config["morning_messages"])
    schedule.every().day.at("12:30").do(eat_ramen, mastodon_client=mastodon, messages=config["noon_messages"])
    schedule.every().day.at("19:00").do(eat_ramen, mastodon_client=mastodon, messages=config["evenenig_messages"])
    schedule.every().day.at("01:30").do(eat_ramen, mastodon_client=mastodon, messages=config["midnight_messages"])


if __name__ == "__main__":
    main()
