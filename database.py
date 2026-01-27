import json
import os

import dotenv
from sqlalchemy import create_engine, MetaData, Table, VARCHAR, Column

if not os.path.exists("data"):
    os.mkdir("data")

dotenv.load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///data/waf.db"
DATABASE_CONNECT_ARGS = os.getenv("DATABASE_CONNECT_ARGS") or '{"timeout": 30}'

engine = create_engine(DATABASE_URL, connect_args=json.loads(DATABASE_CONNECT_ARGS))

md_obj = MetaData()

replied_posts = Table(
    "quoted_posts",
    md_obj,
    Column("id", VARCHAR, primary_key=True),
)

md_obj.create_all(engine, checkfirst=True)
