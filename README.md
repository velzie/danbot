# danbot
dead simple discord bot for automating uploads to a danbooru instance. made for https://booru.mercurywork.shop

# installling
clone the repo, install `requests` and `discord.py`

# use
```
TOKEN=<discord_token_here> DBUSER=<danbooru_account_username> DBTOKEN=<danbooru_api_token> DBURL=https://booru.mercurywork.shop CHANNELID=<discord_channel_id_here> python3 main.py
```
whenever media is posted in that channel, it will automatically upload to the instance
