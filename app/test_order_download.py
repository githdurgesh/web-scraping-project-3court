import asyncio

from app.client.gujarat_client import GujaratHCClient


async def main():
    client = GujaratHCClient()

    try:
        await client._ensure_session()

        file_path = await client.download_order(
            ccin="GJHC240842782023",
            order_no="1",
            order_date="08/01/2024",
            case_detail="AO/1/2024",
            citation="2024:GUJHC:2595",
            file_path="./downloads/orders/AO_1_2024.pdf",
        )

        print("Downloaded:", file_path)

    finally:
        await client.close()
        
if __name__ == "__main__":
    asyncio.run(main())