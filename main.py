import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import bot
from dotenv import load_dotenv
import os
import json
from typing import Optional
import random
import asyncio

load_dotenv()
TOKEN = os.getenv('TOKEN')
OWNER_ID = os.getenv('OWNER_ID')
SERVER_ID =os.getenv('SERVER_ID')
#VC_ID = os.getenv('VC_ID')
PREFIX = os.getenv('PREFIX')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, max_messages=10000, help_command=None)

queue = []
played_sets = []
jsondata = {}
current_timestamp=0
voice_channel = None

def sec_to_hms(seconds):
    seconds_round = round(seconds)
    min, sec = divmod(seconds_round, 60)
    hour, min = divmod(min, 60)
    if hour:
        h = f"{hour}:"
        m = f"{min:02d}"
    else:
        h = ''
        m = min
    return f"{h}{m}:{sec:02d}"

def mmss_to_sec(mmss):
    m,s = mmss.split(":")
    return((int(m) * 60)+ int(s))


async def queuebuild():
    mypath = "setlists"
    tracklists = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f)) ]
    for set in tracklists:

        with open(mypath + "/" + set) as json_file:
            jsondata[set] = json.load(json_file)
            
    queue.append(set)
    
@bot.command()
async def join(ctx):
    try:
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect()
        global abc 
        abc = ctx.guild
        asyncio.sleep(1.5)

        await tracklist.start()
        await ctx.send("hi")
    except:
        await ctx.send("You are not in a voice channel")

@bot.command()
async def dc(ctx):
    try:
        bot_voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if bot_voice_client.source != None or bot_voice_client.is_playing() == True:
            bot_voice_client.stop()
            await asyncio.sleep(1.5) #allows the bot to properly end the file before disconnecting
        await bot_voice_client.disconnect()
        await ctx.send("disconnected from channel")
    except:
        #discord.utils.get(bot.voice_clients, guild=ctx.guild)
        await ctx.send("You are not in a voice channel")

@bot.command()
async def pause(ctx):
    try:
        bot_voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        bot_voice_client.pause()
        await ctx.send("paused current set")
    except:
        await ctx.send("an error occured")
        
@bot.command()
async def unpause(ctx):
    try:
        bot_voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        bot_voice_client.resume()
        await ctx.send("resumed current set")
    except:
        await ctx.send("an error occured")


@tasks.loop(seconds=0.5)
async def tracklist():
    bot_voice_client = discord.utils.get(bot.voice_clients, guild= abc)
    print(queue)
    if bot_voice_client.is_paused():
        pass
    elif bot_voice_client == None or bot_voice_client.is_playing() == False:
        current_timestamp = 0
        if bot_voice_client == None:
            vc = await discord.object(voice_channel).connect()
            vc.play(discord.FFmpegOpusAudio(source=jsondata(queue[0]).get("file")))
        elif len(queue) == 0:
            queue = random.shuffle(played_sets)
        elif len(queue) > 0:
            played_sets.append(queue.pop(0))
            file = jsondata(queue[0]).get("file")
            ffmpegcheck = os.system(f'ffprobe -i {file} -show_entries format=duration -of csv="p=0" > time.txt')
            if ffmpegcheck == 1:
                raise FileNotFoundError
            with open("time.txt",'r') as myfile:
                time_sec = float(str(myfile.readlines()[0]).strip())    
                time_hms = sec_to_hms(time_sec)
            vc.play(discord.FFmpegOpusAudio(source=jsondata(queue[0]).get("file")))
            await bot.get_channel(bot_voice_client).send(embed=discord.Embed(title =f"Now Playing `{queue[0].get('performer')}`", color=queue[0].get('color')))


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await queuebuild()    
    print("ready")
if __name__ == "__main__":
    try:
        bot.run(TOKEN, reconnect=True)
    except:
        raise