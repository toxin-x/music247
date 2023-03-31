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
import time
import datetime
import math


load_dotenv()

if not os.path.exists("setlists"):
    os.mkdir("setlists")

if not os.path.exists("sids"):
    os.mkdir("sids")


TOKEN = os.getenv('TOKEN')
OWNER_ID = os.getenv('OWNER_ID')
SERVER_ID =os.getenv('SERVER_ID')
PREFIX = os.getenv('PREFIX')
MOD_ID = os.getenv('MOD_ID')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, max_messages=10000, help_command=None)

queue = []
qpos = -1
jsondata = {}
current_timestamp = 0
voice_channel = None
played_tracks = []
time_sec= None
time_hms= None
sid_played = True
sid_list = []
current_msgs = []


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
    global new_sets
    new_sets = [] 
    tracklists = sorted([f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f)) ])
    #print()
    for set in tracklists:
        print(set)
        if not set in queue:
            with open(mypath + "/" + set) as json_file:
                jsondata[set] = json.load(json_file)
                #print(jsondata)
                queue.append(set)
                new_sets.append(set)    
                #print(new_sets)

async def sidbuild():
    mypath = "sids"
    global new_sids
    global sid_list
    new_sids = [] 
    sid_list = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f)) ]
    print(sid_list)
    # for sid in sids:
    #     if not sid in sid_list:
    #         print(sid_list)
    #         sid_list.append(sid)
    #         new_sids.append(sid)    
    #         print(new_sids)




#MOD COMMANDS
@bot.command()
@commands.has_role(int(MOD_ID))
async def qbuild(ctx):
    await queuebuild()
    
    await ctx.send(str(new_sets))


@bot.command()
@commands.has_role(int(MOD_ID))
async def setadd(ctx, args, args2):
        
        builder = {}
        mypath = "setlists/"
        set = ctx.message.attachments[0]
        set_name = ctx.message.attachments[0].filename
        set_file = await ctx.message.attachments[0].save(mypath + set_name)
        
        with open(mypath + set_name, "r") as json_file:
            data = json.load(json_file)
            print(args, args2)
            if not "file" in data:
                #x,y = str(args).split()
                builder["uid"] = str(args)
                builder["file"] = str(args2)
                builder.update(data)
                #print(data)
                with open(mypath + "/" + set_name, "w") as json_file:
                    json.dump(builder, json_file, indent = 2)
                await ctx.send(embed=discord.Embed(description=f"added uid: {str(args)} \n file: {str(args2)}"))




@bot.command()
@commands.has_role(int(MOD_ID))
async def join(ctx):
    try:
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect()
        global abc 
        abc = ctx.guild
        await asyncio.sleep(1.5)
        await setplay.start(queue, jsondata)
    except:
        await ctx.send(embed=discord.Embed(description="You are not in a voice channel", color=0x00aeff))

@bot.command()
@commands.has_role(int(MOD_ID))
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
        await ctx.send(embed=discord.Embed(description="You are not in a voice channel", color=0x00aeff))

@bot.command()
@commands.has_role(int(MOD_ID))
async def pause(ctx):
    try:
        bot_voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        bot_voice_client.pause()
        await ctx.send("paused current set")
    except:
        await ctx.send("an error occured")
        
@bot.command()
@commands.has_role(int(MOD_ID))
async def unpause(ctx):
    try:
        bot_voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        bot_voice_client.resume()
        await ctx.send("resumed current set")
    except:
        await ctx.send("an error occured")

@bot.command()
@commands.has_role(int(MOD_ID))
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

@bot.command()
@commands.has_role(int(MOD_ID))
async def skip(ctx):
        bot_voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        bot_voice_client.stop()
        await ctx.send(embed=discord.Embed(description="File skipped", color=0x00aeff))
        
@bot.command()
@commands.has_role(int(MOD_ID))
async def shuffle(ctx):
    print("old", queue)
    random.shuffle(queue)
    print("new", queue)
    
    bot_voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    bot_voice_client.stop()

    await ctx.send(embed=discord.Embed(title="Shuffled Queue"))
    
    
#USER COMMANDS

@bot.command()
async def q(ctx):
    j=0
    timeleft= time_sec - current_timestamp
    msg = ""
    global qpos
    global settime_sec
    settime_sec = [0]
    while j < 6 and j < len(queue) - qpos:
