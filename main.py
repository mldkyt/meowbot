import asyncio
import datetime
import random
import re
import typing
from asyncio import sleep
from os import getenv
from random import randint

import bs4
import requests
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from mastodon import Mastodon
from mastodon.return_types import StatusMention
from sqlalchemy import delete, insert, select

from database import engine, follows_table, replied_posts
from logger import catbot_logger

mastodon = Mastodon(access_token="data/pytooter_usercred.secret")
me = mastodon.me()

# borrowed from https://stackoverflow.com/questions/30337528/make-beautifulsoup-handle-line-breaks-as-a-browser-would
def get_text(tag: bs4.Tag) -> str:
    _inline_elements = {"a","span","em","strong","u","i","font","mark","label",
    "s","sub","sup","tt","bdo","button","cite","del","b","a","font",}

    def _get_text(tag: bs4.Tag) -> typing.Generator:
        for child in tag.children:
            if isinstance(child, bs4.Tag):
                # if the tag is a block type tag then yield new lines before after
                is_block_element = child.name not in _inline_elements
                if is_block_element:
                    yield "\n"
                yield from ["\n"] if child.name == "br" else _get_text(child)
                if is_block_element:
                    yield "\n"
            elif isinstance(child, bs4.NavigableString):
                yield child.string

    return "".join(_get_text(tag))


def get_mentions(reply_to: str, mentions: list[StatusMention]):
    mentions = [i for i in mentions if i.acct != me.acct]
    return f"@{reply_to} " + " ".join([f"@{j.acct}" for j in mentions])


def post_meow():
    meowpost = []

    for word in range(randint(1, 10)):
        iter = randint(1, 5)
        if iter == 1:
            meowpost.append("m" + "e" * randint(1, 3) + "o" * randint(1, 3) + "w")
        if iter == 2:
            meowpost.append(
                "m"
                + "r" * randint(1, 3)
                + "e" * randint(1, 3)
                + "o" * randint(1, 3)
                + "w"
            )
        if iter == 3:
            meowpost.append("mr" + "o" * randint(1, 3) + "w")
        if iter == 4:
            meowpost.append(
                "m"
                + "r" * randint(1, 3)
                + "a" * randint(1, 3)
                + "o" * randint(1, 3)
                + "w"
            )
        if iter == 5:
            meowpost.append("ny" + "a" * randint(1, 5))

    mastodon.toot(" ".join(meowpost))


async def meow():
    while True:
        try:
            a = randint(0, 100)
            if a == 67:
                post_meow()

            await sleep(60)
        except Exception:
            catbot_logger.exception("exception in meow")
            break


def build_reply(text: str) -> str:
    reply = []

    for word in text.split(" "):
        if re.match(r"^me+o+w$", word):
            reply.append("m" + "e" * randint(1, 3) + "o" * randint(1, 3) + "w")
        if re.match(r"^mr+e+o+w$", word):
            reply.append(
                "m"
                + "r" * randint(1, 3)
                + "e" * randint(1, 3)
                + "o" * randint(1, 3)
                + "w"
            )
        if re.match(r"^mro+w$", word):
            reply.append("mr" + "o" * randint(1, 3) + "w")
        if re.match(r"^mr+a+o+w", word):
            reply.append(
                "m"
                + "r" * randint(1, 3)
                + "a" * randint(1, 3)
                + "o" * randint(1, 3)
                + "w"
            )
        if re.match(r"^nya+$", word):
            reply.append("ny" + "a" * randint(1, 5))

    return " ".join(reply)


async def reply(debug=False):
    while True:
        try:
            notifs = mastodon.notifications()
            for i in notifs:
                if i.status is None:
                    continue
                if i.status.account.acct == me.acct:
                    continue
                if i.status.account.bot:
                    continue

                # Check reply state
                with engine.begin() as c:
                    if (
                        c.execute(
                            select(replied_posts).where(
                                (replied_posts.c.id == str(i.status.id))
                            )
                        ).fetchone()
                        is not None
                    ):
                        continue

                # Handle replying
                reply_text = build_reply(get_text(BeautifulSoup(i.status.content)).lower())

                if len(reply_text.strip()) > 0:
                    mastodon.status_reblog(i.status.id)
                    await sleep(0.1)
                    mastodon.status_post(
                        get_mentions(i.status.account.acct, i.status.mentions) + " " + reply_text + " :3",
                        in_reply_to_id=i.status.id,
                        visibility=i.status.visibility
                    )
                    await sleep(0.1)

                    emoji = random.choice(["neocat_floof", "neocat_pat_floof"])
                    # Reaction
                    requests.put(f"{mastodon.api_base_url}/api/v1/pleroma/statuses/{i.status.id}/reactions/:{emoji}:", headers={
                        "Authorization": f"Bearer {mastodon.access_token}"
                    })

                    await sleep(0.1)

                    with engine.begin() as c:
                        c.execute(insert(replied_posts).values(id=str(i.status.id)))

                    await sleep(0.5)

            await asyncio.sleep(30)
        except Exception:
            catbot_logger.exception("exception in reply")
            break


