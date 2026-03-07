import asyncio
import datetime
import random
import re
from asyncio import sleep
from os import getenv
from random import randint

from dotenv import load_dotenv
from sqlalchemy import select, insert, delete
from sqlalchemy.util import await_only

from database import replied_posts, engine, follows_table
from logger import wafbot_logger
from misskey import Misskey


def post_waf():
    global misskey

    misskey.post(random.choice(["waf", "waff", ":neofox_floof:", ":neofox_pat_floof:", ":neofox_floof_cute:", ":neofox_floof__w_:", ":neofox_floof_happy:"]))

async def waf():
    while True:

        try:
            a = randint(0, 100)
            if a == 67:
                post_waf()

            await sleep(60)
        except Exception:
            wafbot_logger.exception("exception in waf")
            break

async def reply(debug=False):
    global misskey

    while True:
        try:
            notifs = misskey.notifications()

            for i in notifs:
                if i["user"]["isBot"]:
                    continue

                # Check reply state
                with engine.begin() as c:
                    if (c.execute(select(replied_posts).where(
                            (replied_posts.c.id == str(i["note"]["id"])))).fetchone() is not None):
                        continue

                # Handle replying
                if re.match(r"^.*wa+f+.*$", i["note"]["text"].lower()):
                    misskey.post(quote_id=i["note"]["id"])
                    await sleep(0.1)
                    misskey.post(misskey.mention_users(i["note"]) + " " + random.choice(
                        ["waf", "waff", ":neofox_floof:", ":neofox_pat_floof:", ":neofox_floof_cute:",
                         ":neofox_floof__w_:", ":neofox_floof_happy:"]), reply_id=i["note"]["id"])
                    await sleep(0.1)
                    misskey.add_reaction(i["note"], random.choice(
                        [":neofox_floof:", ":neofox_pat_floof:", ":neofox_floof_cute:", ":neofox_floof__w_:",
                         ":neofox_floof_happy:"]))
                    await sleep(0.1)

                    with engine.begin() as c:
                        c.execute(insert(replied_posts).values(id=str(i["note"]["id"])))

                    await sleep(0.5)

            await asyncio.sleep(30)
        except Exception:
            wafbot_logger.exception("exception in reply")
            break

async def timeline():
    while True:
        try:
            posts = misskey.home_tl()

            for post in posts:
                if post["text"] is None:
                    continue

                # Check reply state
                with engine.begin() as c:
                    if (c.execute(select(replied_posts).where(
                            (replied_posts.c.id == str(post["id"])))).fetchone() is not None):
                        continue

                # Handle replying
                if re.match(r"^.*\bwa+f+\b.*$", post["text"].lower()):
                    misskey.post(quote_id=post["id"])
                    await sleep(0.1)
                    misskey.post(misskey.mention_users(post) + " " + random.choice(
                        ["waf", "waff", ":neofox_floof:", ":neofox_pat_floof:", ":neofox_floof_cute:",
                         ":neofox_floof__w_:", ":neofox_floof_happy:"]), reply_id=post["id"])
                    await sleep(0.1)
                    misskey.add_reaction(post, random.choice(
                        [":neofox_floof:", ":neofox_pat_floof:", ":neofox_floof_cute:", ":neofox_floof__w_:",
                         ":neofox_floof_happy:"]))
                    await sleep(0.1)

                    with engine.begin() as c:
                        c.execute(insert(replied_posts).values(id=str(post["id"])))

                    await sleep(0.5)

                await asyncio.sleep(0.5)

            await asyncio.sleep(20)
        except Exception:
            wafbot_logger.exception("exception in timeline")
            break

async def check_followers():
    global misskey

    while True:
        
        try:
            for i in misskey.get_followers():
                try:
                    with engine.begin() as c:
                        a = c.execute(
                            select(follows_table)
                            .where(follows_table.c.id == i["id"])
                        ).fetchone()

                    if a is not None:
                        continue

                    if not i["isFollowing"] and not i["hasPendingFollowRequestFromYou"] and not i["isBlocking"]:
                        print(f"follow {i['name']}")
                        while True:
                            follow = misskey.follow(i["id"])
                            if follow:
                                with engine.begin() as c:
                                    c.execute(insert(follows_table).values(
                                        id=i["id"],
                                        acct=misskey.get_effective_name(i),
                                        followed=datetime.datetime.now())
                                    )
                                break
                            await asyncio.sleep(4)
                except Exception:
                    print("fail to follow", i["name"])
                    break

            with engine.begin() as c:
                a = c.execute(select(follows_table.c.id, follows_table.c.acct)).all()

            for i in a:
                rel = misskey.get_user(i[0])
                if not rel:
                    continue

                if not rel["isFollowed"] and rel["isFollowing"]:
                    print(f"unfollow {i[0]}")
                    try:
                        unfollow_ok = misskey.unfollow(i[0])
                        if unfollow_ok:
                            with engine.begin() as c:
                                c.execute(delete(follows_table).where((follows_table.c.id == i[0])))

                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"failed to unfollow {i[0]}: {str(e)}")
                        pass

            await asyncio.sleep(180)
        except Exception:
            wafbot_logger.exception("error in check_followers")
            break


async def wafin():

    await asyncio.gather(
        waf(),
        reply(),
        timeline(),
        check_followers()
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
