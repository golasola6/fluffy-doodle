from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
from pyrogram import Client, filters
from pyrogram.types import *
from motor.motor_asyncio import AsyncIOMotorClient  
from os import environ as env
import asyncio, datetime, time
from bson import ObjectId
from pyrogram import enums
import re

ACCEPTED_TEXT = "Hey {user}\n\nYour Request For {chat} Is Accepted ✅\nSend /start to Get more Updates.\n\nJoin👇👇\n{joinlink}"
START_TEXT = "Hey {}\n\nI am Auto Request Accept Bot With Working For All Channel. Add Me In Your Channel To Use"

API_ID = int(env.get('API_ID'))
API_HASH = env.get('API_HASH')
BOT_TOKEN = env.get('BOT_TOKEN')
DB_URL = env.get('DB_URL')
id_pattern = re.compile(r'^.\d+$')
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in env.get('ADMIN', '5965340120 6126812037').split()]
JOINLINK = env.get('JOINLINK', 'https://t.me/+V4qgIH1P7iszZDhl')
Dbclient = AsyncIOMotorClient(DB_URL)
Cluster = Dbclient['Cluster0']
Data = Cluster['users']
Bot = Client(name='LazyAutoAcceptBot', api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@Bot.on_message(filters.command("start") & filters.private)                    
async def start_handler(c, m):
    try:
        user_id = m.from_user.id

        # Add user to DB if not exists
        if not await Data.find_one({'id': user_id}):
            await Data.insert_one({'id': user_id})

        # Default button
        lazydeveloper_btn = [[
            InlineKeyboardButton('🎃 ÄßÖÚ† 🎃', callback_data="about_bot")
        ]]

        # Fetch all dynamic buttons from DB
        dynamic_buttons = []
        buttons = await Cluster["buttons"].find().to_list(None)
        for i in range(0, len(buttons), 2):
            row = []
            row.append(InlineKeyboardButton(buttons[i]["text"], url=buttons[i]["url"]))
            if i+1 < len(buttons):
                row.append(InlineKeyboardButton(buttons[i+1]["text"], url=buttons[i+1]["url"]))

            dynamic_buttons.append(row)

        # Combine buttons
        final_keyboard =  dynamic_buttons + lazydeveloper_btn

        # Fetch video from DB
        video_data = await Cluster["assets"].find_one({"_id": "start_video"})
        video = video_data["video"] if video_data else None

        # Start message
        joinlink = f"{JOINLINK}"

        if video:
            return await c.send_video(
                chat_id=user_id,
                video=video,
                caption=START_TEXT.format(m.from_user.mention, joinlink),
                reply_markup=InlineKeyboardMarkup(final_keyboard),
                supports_streaming=True,
                protect_content=True,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            return await m.reply_text(
                text=START_TEXT.format(m.from_user.mention, joinlink),
                reply_markup=InlineKeyboardMarkup(final_keyboard),
                disable_web_page_preview=True
            )

    except Exception as lazy:
        print(lazy)

@Bot.on_message(filters.command("set_video") & filters.user(ADMINS))
async def set_video(c, m):
    try:
        if not m.reply_to_message or not m.reply_to_message.video:
            return await m.reply("🎬 Reply to a video to set as the intro video.")

        file_id = m.reply_to_message.video.file_id

        await Cluster["assets"].update_one(
            {"_id": "start_video"},
            {"$set": {"video": file_id}},
            upsert=True
        )
        await m.reply("✅ Start intro video saved/updated successfully!")
    except Exception as e:
        await m.reply(f"⚠️ Error: {e}")


@Bot.on_message(filters.command("add_btn") & filters.user(ADMINS))
async def add_btn_handler(client, message):
    await message.reply_text("Send me button(s) in format:\n\n`Button Text - URL`\n\nYou can add multiple lines like this too.", quote=True)
    Bot.add_btn_state = message.from_user.id

@Bot.on_message(filters.command("all_btns") & filters.user(ADMINS))
async def all_btns_handler(client, message):
    buttons = await Cluster["buttons"].find().to_list(None)

    if not buttons:
        await message.reply_text("No buttons added yet.")
        return

    keyboard = []
    for btn in buttons:
        btn_id = str(btn["_id"])
        keyboard.append([
            InlineKeyboardButton(f"{btn['text']}", url=btn["url"]),
            InlineKeyboardButton("✏️ Update", callback_data=f"update_btn_{btn_id}"),
            InlineKeyboardButton("❌ Delete", callback_data=f"delete_btn_{btn_id}")
        ])

    await message.reply_text("🧩 All Buttons:", reply_markup=InlineKeyboardMarkup(keyboard))

@Bot.on_callback_query(filters.regex("delete_btn_"))
async def delete_button(client, callback_query):
    btn_id = callback_query.data.split("_")[-1]
    await Cluster["buttons"].delete_one({"_id": ObjectId(btn_id)})
    await callback_query.answer("Button deleted.")
    await callback_query.message.delete()

@Bot.on_callback_query(filters.regex("update_btn_"))
async def update_button(client, callback_query):
    btn_id = callback_query.data.split("_")[-1]
    await callback_query.message.reply_text(f"Send new format for this button (text - url):", quote=True)
    Bot.update_btn_state = {"user": callback_query.from_user.id, "btn_id": btn_id}
    await callback_query.answer()

@Bot.on_callback_query(filters.regex("about_bot"))
async def about_handler(c, cb):
    about_text = """
👑 <b>Owner</b>: <a href='https://t.me/directapkpromo'>SimplyfyTuber</a>
🛠 <b>Developer:</b> <a href='https://telegram.me/LazyDeveloperr'>LazyDeveloperr</a>

🧠 <b>Powered By:</b> Pyrogram & MongoDB  
🔐 <b>Secure:</b> Auth-based Admin Panel & Dynamic Buttons

—
🧡 <b>Made with love by LazyDeveloper</b>
    """
    lazydeveloper_btn = [[
            InlineKeyboardButton('ཫ𐰌𓇽 HOME 𓇽𐰌ཀ', callback_data="home")
        ]]
    await cb.message.edit_text(
                            about_text,
                            reply_markup=InlineKeyboardMarkup(lazydeveloper_btn),
                            disable_web_page_preview=True,
                            parse_mode=enums.ParseMode.HTML
                            )

@Bot.on_callback_query(filters.regex("home"))
async def about_handler(c, cb):
    try:
        # Default button
        lazydeveloper_btn = [[
            InlineKeyboardButton('🎃 ÄßÖÚ† 🎃', callback_data="about_bot")
        ]]

        # Fetch all dynamic buttons from DB
        dynamic_buttons = []
        buttons = await Cluster["buttons"].find().to_list(None)
        for i in range(0, len(buttons), 2):
            row = []
            row.append(InlineKeyboardButton(buttons[i]["text"], url=buttons[i]["url"]))
            if i+1 < len(buttons):
                row.append(InlineKeyboardButton(buttons[i+1]["text"], url=buttons[i+1]["url"]))

            dynamic_buttons.append(row)

        # Combine buttons
        final_keyboard =  dynamic_buttons + lazydeveloper_btn

        # Start message
        joinlink = f"{JOINLINK}"

        return await cb.message.edit_text(
                START_TEXT.format(cb.message.from_user.mention, joinlink),
                reply_markup=InlineKeyboardMarkup(final_keyboard),
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
    except Exception as lazy:
        print(lazy)

@Bot.on_message(filters.text & filters.user(ADMINS) & ~filters.command(["start", "all_btns", "broadcast", "users"]))
async def admin_text_handler(client, message):
    user_id = message.from_user.id

    # 🟩 Update Button Logic
    if getattr(Bot, "update_btn_state", None):
        state = Bot.update_btn_state
        if state["user"] == user_id:
            if " - " in message.text:
                text, url = message.text.split(" - ", 1)
                await Cluster["buttons"].update_one(
                    {"_id": ObjectId(state["btn_id"])},
                    {"$set": {"text": text.strip(), "url": url.strip()}}
                )
                await message.reply_text("✅ Button updated.")
            else:
                await message.reply_text("⚠️ Invalid format. Use `Text - URL`")
            Bot.update_btn_state = None
            return

    # 🟨 Add Button Logic
    if getattr(Bot, "add_btn_state", None) == user_id:
        btns = message.text.strip().split("\n")
        inserted = 0

        for btn in btns:
            if " - " in btn:
                text, url = btn.split(" - ", 1)
                await Cluster["buttons"].insert_one({"text": text.strip(), "url": url.strip()})
                inserted += 1

        await message.reply_text(f"✅ {inserted} button(s) saved.")
        Bot.add_btn_state = None


@Bot.on_message(filters.command(["broadcast", "users"]) & filters.user(ADMINS))  
async def broadcast(c, m):
    if m.text == "/users":
        total_users = await Data.count_documents({})
        return await m.reply(f"Total Users: {total_users}")
    b_msg = m.reply_to_message
    sts = await m.reply_text("Broadcasting your messages...")
    users = Data.find({})
    total_users = await Data.count_documents({})
    done = 0
    failed = 0
    success = 0
    start_time = time.time()
    async for user in users:
        user_id = int(user['id'])
        try:
            await b_msg.copy(chat_id=user_id)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await b_msg.copy(chat_id=user_id)
            success += 1
        except InputUserDeactivated:
            await Data.delete_many({'id': user_id})
            failed += 1
        except UserIsBlocked:
            failed += 1
        except PeerIdInvalid:
            await Data.delete_many({'id': user_id})
            failed += 1
        except Exception as e:
            failed += 1
        done += 1
        if not done % 20:
            await sts.edit(f"Broadcast in progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nFailed: {failed}")    
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.delete()
    await m.reply_text(f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nFailed: {failed}", quote=True)

@Bot.on_message(filters.command("accept_old_request") & filters.user(ADMINS))
async def accept_old_requests(c, m):
    chat_id = m.chat.id

    try:
        # Get pending join requests
        pending = await c.get_chat_join_requests(chat_id)

        if not pending:
            await m.reply_text("✨ No pending join requests to approve, my love!")
            return

        count = 0
        for user in pending:
            try:
                await c.approve_chat_join_request(chat_id, user.from_user.id)
                # Store in DB if not already present
                if not await Data.find_one({'id': user.from_user.id}):
                    await Data.insert_one({'id': user.from_user.id})
                count += 1
            except Exception as e:
                print(f"Error approving user {user.from_user.id}: {e}")

        await m.reply_text(f"🥰 Approved {count} pending join requests, sweetheart!")

    except Exception as e:
        print(f"Error fetching join requests: {e}")
        await m.reply_text("💔 Something went wrong while accepting requests.")

@Bot.on_chat_join_request()
async def req_accept(c, m):
    user_id = m.from_user.id
    chat_id = m.chat.id
    if not await Data.find_one({'id': user_id}): await Data.insert_one({'id': user_id})
    await c.approve_chat_join_request(chat_id, user_id)
    try: 
        # Default button
        lazydeveloper_btn = [[
            InlineKeyboardButton('🎃 ÄßÖÚ† 🎃', callback_data="about_bot")
        ]]

        # Fetch all dynamic buttons from DB
        dynamic_buttons = []
        buttons = await Cluster["buttons"].find().to_list(None)
        for i in range(0, len(buttons), 2):
            row = []
            row.append(InlineKeyboardButton(buttons[i]["text"], url=buttons[i]["url"]))
            if i+1 < len(buttons):
                row.append(InlineKeyboardButton(buttons[i+1]["text"], url=buttons[i+1]["url"]))

            dynamic_buttons.append(row)

        # Combine buttons
        final_keyboard =  dynamic_buttons + lazydeveloper_btn

        # Fetch video from DB
        video_data = await Cluster["assets"].find_one({"_id": "start_video"})
        video = video_data["video"] if video_data else None

        # Start message
        joinlink = f"{JOINLINK}"

        if video:
            return await c.send_video(
                chat_id=user_id,
                video=video,
                caption=ACCEPTED_TEXT.format(user=m.from_user.mention, chat=m.chat.title, joinlink=joinlink),
                reply_markup=InlineKeyboardMarkup(final_keyboard),
                supports_streaming=True,
                protect_content=True,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            return await m.reply_text(
                user_id,
                text=ACCEPTED_TEXT.format(user=m.from_user.mention, chat=m.chat.title, joinlink=joinlink),
                reply_markup=InlineKeyboardMarkup(final_keyboard),
                disable_web_page_preview=True
            )
        
    except Exception as e: 
        print(e)
   

Bot.run()



#crafted by - the one and only LazyDeveloperr
