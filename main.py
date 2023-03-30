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
qpos = -1
jsondata = {}
current_timestamp = 0
voice_channel = None
played_tracks = []
time_hms= None

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
    try:
        m,s = mmss.split(":")
        return((int(m) * 60)+ int(s))
    except:
        return(f"{mmss} is not a number")

async def queuebuild():
    mypath = "setlists"
    tracklists = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f)) ]
    for set in tracklists:

        with open(mypath + "/" + set) as json_file:
            jsondata[set] = json.load(json_file)
            #print(jsondata)
            queue.append(set)
    #print(queue)
    
@bot.command()
async def join(ctx):
    try:
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect()
        global abc 
        abc = ctx.guild
        await asyncio.sleep(1.5)
        await setplay.start(queue, jsondata)
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

@bot.command()
async def seek(ctx, text):
    if type(mmss_to_sec(text)) == int:
        global current_timestamp
        current_timestamp = mmss_to_sec(text)
        bot_voice_client = discord.utils.get(bot.voice_clients, guild= abc)
        bot_voice_client.source = discord.FFmpegOpusAudio(source=jsondata.get(queue[qpos]).get("file"), before_options=f"-ss {str(mmss_to_sec(text))}")
    
        await ctx.send(f"seeked to {text}")
    elif type(mmss_to_sec(text)) != int:
        await ctx.send(f"{text} could not be converted to a time")
    
    else: 
        await ctx.send("an error occured")


@tasks.loop(seconds=0.5)
async def setplay(queue, jsondata):
    bot_voice_client = discord.utils.get(bot.voice_clients, guild= abc)
    global current_timestamp
    global qpos
    global played_tracks
    print(queue, str(qpos))
    if bot_voice_client.is_paused():
        pass
    elif bot_voice_client == None or bot_voice_client.is_playing() == False:
        current_timestamp = 0
        qpos += 1
        played_tracks=[]
        #print(queue)
        if bot_voice_client == None:
            vc = await discord.object(voice_channel).connect()
            vc.play(discord.FFmpegOpusAudio(source=jsondata.get(queue[qpos]).get("file")))
        elif qpos >= len(queue):    
            random.shuffle(queue)
            qpos = -1
        elif qpos < len(queue):

            file = jsondata.get(queue[qpos]).get("file")
            ffmpegcheck = os.system(f'ffprobe -i {file} -show_entries format=duration -of csv="p=0" > time.txt')
            if ffmpegcheck == 1:
                raise FileNotFoundError
            with open("time.txt",'r') as myfile:
                time_sec = float(str(myfile.readlines()[0]).strip())
                global time_hms    
                time_hms = sec_to_hms(time_sec)
            color_hold = jsondata.get(queue[qpos]).get('color')     
            color = int(color_hold[1:], 16)
            #print(jsondata.get(queue[qpos]).get("file"))
            bot_voice_client.play(discord.FFmpegOpusAudio(source=jsondata.get(queue[qpos]).get("file")))
            await bot_voice_client.channel.send(embed=discord.Embed(title =f"Now Playing `{jsondata.get(queue[qpos]).get('performer')} - Dischead Jockeys {jsondata.get(queue[qpos]).get('set')}` ", description=f"Originally aired on:  `{jsondata.get(queue[qpos]).get('date')}`", color = color))
    else:
        current_timestamp += 0.5
        #print(jsondata.get(queue[qpos]).get("tracks"))
        #print(sec_to_hms(current_timestamp))
        for i in jsondata.get(queue[qpos]).get("tracks"):
            time = mmss_to_sec(jsondata.get(queue[qpos]).get("tracks").get(i).get("timestamp"))
            #print(i)
            #print(played_tracks)
            if not i in played_tracks:
                track = jsondata.get(queue[qpos]).get("tracks").get(i)
                #print(current_timestamp, time, track)
                #print(played_tracks)
                if current_timestamp > float(time):
                        played_tracks.append(i)
                        title = f"Now playing `{track.get('artist')} - {track.get('title')}`"
                        desc = f"Dischead Jockeys {jsondata.get(queue[qpos]).get('set')}, performed by `{jsondata.get(queue[qpos]).get('performer')}` \n {sec_to_hms(current_timestamp)}/{time_hms}"
                        color_hold = jsondata.get(queue[qpos]).get('color')     
                        color = int(color_hold[1:], 16)
                        await bot_voice_client.channel.send(embed=discord.Embed(title = title, description=desc, color = color))
                        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{track.get('artist')} - {track.get('title')}"))


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