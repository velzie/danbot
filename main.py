
import discord

import hashlib
import os
import aiohttp
import asyncio
import requests


def checksum(filename, hash_factory=hashlib.md5, chunk_num_blocks=128): # Maybe try chunking it higher for faster speeds..?
    h = hash_factory()
    h.update(filename)
    return h.hexdigest()

class danbooru():
    # Updated for 29th of October 2023, credit https://github.com/LuqueDaniel/pybooru/issues/61
    def __init__(self,session, login, api_key, base_url):
        "Must have all 3 values filled to work"
        # Example danbooru("username","7Fi5AkBieaR83aQavLBbps2t","https://danbooru.selfhosted.org")
        self.login = login
        self.api_key = api_key
        self.base_url = base_url
        self.fn = "" # Filename not set until create post
        self.session =session

    async def create_post(self, filename, tag_string, rating, source):
        "Upload the image"
        self.fn = filename
        # if self.search_md5() == -1: # If image not found, upload
        media_asset_id = await self.upload_image()
        image_id = self.search_md5() # get image ID (even if it was uploaded)
        return await self.upload_to_post(media_asset_id, image_id, tag_string, rating, source)

    async def upload_image(self):
        "Upload the image with the tags given and the other information given"
        files = {'upload[files][0]': self.fn}
        url = self.base_url + "/uploads.json?api_key={}&login={}".format(self.api_key,self.login)

        response = await self.session.post(url, data=files)
        if response.status == 201:
            print(await response.json())
            return (await response.json())["id"]
        else:
            print(await response.json())
            quit(1)

    def search_md5(self):
        "Searches danbooru instance with md5sum to get the id value"
        md5 = checksum(self.fn)
        url = self.base_url + "/uploads.json?search[media_assets][md5]={}&api_key={}&login={}".format(md5,self.api_key,self.login)
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()[0]["upload_media_assets"][0]["media_asset"]["id"]
        elif response.status_code == 304:
            print("Image not uploaded before!")
            return -1
        else:
            print(response.json())
            quit(1)

    async def upload_to_post(self, media_asset_id, image_id, tag_string, rating, source):
        url = self.base_url + "/posts.json?api_key={}&login={}".format(self.api_key,self.login)
        params = {"post[tag_string]": tag_string,
                  "post[rating]": rating, # rating [g -> general ,s -> sensitive,q -> questionable, e -> explicit]
                  "post[source]": source,
                  "media_asset_id": image_id,
                  "upload_media_asset_id": media_asset_id, # NOT SURE WHY THIS HAS TO BE DONE!!?!
                  #"post[artist_commentary_title]": todo (want to import via pixiv api)
                  #"post[artist_commentary_desc]": todo
                  }

        response = requests.post(url, params=params)
        if response.status_code == 201:
            return True
        else:
            return "Failed to create post"




intents = discord.Intents.default()
intents.message_content = True


class Bot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        self.session = aiohttp.ClientSession()
        self.db = danbooru(self.session,os.environ["DBUSER"], os.environ["DBTOKEN"], os.environ["DBURL"])

    async def on_message(self,message: discord.Message):
        if message.channel.id != int(os.environ["CHANNELID"]):
            return
        if message.author == client.user:
            return
        if len(message.attachments) == 1:
            img = message.attachments[0].url
            tags = message.content
        elif "://" in message.content.split(" ")[0]:
            img = message.content.split(" ")[0]
            tags = message.content[message.content.find(" "):]
        else:
            return

        print(img)

        if tags == "":
            return
        tags += " user:{}".format(message.author.global_name)

        session = aiohttp.ClientSession()


        resp = await session.get(img)

        try: 
            r = await self.db.create_post(await resp.content.read(),tags,"g",None)
        except Exception as e:
            return await message.reply("ERROR: " + e.__str__());

        if r == True:
            await message.add_reaction("✅")
        else:
            await message.reply(r);


        if message.content.startswith('.ping'):
            print("a")
            await message.channel.send('Hello!')
        await session.close()


client = Bot(intents=intents)
client.run(os.environ["TOKEN"])
