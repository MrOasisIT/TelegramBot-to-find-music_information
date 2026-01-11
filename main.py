from aiogram import Bot,Dispatcher
import asyncio
import handlers
from handlers.poisk import router
from secret_data import TOKEN

bot = Bot(token = TOKEN)
dp = Dispatcher()

async def main():
    dp.include_routers(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    