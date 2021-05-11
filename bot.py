# Made with python3
# (C) @FayasNoushad
# Copyright permission under GNU General Public License v3.0
# All rights reserved by FayasNoushad
# License -> https://github.com/FayasNoushad/Rename-Bot/blob/main/LICENSE

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

import os
import time
import asyncio
import sqlite3
import pyrogram
import database as sql
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from progress import progress_for_pyrogram
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from PIL import Image
from database import *

DOWNLOAD_LOCATION = "./DOWNLOADS"
AUTH_USERS = set(int(x) for x in os.environ.get("AUTH_USERS", "").split( ))
PROCESS_MAX_TIMEOUT = int(os.environ.get("TIME_LIMIT"))
ADL_BOT_RQ = {}
START_TEXT = """
Hello {} , I'am a simple file or media rename bot with permanent thumbnail support.

Made by @FayasNoushad
"""
HELP_TEXT = """
<b><u>Rename</u></b>
➠ Send me any telegram file or media.
➠ Choose appropriate option.

<b><u>Set Thumbnail</u></b>
➠ Send a photo to make it as custom thumbnail.

<b><u>Deleting Thumbnail</u></b>
➠ Send /delthumb to deleting thumbnail.

<b><u>Show Thumbnail</u></b>
➠ Send /showthumb for view current thumbnail.

Made by @FayasNoushad
"""
ABOUT_TEXT = """
- **Bot :** `Rename Bot`
- **Creator :** [Fayas](https://telegram.me/TheFayas)
- **Channel :** [Fayas Noushad](https://telegram.me/FayasNoushad)
- **Credits :** `Everyone in this journey`
- **Source :** [Click here](https://github.com/FayasNoushad/Rename-Bot)
- **Language :** [Python3](https://python.org)
- **Library :** [Pyrogram v1.2.0](https://pyrogram.org)
- **Server :** [Heroku](https://heroku.com)
"""
START_BUTTONS = InlineKeyboardMarkup(
        [[
        InlineKeyboardButton('Channel', url='https://telegram.me/FayasNoushad'),
        InlineKeyboardButton('Feedback', url='https://telegram.me/TheFayas')
        ],[
        InlineKeyboardButton('Help', callback_data='help'),
        InlineKeyboardButton('About', callback_data='about'),
        InlineKeyboardButton('Close', callback_data='close')
        ]]
    )
HELP_BUTTONS = InlineKeyboardMarkup(
        [[
        InlineKeyboardButton('Home', callback_data='home'),
        InlineKeyboardButton('About', callback_data='about'),
        InlineKeyboardButton('Close', callback_data='close')
        ]]
    )
ABOUT_BUTTONS = InlineKeyboardMarkup(
        [[
        InlineKeyboardButton('Home', callback_data='home'),
        InlineKeyboardButton('Help', callback_data='help'),
        InlineKeyboardButton('Close', callback_data='close')
        ]]
    )

if __name__ == "__main__" :
    if not os.path.isdir(DOWNLOAD_LOCATION):
        os.makedirs(DOWNLOAD_LOCATION)

FayasNoushad = Client(
    "Rename Bot",
    bot_token=os.environ.get("BOT_TOKEN"),
    api_id=int(os.environ.get("APP_ID", 12345)),
    api_hash=os.environ.get("API_HASH")
)

@FayasNoushad.on_callback_query()
async def cb_handler(bot, update):
    if update.data == "home":
        await update.message.edit_text(
            text=START_BUTTONS.format(update.from_user.mention),
            reply_markup=START_BUTTONS,
            disable_web_page_preview=True
        )
    elif update.data == "help":
        await update.message.edit_text(
            text=HELP_TEXT,
            reply_markup=HELP_BUTTONS,
            disable_web_page_preview=True
        )
    elif update.data == "about":
        await update.message.edit_text(
            text=ABOUT_TEXT,
            reply_markup=ABOUT_BUTTONS,
            disable_web_page_preview=True
        )
    elif update.data == "rename":
        await update.message.delete()
        await force_name(bot, update.message)
    elif update.data == "cancel":
        await update.message.edit_text(
            text="<code>Process Cancelled</code>",
            disable_web_page_preview=True
        )
    else:
        await update.message.delete()

