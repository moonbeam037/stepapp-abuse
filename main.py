from aiohttp import ClientSession
import aiohttp
from re import findall
from os.path import exists
from random import choice
import asyncio


HEADERS = {
    "requestverificationtoken": "CfDJ8Eg0UXBf4GFKnlq0xAV8GmNL3ot6lYt8C6"
                                "-ek5Pp81KvNDiN"
                                "_GNnGR4IPyxNoxoTguxuCKCgoTMa4_9Y"
                                "aWj6Vshi7RL1on3cZG6uzAlfOm0FG95_V"
                                "MaQ2z6tr1Gf878lnRhxWEc56xWElQVaN_UXkGA",
    "cookie": ".AspNetCore.Antiforgery.dXyz_uFU2og=CfDJ8Eg0UXBf4GFKnlq0"
              "xAV8GmOh9Nx6DY5Cc"
              "22NCqtFiJEAbV5rFsyrEwRDOEV4t1DjP6wfW5jna6f"
              "WPwM0MwjORFTvVanGc37k8iTpoCeUZ_fhA3JEVYtOLHPX"
              "0TUh_J2UAGjZcKERj-dYv1MK8DQOL-M; _ym_uid=164"
              "8817213894345354; _ym_isad=1; __cf_bm=JFrI.KXJit7iHW4gK1u3"
              "UFLgOAf3G1FHEJV6Z0vVLQc-1648817219-0-AXI/GKzPzZ"
              "2CUy7SkAaeEpY6DrZ8j+p/c8UdY3rOm8u4pmhP7wQw9+ao4xQEXGmM8Qtq"
              "8/pfJoECUb94vgH7bW5WDqrbmw2+8Ptrn0LEI0S"
              "InHvM9iP/Nt+RBk0ZUxRVXA=="}


def get_proxy():
    return choice(proxies)


async def get_message(email: str):
    async with ClientSession(headers=HEADERS) as client:
        response = await client.post(
                        url="https://tempmailo.com/",
                        json={"mail": email},
                        proxy=get_proxy())
        messages = await response.json()

    for message in messages:
        if message["from"] == "StepApp <noreply@m.step.app>":
            return findall(r"\d+", message["text"])[0]

    return await get_message(email)


async def get_email():
    async with ClientSession(headers=HEADERS) as session:
        resp = await session.get(
                "https://tempmailo.com/changemail?_r=0.31616628502059085",
                proxy=get_proxy())
        email = await resp.text()

    if email == "Rate limit exceeded!":
        return await get_email()
    return email


async def register_account(r: str):
    print("Регистрация аккаунта")
    email = await get_email()
    async with ClientSession(cookies={"r": r}) as client:
        response = await client.get("https://api.step.app/v1/auth/otp-code"
                                    f"?email={email}",
                                    proxy=get_proxy())
        if "OK" not in (await response.text()):
            raise Exception("Не удалось зарегистрировать аккаунт")

        code = await get_message(email)
        response = await client.get("https://api.step.app/v1/auth/token"
                                    f"?email={email}"
                                    f"&code={code}")

        data = await response.json()

        if "access" not in data:
            raise Exception("Не удалось зарегистрировать аккаунт")

    return email, data["access"]["token"], data["refresh"]["token"]


async def add_referrer(r: str, access_token: str):
    print("Добавление реферального кода")
    
    async with ClientSession(
            headers={"Authorization": f"Bearer {access_token}"}) as client:
        response = await client.patch(
                url="https://api.step.app/v1/user/me",
                json={"referrer": r},
                proxy=get_proxy())

    return "OK" in (await response.text())


async def worker(r: str):
    while True:
        print("Попытка создать аккаунт")
        try:
            email, access_token, refresh_token = await register_account(r)
            if await add_referrer(r, access_token):
                print("Успешно зарегистрирован аккаунт " + email)

        except Exception as e:
            print("Во время выполнения регистрации произошла ошибка", str(e))

        await asyncio.sleep(1)


async def main():
    referrer = input("Реф код - ")
    tasks = [asyncio.create_task(worker(referrer))
             for _ in range(int(input("Кол-во потоков - ")))]

    await asyncio.gather(*tasks)


if exists("proxy.txt"):
    proxies = open("proxy.txt").read().strip().split("\n")
else:
    proxies = [None]

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

loop.run_until_complete(main())