#        print("-------------")
        file = jsondata.get(queue[qpos+j]).get("file")
        ffmpegcheck = os.system(f'ffprobe -i {file} -show_entries format=duration -of csv="p=0" > timequeue.txt')
        if ffmpegcheck == 1:
            raise FileNotFoundError        
        if j == 0:
            with open("timequeue.txt",'r') as myfile:
                settime_sec[0] = (float(str(myfile.readlines()[0]).strip()))
            next_time = timeleft
            time_out = math.ceil(next_time + time.time())
            if queue[qpos+j][0].isdigit():
                set_title = f"DJ {jsondata.get(queue[qpos+j]).get('set')}"
            else:
                set_title = f"{jsondata.get(queue[qpos+j]).get('set')}" 
            msg = f"**Now Playing: {jsondata.get(queue[qpos+j]).get('performer')} - {set_title}** \n " 
        else:
            with open("timequeue.txt",'r') as myfile:
                settime_sec.append(float(str(myfile.readlines()[0]).strip()))
            if queue[qpos+j][0].isdigit():
                set_title = f"DJ {jsondata.get(queue[qpos+j]).get('set')}"
            else:
                set_title = f"{jsondata.get(queue[qpos+j]).get('set')}" 
            time_out = math.ceil(next_time + time.time()) 
            msg = msg + f"**{j}.** {jsondata.get(queue[qpos+j]).get('performer')} - {set_title} <t:{time_out}:R>, <t:{time_out}:t> \n "
            next_time = math.ceil(next_time + settime_sec[j])
        j+=1
    await ctx.send(embed=discord.Embed(title="Queue:", description=msg))
    
@bot.command()
async def setq(ctx):
    j=1
    #timeleft= time_sec - current_timestamp
    msg = ""
    global qpos
    timeleft= time_sec - current_timestamp
    global settime_sec
    settime_sec = [0]
    next_time = 0

    #print(len(played_tracks))
    print(current_timestamp)
    setq_left = len(jsondata.get(queue[qpos]).get("tracks")) - len(played_tracks)
    while j < 6 and j < setq_left:
        k = j + len(played_tracks)
        
        file = jsondata.get(queue[qpos]).get("file")
        ffmpegcheck = os.system(f'ffprobe -i {file} -show_entries format=duration -of csv="p=0" > timequeue.txt')
        print(settime_sec)
        print(j)
        print(k)
        
        if ffmpegcheck == 1:
            raise FileNotFoundError 
        
        if j == 1:
            with open("timequeue.txt",'r') as myfile:
                settime_sec[0] = (float(str(myfile.readlines()[0]).strip())) 
            next_time = timeleft
            msg = ("Now Playing" + ": " + jsondata.get(queue[qpos]).get("tracks").get(str(k-1)).get("artist") + " - " + jsondata.get(queue[qpos]).get("tracks").get(str(k-1)).get("title") + "\n")
        
        else:
            with open("timequeue.txt",'r') as myfile:
                settime_sec.append(float(str(myfile.readlines()[0]).strip()))
            msg = msg + (str(j-1) + ": " + jsondata.get(queue[qpos]).get("tracks").get(str(k-1)).get("artist") + " - " + jsondata.get(queue[qpos]).get("tracks").get(str(k-1)).get("title") + "\n")
            
            next_time = math.ceil(next_time + settime_sec[j-1])
        
        j += 1
    
    await ctx.send(embed=discord.Embed(title="Queue:", description=msg))

@bot.command()
async def np(ctx):
    title = f"Now playing `{now_playing.get('artist')} - {now_playing.get('title')}`"
    if queue[qpos][0].isdigit():
        set_title = f"Dischead Jockeys {jsondata.get(queue[qpos]).get('set')}"
    else:
        set_title = f"{jsondata.get(queue[qpos]).get('set')}"
    
    desc = f"{set_title}, performed by `{jsondata.get(queue[qpos]).get('performer')}` \n {sec_to_hms(current_timestamp)}/{time_hms}"
    color_hold = jsondata.get(queue[qpos]).get('color')     
    color = int(color_hold[1:], 16)
    await ctx.send(embed=discord.Embed(title = title, description=desc, color = color))