@FayasNoushad.on_message(filters.command(["start"]))
async def start(bot, update):
    await bot.send_message(
        chat_id=update.chat.id,
        text=START_TEXT.format(update.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=START_BUTTONS,
        reply_to_message_id=update.message_id
    )

@FayasNoushad.on_message(filters.photo)
async def save_photo(bot, update):
    if update.media_group_id is not None:
        # album is sent
        download_location = DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + "/" + str(update.media_group_id) + "/"
        # create download directory, if not exist
        if not os.path.isdir(download_location):
            os.makedirs(download_location)
        await sql.df_thumb(update.from_user.id, update.message_id)
        await bot.download_media(
            message=update,
            file_name=download_location
        )
    else:
        # received single photo
        download_location = DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + ".jpg"
        await sql.df_thumb(update.from_user.id, update.message_id)
        await bot.download_media(
            message=update,
            file_name=download_location
        )
        await bot.send_message(
            chat_id=update.chat.id,
            text="Thumbnail Saved ✅ This Is Permanent",
            reply_to_message_id=update.message_id
        )

@FayasNoushad.on_message(filters.command(["delthumb"]))
async def delete_thumbnail(bot, update):
    thumb_image_path = DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + ".jpg"
    #download_location = DOWNLOAD_LOCATION + "/" + str(update.from_user.id)
    try:
        await sql.del_thumb(update.from_user.id)
        #os.remove(download_location + ".json")
    except:
        pass
    try:
        os.remove(thumb_image_path)
    except:
        pass
    await bot.send_message(
        chat_id=update.chat.id,
        text="Thumbnail cleared succesfully!",
        reply_to_message_id=update.message_id
    )

@FayasNoushad.on_message(filters.command(["showthumb"]))
async def show_thumb(bot, update):
    thumb_image_path = DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + ".jpg"
    if not os.path.exists(thumb_image_path):
        mes = await thumb(update.from_user.id)
        if mes != None:
            m = await bot.get_messages(update.chat.id, mes.msg_id)
            await m.download(file_name=thumb_image_path)
            thumb_image_path = thumb_image_path
        else:
            thumb_image_path = None    

    if thumb_image_path is not None:
        try:
            await bot.send_photo(
                chat_id=update.chat.id,
                photo=thumb_image_path,
                reply_to_message_id=update.message_id
            )
        except:
            pass
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text="No thumbnails found!",
            reply_to_message_id=update.message_id
        )

@FayasNoushad.on_message(filters.private & (filters.audio | filters.document | filters.animation | filters.video | filters.voice | filters.video_note))
async def filter(bot, update):
    if update.from_user.id not in AUTH_USERS:
        if str(update.from_user.id) in ADL_BOT_RQ:
            current_time = time.time()
            previous_time = ADL_BOT_RQ[str(update.from_user.id)]
            process_max_timeout = round(PROCESS_MAX_TIMEOUT/60)
            present_time = round(PROCESS_MAX_TIMEOUT-(current_time - previous_time))
            ADL_BOT_RQ[str(update.from_user.id)] = time.time()
            if round(current_time - previous_time) < PROCESS_MAX_TIMEOUT:
                await bot.send_message(
                    chat_id=update.chat.id,
                    text=f"Sorry Friend, Free users can only 1 request per {process_max_timeout} minutes. Please try again after {present_time} seconds later.",
                    disable_web_page_preview=True,
                    parse_mode="html",
                    reply_to_message_id=update.message_id
                )
                return
        else:
            ADL_BOT_RQ[str(update.from_user.id)] = time.time()
    file = update.media
    try:
        filename = file.file_name
    except:
        filename = "None"
    await bot.send_message(
        chat_id=update.chat.id,
        text=f"<b>File Name</b> : <code>{filename}</code> \n\nSelect the desired option below 😇",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="📝 RENAME 📝", callback_data="rename")],
                                                [InlineKeyboardButton(text="✖️ CANCEL ✖️", callback_data="cancel")]]),
        parse_mode="html",
        reply_to_message_id=update.message_id,
        disable_web_page_preview=True
    )

@FayasNoushad.on_message(filters.private & filters.reply & filters.text)
async def cus_name(bot, message):
    if (message.reply_to_message.reply_markup) and isinstance(message.reply_to_message.reply_markup, ForceReply):
        asyncio.create_task(rename(bot, message))
    else:
        print('No media present')