async def timeline():
    while True:
        try:
            statuses = mastodon.timeline_home()

            for status in statuses:
                if status.reblog is None:
                    continue
                # Check author
                if status.account.acct == me.acct:
                    continue

                # Check reply state
                with engine.begin() as c:
                    if (
                        c.execute(
                            select(replied_posts).where(
                                (replied_posts.c.id == str(status.id))
                            )
                        ).fetchone()
                        is not None
                    ):
                        continue

                # Handle replying
                reply_text = build_reply(get_text(BeautifulSoup(status.content)).lower())
                if len(reply_text.strip()) > 0:
                    mastodon.status_reblog(status.id)
                    await sleep(0.1)
                    mastodon.status_post(
                        get_mentions(status.account.acct, status.mentions) + " " + reply_text + " :3",
                        in_reply_to_id=status.id
                    )

                    emoji = random.choice(["neocat_floof", "neocat_pat_floof"])
                    # Reaction
                    requests.put(f"{mastodon.api_base_url}/api/v1/pleroma/statuses/{status.id}/reactions/:{emoji}:", headers={
                        "Authorization": f"Bearer {mastodon.access_token}"
                    })

                    with engine.begin() as c:
                        c.execute(insert(replied_posts).values(id=str(status.id)))

                    await sleep(0.5)

                await asyncio.sleep(0.5)

            await asyncio.sleep(20)
        except Exception:
            catbot_logger.exception("exception in timeline")
            break


async def check_followers():
    while True:
        try:
            for i in mastodon.pagination_iterator(mastodon.account_followers(me)):
                try:
                    with engine.begin() as c:
                        a = c.execute(
                            select(follows_table).where(follows_table.c.id == i.id)
                        ).fetchone()

                    if a is not None:
                        continue

                    rel = mastodon.account_relationships(i)

                    if (
                        len(rel) == 0 or
                        not rel[0].following
                        and not rel[0].requested_by
                        and not rel[0].blocked_by
                    ):
                        print(f"follow {i['name']}")
                        while True:
                            follow = mastodon.account_follow(i)
                            if follow:
                                with engine.begin() as c:
                                    c.execute(
                                        insert(follows_table).values(
                                            id=i.id,
                                            acct=i.acct,
                                            followed=datetime.datetime.now(),
                                        )
                                    )
                                break
                            await asyncio.sleep(4)
                except Exception:
                    print("fail to follow", i["name"])
                    break

            with engine.begin() as c:
                a = c.execute(select(follows_table.c.id, follows_table.c.acct)).all()

            for i in a:
                rel = mastodon.account_relationships(a[0])
                if len(rel) == 0:
                    continue

                if not rel[0].followed_by and rel[0].following:
                    print(f"unfollow {i[0]}")
                    try:
                        unfollow_ok = mastodon.account_unfollow(i[0])
                        with engine.begin() as c:
                            c.execute(
                                delete(follows_table).where(
                                    (follows_table.c.id == i[0])
                                )
                            )

                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"failed to unfollow {i[0]}: {str(e)}")
                        pass

            await asyncio.sleep(180)
        except Exception:
            catbot_logger.exception("error in check_followers")
            break


async def status():
    HEARTBEAT_URL = getenv("HEARTBEAT_URL", "")

    if len(HEARTBEAT_URL.strip()) == 0:
        return

    while True:
        async with ClientSession() as session:
            async with session.post(HEARTBEAT_URL, timeout=ClientTimeout(total=5)):
                pass

        await asyncio.sleep(60)


async def main():

    await asyncio.gather(meow(), reply(), timeline(), check_followers(), status())


if __name__ == "__main__":
    asyncio.run(main())
