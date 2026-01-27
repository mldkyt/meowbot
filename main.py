import asyncio
import re
from asyncio import sleep
from os import getenv
from random import randint

from dotenv import load_dotenv
from sqlalchemy import select, insert
from sqlalchemy.util import await_only

from database import replied_posts, engine
from misskey import Misskey


def post_waf():
    global misskey

    misskey.post("waf")

async def waf():
    while True:

        a = randint(0, 10000)
        if a == 6767:
            post_waf()

        await sleep(60)

async def reply(debug=False):
    global misskey

    while True:
        notifs = misskey.notifications()

        for i in notifs:

            if i["user"]["isBot"]:
                continue

            # Check reply state
            with engine.begin() as c:
                if (c.execute(select(replied_posts).where(
                    (replied_posts.c.id == str(i["id"])))).fetchone() is not None):
                    continue

            # Handle replying
            if re.match(r"^.*wa+f+.*$", i["note"]["text"].lower()):
                misskey.post(quote_id=i["note"]["id"])
                misskey.post(misskey.mention_users(i["note"]) + " waf", reply_id=i["note"]["id"])

                with engine.begin() as c:
                    c.execute(insert(replied_posts).values(id=str(i["id"])))


        await asyncio.sleep(30)

async def wafin():

    await asyncio.gather(
        waf(),
        reply()
    )


if __name__ == '__main__':

    load_dotenv()

    MISSKEY_INSTANCE = getenv("MISSKEY_INSTANCE")
    MISSKEY_TOKEN = getenv("MISSKEY_TOKEN")

    if not MISSKEY_INSTANCE or not MISSKEY_TOKEN:
        exit(1)

    global misskey

    misskey = Misskey()
    misskey.log_in(MISSKEY_INSTANCE, MISSKEY_TOKEN)

    asyncio.run(wafin())
