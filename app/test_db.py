# import asyncio
# import asyncpg


# async def test_connection():

#     try:
#         conn = await asyncpg.connect(
#             host="192.168.166.84",
#             port=5432,
#             user="postgres",
#             password="mErcUry@7539",
#             database="qilegal_demo",
#         )

#         print("DATABASE CONNECTION SUCCESS")

#         result = await conn.fetchval(
#             "SELECT current_database();"
#         )

#         print("DATABASE:", result)

#         await conn.close()

#     except Exception as e:
#         print("DATABASE CONNECTION FAILED")
#         print(type(e).__name__)
#         print(str(e))


# asyncio.run(test_connection())

import asyncio
import asyncpg


async def test_connection():
    try:
        conn = await asyncpg.connect(
            host="192.168.166.84",
            port=5432,
            user="qilegal_read",
            password="mErcUry@7539",
            database="qilegal_demo",
        )

        print("DATABASE CONNECTION SUCCESS")

        database = await conn.fetchval(
            "SELECT current_database();"
        )

        user = await conn.fetchval(
            "SELECT current_user;"
        )

        print("DATABASE:", database)
        print("USER:", user)

        await conn.close()

    except Exception as e:
        print("DATABASE CONNECTION FAILED")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", str(e))


asyncio.run(test_connection())