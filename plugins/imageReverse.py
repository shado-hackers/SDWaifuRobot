# Copyright 2023 Qewertyy, MIT License
import traceback
from httpx import AsyncClient
import base64
import requests
from pyrogram import Client, filters, types as t
from Utils import ReverseImageSearch, getFile, uploadToTelegraph, createMessage


async def uploadToImgur(file: str):
    try:
        # Read the image file and encode it to base64
        with open(file, 'rb') as f:
            data = f.read()
            base64_data = base64.b64encode(data)

        # Set API endpoint and headers for Imgur upload
        url = "https://api.imgur.com/3/image"
        headers = {"Authorization": "Client-ID a10ad04550b0648"}

        # Upload image to Imgur and get the response
        response = requests.post(url, headers=headers, data={"image": base64_data})

        if response.status_code != 200:
            return None

        # Parse and return the image URL from Imgur response
        result = response.json()
        return result["data"]["link"]

    except Exception as e:
        print("Error uploading to Imgur:")
        traceback.print_exc()
        return None

    finally:
        os.remove(file)
        

@Client.on_message(filters.command(["pp", "reverse", "sauce"]))
async def reverseImageSearch(_: Client, m: t.Message):
    try:
        reply = await m.reply_text("`Downloading...`")
        file = await getFile(m)
        if file is None:
            return await reply.edit("Reply to an image?")
        if file == 1:
            return await reply.edit("File size is large")
        await reply.edit("`Uploading to the server...`")
        imagePath = await uploadToTelegraph(file)
        if imagePath is None:
            return await reply.edit("Ran into an error.")
        await reply.edit_text(
            text="Select a search engine",
            reply_markup=t.InlineKeyboardMarkup(
                [
                    [
                        t.InlineKeyboardButton(
                            text="Google",
                            callback_data=f"ris.g.{imagePath}.{m.from_user.id}",
                        )
                    ],
                    [
                        t.InlineKeyboardButton(
                            text="Bing",
                            callback_data=f"ris.b.{imagePath}.{m.from_user.id}",
                        )
                    ],
                    [
                        t.InlineKeyboardButton(
                            text="Yandex",
                            callback_data=f"ris.y.{imagePath}.{m.from_user.id}",
                        )
                    ],
                ]
            ),
        )
    except Exception as E:
        traceback.print_exc()
        await reply.delete()
        return await m.reply_text("Ran into an error.")


@Client.on_callback_query(filters.regex(r"^ris.(.*?)"))
async def ReverseResults(_: Client, query: t.CallbackQuery):
    data = query.data.split(".")
    userId = int(data[-1])
    imageUrl = "https://i.imgur.com" + data[-3] + "." + data[-2]
    platform = "bing" if data[1] == "b" else "google" if data[1] == "g" else "yandex"
    if query.from_user.id != userId:
        return await query.answer("Not for you!", show_alert=True)
    output = await ReverseImageSearch(imageUrl, platform)
    if output["code"] != 2:
        return await query.edit_message_text("Ran into an error.")
    messages = createMessage(platform, output["content"])
    btn = t.InlineKeyboardMarkup(
        [[t.InlineKeyboardButton(text="Image URL", url=output["content"]["url"])]]
    )
    await query.edit_message_text(messages["message"], reply_markup=btn)
