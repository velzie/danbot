import discord
from discord.ext import tasks
import requests

import hashlib
import requests
import os


def checksum(filename, hash_factory=hashlib.md5, chunk_num_blocks=128): # Maybe try chunking it higher for faster speeds..?
    h = hash_factory()
    with open(filename,'rb') as f: 
        while chunk := f.read(chunk_num_blocks*h.block_size): 
            h.update(chunk)
    return h.hexdigest()

class danbooru():
    # Updated for 29th of October 2023, credit https://github.com/LuqueDaniel/pybooru/issues/61
    def __init__(self, login, api_key, base_url):
        "Must have all 3 values filled to work"
        # Example danbooru("username","7Fi5AkBieaR83aQavLBbps2t","https://danbooru.selfhosted.org")
        self.login = login
        self.api_key = api_key
        self.base_url = base_url
        self.fn = "" # Filename not set until create post

    def create_post(self, filename, tag_string, rating, source):
        "Upload the image"
        self.fn = filename
        # if self.search_md5() == -1: # If image not found, upload
        media_asset_id = self.upload_image()
        image_id = self.search_md5() # get image ID (even if it was uploaded)
        self.upload_to_post(media_asset_id, image_id, tag_string, rating, source)

    def upload_image(self):
        "Upload the image with the tags given and the other information given"
        files = {'upload[files][0]': open(self.fn, 'rb')}
        url = self.base_url + "/uploads.json?api_key={}&login={}".format(self.api_key,self.login)
        response = requests.post(url, files=files)
        if response.status_code == 201:
            print(response.json())
            return response.json()["id"]
        else:
            print(response.json())
            quit(1)

    def search_md5(self):
        "Searches danbooru instance with md5sum to get the id value"
        md5 = checksum(self.fn)
        url = self.base_url + "/uploads.json?search[media_assets][md5]={}&api_key={}&login={}".format(md5,self.api_key,self.login)
        print(url)
        response = requests.get(url)
        if response.status_code == 200:
            print(response.json()[0]["upload_media_assets"][0]["media_asset"]["id"])
            return response.json()[0]["upload_media_assets"][0]["media_asset"]["id"]
        elif response.status_code == 304:
            print("Image not uploaded before!")
            return -1
        else:
            print(response.json())
            quit(1)

    def upload_to_post(self, media_asset_id, image_id, tag_string, rating, source):
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
        print(response)
        if response.status_code == 201:
            print("Post Creation Success")
        else:
            print("Failed to create post")


db = danbooru(os.environ["DBUSER"], os.environ["DBTOKEN"], os.environ["DBURL"])


intents = discord.Intents.default()
intents.message_content = True


class Bot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_message(self,message):
        if message.channel.id != int(os.environ["CHANNELID"]):
            return
        if message.author == client.user:
            return
        if len(message.attachments) != 1:
            return

        img = message.attachments[0].url
        print(img)

        with open("/dev/shm/a","wb") as f:
            f.write(requests.get(img).content)

        db.create_post('/dev/shm/a',message.content,"g",None)


        if message.content.startswith('.ping'):
            print("a")
            await message.channel.send('Hello!')


client = Bot(intents=intents)
client.run(os.environ["TOKEN"])