async def force_name(bot, message):
    await bot.send_message(
        message.reply_to_message.from_user.id,
        text="Enter new name for media with file type\n\nExample :- <code>sample.mkv | media</code>",
        reply_to_message_id=message.reply_to_message.message_id,
        reply_markup=ForceReply(True)
    )
    
async def rename(bot, message):    
    mssg = await bot.get_messages(message.chat.id, message.reply_to_message.message_id)
    media = mssg.reply_to_message    
    if media.empty:
        await message.reply_text('Why did you delete that 😕', True)
        return
    await bot.delete_messages(chat_id=message.chat.id, message_ids=message.reply_to_message.message_id, revoke=True)
    if (" | " in message.text) and (message.reply_to_message is not None):
        file_name, file_type = message.text.split(" | ", 1)
        if len(file_name) > 64:
            await message.reply_text(text=f"Limits of telegram file or media name spellings is 64 characters only.")
            return
        description = "<b>" + file_name + "</b>"
        download_location = DOWNLOAD_LOCATION + "/"
        thumb_image_path = download_location + "FayasNoushad " + str(message.from_user.id) + ".jpg"
        if not os.path.exists(thumb_image_path):
            mes = await thumb(message.from_user.id)
            if mes != None:
                m = await bot.get_messages(message.chat.id, mes.msg_id)
                await m.download(file_name=thumb_image_path)
                thumb_image_path = thumb_image_path

        a = await bot.send_message(chat_id=message.chat.id, text="<code>Downloading To My server Please Wait...</code>", reply_to_message_id=message.message_id)
        c_time = time.time()
        the_real_download_location = await bot.download_media(
            message=media,
            file_name=download_location,
            progress=progress_for_pyrogram,
            progress_args=("<code>Downloading To My server Please Wait...</code>", a, c_time)
        )
        if the_real_download_location is not None:
            await bot.edit_message_text(text="<code>Downloaded Successfully! Now I am Uploading to Telegram...</code>", chat_id=message.chat.id, message_id=a.message_id)
            new_file_name = download_location + file_name
            os.rename(the_real_download_location, new_file_name)
            # logger.info(the_real_download_location)
            try:
                await bot.edit_message_text(text="<code>Downloaded Successfully! Now I am Uploading to Telegram...</code>", chat_id=message.chat.id, message_id=a.message_id)
            except:
                pass
            if os.path.exists(thumb_image_path):
                width = 0
                height = 0
                metadata = extractMetadata(createParser(thumb_image_path))
                if metadata.has("width"):
                    width = metadata.get("width")
                if metadata.has("height"):
                    height = metadata.get("height")
                Image.open(thumb_image_path).convert("RGB").save(thumb_image_path)
                img = Image.open(thumb_image_path)
                img.resize((320, height))
                img.save(thumb_image_path, "JPEG")
            else:
                thumb_image_path = None
            c_time = time.time()
            if "media" in file_type:
                await bot.send_video(
                    chat_id=message.chat.id,
                    video=new_file_name,
                    thumb=thumb_image_path,
                    caption=description,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⚙ Join Updates Channel ⚙', url='https://telegram.me/FayasNoushad')]]),
                    reply_to_message_id=message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=("<code>Downloaded Successfully! Now I am Uploading to Telegram...</code>", a, c_time)
                )
                try:
                    os.remove(new_file_name)
                except:
                    pass
                try:
                    os.remove(thumb_image_path)
                except:
                    pass
                await bot.edit_message_text(text="<b>Thank you for Using Me</b>", chat_id=message.chat.id, message_id=a.message_id, disable_web_page_preview=True)
                return
            if "file" in file_type:
                await bot.send_document(
                    chat_id=message.chat.id,
                    document=new_file_name,
                    thumb=thumb_image_path,
                    caption=description,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⚙ Join Updates Channel ⚙', url='https://telegram.me/FayasNoushad')]]),
                    reply_to_message_id=message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=("<code>Downloaded Successfully! Now I am Uploading to Telegram...</code>", a, c_time)
                )
                try:
                    os.remove(new_file_name)
                except:
                    pass                 
                try:
                    os.remove(thumb_image_path)
                except:
                    pass
                await bot.edit_message_text(text="<b>Thank you for Using Me</b>", chat_id=message.chat.id, message_id=a.message_id, disable_web_page_preview=True)
                return
        else:
            await bot.send_message(chat_id=message.chat.id, text="You're not Authorized to do that!", reply_to_message_id=message.message_id)


FayasNoushad.run()