@bot.command()
async def about(ctx):
            
            kyllian_user = bot.get_user(264585115726905346)
            info_message_embed = discord.Embed(title=f"Jockey • Bot by {kyllian_user.name}#{(kyllian_user.discriminator)}", color=0x00aeff, timestamp=datetime.datetime.now())
            info_message_embed.set_thumbnail(url=kyllian_user.avatar.url)
            info_message_embed.set_footer(text=f"© 2023 Toxin_X", icon_url=bot.user.avatar.url)
            await ctx.send(embed=info_message_embed)




@tasks.loop(seconds=0.5)
async def setplay(queue, jsondata):
    bot_voice_client = discord.utils.get(bot.voice_clients, guild= abc)
    global current_timestamp
    global qpos
    global played_tracks
    global sid_played
    global current_msgs
    if bot_voice_client.is_paused():
        pass
    elif bot_voice_client == None or bot_voice_client.is_playing() == False:
        current_timestamp = 0
        played_tracks=[]
        if sid_played == True:
            qpos += 1
        #print(queue)
        if bot_voice_client == None:
            vc = await discord.object(voice_channel).connect()
            vc.play(discord.FFmpegOpusAudio(source=jsondata.get(queue[qpos]).get("file")))
        elif qpos >= len(queue):    
            random.shuffle(queue)
            qpos = -1
        elif qpos < len(queue):
            #print(qpos)
            if sid_played == True:
                file = jsondata.get(queue[qpos]).get("file")
                ffmpegcheck = os.system(f'ffprobe -i {file} -show_entries format=duration -of csv="p=0" > time.txt')
                if ffmpegcheck == 1:
                    raise FileNotFoundError
                with open("time.txt",'r') as myfile:
                    global time_sec
                    time_sec = float(str(myfile.readlines()[0]).strip())
                    global time_hms    
                    time_hms = sec_to_hms(time_sec)
                color_hold = jsondata.get(queue[qpos]).get('color')     
                color = int(color_hold[1:], 16)
                #print(queue[qpos])
               
                if queue[qpos][0].isdigit():
                    set_title = f"Dischead Jockeys {jsondata.get(queue[qpos]).get('set')}"
                else:
                    set_title = f"{jsondata.get(queue[qpos]).get('set')}"
                
                bot_voice_client.play(discord.FFmpegOpusAudio(source=jsondata.get(queue[qpos]).get("file")))
                await bot_voice_client.channel.send(embed=discord.Embed(title =f"Now Playing `{jsondata.get(queue[qpos]).get('performer')} - {set_title}` ", description=f"Originally aired on:  `{jsondata.get(queue[qpos]).get('date')}`", color = color))
                sid_played = False
                # for j in current_msgs:
                #     await j.delete()
                #     asyncio.sleep(1)
            else:
                id_file = random.choice(sid_list)
                bot_voice_client.play(discord.FFmpegOpusAudio(source= f"sids/{id_file}"))
                #print(id_file)
                sid_played=True
    else:
        current_timestamp += 0.5
        #print(jsondata.get(queue[qpos]).get("tracks"))
        #print(sec_to_hms(current_timestamp))
        for i in jsondata.get(queue[qpos]).get("tracks"):
            track_timestamp = mmss_to_sec(jsondata.get(queue[qpos]).get("tracks").get(i).get("timestamp"))
            #print(i)
            #print(played_tracks)
            if not i in played_tracks:
                track = jsondata.get(queue[qpos]).get("tracks").get(i)
                #print(current_timestamp, time, track)
                #print(played_tracks)
                if current_timestamp > float(track_timestamp):
                        global now_playing
                        now_playing = track
                        played_tracks.append(i)
                        if queue[qpos][0].isdigit():
                            set_title = f"Dischead Jockeys {jsondata.get(queue[qpos]).get('set')}"
                        else:
                            set_title = f"{jsondata.get(queue[qpos]).get('set')}"
                        
                        title = f"Now playing `{track.get('artist')} - {track.get('title')}`"
                        desc = f"{set_title}, performed by `{jsondata.get(queue[qpos]).get('performer')}` \n {sec_to_hms(current_timestamp)}/{time_hms}"
                        color_hold = jsondata.get(queue[qpos]).get('color')     
                        color = int(color_hold[1:], 16)
                        msg = await bot_voice_client.channel.send(embed=discord.Embed(title = title, description=desc, color = color))
                        current_msgs.append(msg)
                        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{track.get('artist')} - {track.get('title')}"))


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await queuebuild()
    await sidbuild()    
    print("ready")
if __name__ == "__main__":
    try:
        bot.run(TOKEN, reconnect=True)
    except:
        raise