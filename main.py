
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
SERVER_ID = os.getenv('SERVER_ID')
PREFIX = os.getenv('PREFIX')
MOD_ID = os.getenv('MOD_ID')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, max_messages=10000)


queueList = []
qpos = -1
jsondata = {}
current_timestamp = 0
voice_channel = None
played_tracks = []
time_sec = None
time_hms = None
sid_played = True
sid_list = []
current_msgs = []
nofile = []



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
        m, s = mmss.split(":")
        return ((int(m) * 60) + int(s))
    except:
        return (f"{mmss} is not a number")


async def queue_build():
    mypath = "setlists"
    global new_sets
    new_sets = []
    nofile = []
    tracklists = sorted([f for f in os.listdir(
        mypath) if os.path.isfile(os.path.join(mypath, f))])
    # print()
    for set in tracklists:
        print(set)
        if not set in queueList:
            with open(mypath + "/" + set) as json_file:
                jsontemp = json.load(json_file)
                if "file" in jsontemp:
                    jsondata[set] = jsontemp
                    # print(jsondata)
                    queueList.append(set)
                    new_sets.append(set)
                    # print(new_sets)
                else:
                    nofile.append(set)
    print(f"Queue: {queueList} \n No File: {nofile}")
#    await sidbuild()

# async def sidbuild():
#     mypath = "sids"
#     global new_sids
#     global sid_vox_list
#     global sid_tracks_list
#     new_sids = []
#     sid_vox_list = [f for f in os.listdir(mypath + "vox") if os.path.isfile(os.path.join(mypath + "vox", f))]
#     sid_tracks_list = [f for f in os.listdir(mypath + "tracks") if os.path.isfile(os.path.join(mypath + "tracks", f))]
#     print(sid_vox_list, sid_tracks_list)

# MOD COMMANDS


@bot.command()
@commands.has_role(int(MOD_ID))
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("synced")


@bot.hybrid_command(name = "qbuild", with_app_command = True, description = "rebuilds queue")
@commands.has_role(int(MOD_ID))
async def qbuild(ctx: commands.Context):
    await queue_build()
    if new_sets != []:
        await ctx.send(str(new_sets))


@bot.hybrid_command(name = "showsets", with_app_command = True, description = "Show all sets currently in the database")
@commands.has_role(int(MOD_ID))
async def showsets(ctx: commands.Context):
    mypath = "setlists"
    tracklists = sorted(queueList)
    with open("sets.txt", "w") as setout:
        setout.writelines("\n".join(tracklists))
        if len(nofile) < 0:
            setout.write("\n\nSets with no audio file: \n")
            setout.writelines("\n".join(nofile))
    with open("sets.txt", "rb") as setout:
        await ctx.send(f"There are currently {len(tracklists)} sets: ", file=discord.File(setout, "sets.txt"))


@bot.command()
@commands.has_role(int(MOD_ID))
async def setadd(ctx, args, args2):

    builder = {}
    mypath = "setlists/"
    set = ctx.message.attachments[0]
    if not ctx.message.attachments[0]:
        ctx.send(embed=discord.Embed(description="No attachments found"))
    else:
        set_name = ctx.message.attachments[0].filename
        set_file = await ctx.message.attachments[0].save(mypath + set_name)
        ffmpegcheck = os.system(
            f'ffprobe -i {args2} -show_entries format=duration -of csv="p=0" > timequeue.txt')
        if ffmpegcheck == 1:
            raise FileNotFoundError
        with open("timequeue.txt", 'r') as myfile:
            j = myfile.readlines()[0].strip()
            set_length = float(j)
        with open(mypath + set_name, "r") as json_file:
            data = json.load(json_file)
            print(args, args2)
            if not "file" in data:
                # x,y = str(args).split()
                builder["uid"] = str(args)
                builder["file"] = str(args2)
                builder["set_len"] = set_length
                builder.update(data)
                # print(data)
                with open(mypath + set_name, "w") as json_file:
                    json.dump(builder, json_file, indent=2)
                await ctx.send(embed=discord.Embed(title=str(set_name), description=f"added:\n uid: {str(args)} \n length: sec: {str(set_length)}, mm:ss: {sec_to_hms(set_length)}  \n file: {str(args2)}"))
            elif "file" in data:
                data["file"]
                ctx.send(embed=discord.Embed(title=str(
                    set_name), description=f"already has: \n uid: {str(data['uid'])} \n file: {str(data['file'])}"))
            
        await queue_build()
        await ctx.send(embed=discord.Embed(title="added new sets:", description=str(new_sets)))


@bot.hybrid_command(name = "connect", with_app_command = True, description = "connect to vc")
@commands.has_role(int(MOD_ID))
async def connect(ctx: commands.Context, channel: Optional[discord.VoiceChannel]):
    print(ctx)
    try:
        #await ctx.defer()
        if channel:
            voice_channel = channel
        else:
            voice_channel = ctx.author.voice.channel
        await voice_channel.connect()
        global abc
        abc = ctx.guild
        await asyncio.sleep(1.5)
        await ctx.send(embed=discord.Embed(title=f"connected to {voice_channel.mention}"))
        await setplay.start(queueList, jsondata)
        
        print(voice_channel)
    except Exception as ex:
        #if type(ex) == AttributeError
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        await ctx.send(embed=discord.Embed(description="You are not in a voice channel", color=0x00aeff))


@bot.hybrid_command(name = "disconnect", with_app_command = True, description = "Disconnect from VC")
@commands.has_role(int(MOD_ID))
async def disconnect(ctx: commands.Context):
    try:
        bot_voice_client = discord.utils.get(
            bot.voice_clients, guild=ctx.guild)
        if bot_voice_client.source != None or bot_voice_client.is_playing() == True:
            bot_voice_client.stop()
            # allows the bot to properly end the file before disconnecting
            await asyncio.sleep(1.5)
        await bot_voice_client.disconnect()
        await ctx.send("disconnected from channel")
    except:
        # discord.utils.get(bot.voice_clients, guild=ctx.guild)
        await ctx.send(embed=discord.Embed(description="You are not in a voice channel", color=0x00aeff))


@bot.hybrid_command(name = "pause", with_app_command = True, description = "pause playback")
@commands.has_role(int(MOD_ID))
async def pause(ctx: commands.Context):
    try:
        bot_voice_client = discord.utils.get(
            bot.voice_clients, guild=ctx.guild)
        bot_voice_client.pause()
        await ctx.send("paused current set")
    except:
        await ctx.send("an error occured")


@bot.hybrid_command(name = "unpase", with_app_command = True, description = "unpause playback")
@commands.has_role(int(MOD_ID))
async def unpause(ctx: commands.Context):
    try:
        bot_voice_client = discord.utils.get(
            bot.voice_clients, guild=ctx.guild)
        bot_voice_client.resume()
        await ctx.send("resumed current set")
    except:
        await ctx.send("an error occured")


#@bot.hybrid_command(name = "seek", with_app_command = True, description ="jump to specific time")
@bot.command()
@commands.has_role(int(MOD_ID))
async def seek(ctx, text):
    if type(mmss_to_sec(text)) == int:
        global current_timestamp
        current_timestamp = mmss_to_sec(text)
        bot_voice_client = discord.utils.get(bot.voice_clients, guild=abc)
        bot_voice_client.source = discord.FFmpegOpusAudio(source=jsondata.get(
            queueList[qpos]).get("file"), before_options=f"-ss {str(mmss_to_sec(text))}")
        await ctx.send(f"seeked to {text}")
    elif type(mmss_to_sec(text)) != int:
        await ctx.send(f"{text} could not be converted to a time")

    else:
        await ctx.send("an error occured")


@bot.hybrid_command(name = "skip", with_app_command = True, description = "skip set")
@commands.has_role(int(MOD_ID))
async def skip(ctx: commands.Context):
    bot_voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    bot_voice_client.stop()
    await ctx.send(embed=discord.Embed(description="File skipped", color=0x00aeff))


@bot.hybrid_command(name = "shuffle", with_app_command = True, description = "shuffle queue")
@commands.has_role(int(MOD_ID))
async def shuffle(ctx: commands.Context):
    print("old", queueList)
    random.shuffle(queueList)
    print("new", queueList)

    bot_voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    bot_voice_client.stop()

    await ctx.send(embed=discord.Embed(title="Shuffled Queue"))


# USER COMMANDS

@bot.hybrid_command(name = "queue", with_app_command = True, description = "view queue")
async def queue(ctx: commands.Context, page: Optional[int] = 1):
    j = 0
    timeleft = time_sec - current_timestamp
    msg = ""
    global qpos
    global settime_sec
    settime_sec = [0]
    if page < 1:
        page = 1
    page_len = 6
    k = (page_len*page) - page 
    while j < k and j < len(queueList) - qpos:
        #        print("-------------")
        file = jsondata.get(queueList[qpos+j]).get("file")
        if j == 0:
            settime_sec[0] = jsondata.get(queueList[qpos]).get("set_len")
            next_time = timeleft
            time_out = math.ceil(next_time + time.time())
            if queueList[qpos+j][0].isdigit():
                set_title = f"DJ {jsondata.get(queueList[qpos+j]).get('set')}"
            else:
                set_title = f"{jsondata.get(queueList[qpos+j]).get('set')}"
            if j > k-page_len: 
                msg = f"**Now Playing: {jsondata.get(queueList[qpos+j]).get('performer')} - {set_title}** \n "
        else:
            settime_sec.append(jsondata.get(queueList[qpos]).get("set_len"))
            if queueList[qpos+j][0].isdigit():
                set_title = f"DJ {jsondata.get(queueList[qpos+j]).get('set')}"
            else:
                set_title = f"{jsondata.get(queueList[qpos+j]).get('set')}"
            time_out = round(next_time + time.time())
            if j > k-page_len: 
                msg = msg + f"**{j}.** {jsondata.get(queueList[qpos+j]).get('performer')} - {set_title} <t:{time_out}:R>, <t:{time_out}:t> \n "
            next_time = math.ceil(next_time + settime_sec[j])
        j += 1
    await ctx.send(embed=discord.Embed(title="Queue:", description=msg).set_footer(text=f"{page}/{math.ceil((len(queueList)-qpos)/(page_len-1))}"))


@bot.hybrid_command(name = "setqueue", with_app_command = True, description ="see the upcoming songs in set")
async def setqueue(ctx: commands.Context):
    j = 1
    # timeleft= time_sec - current_timestamp
    msg = ""
    global qpos
    timeleft = time_sec - current_timestamp
    global settime_sec
    settime_sec = [0]
    next_time = 0

    # print(len(played_tracks))
    print(current_timestamp)
    setq_left = len(jsondata.get(queueList[qpos]).get("tracks")) - len(played_tracks)
    while j < 6 and j < setq_left:
        k = j + len(played_tracks)

        file = jsondata.get(queueList[qpos]).get("file")
        print(settime_sec)
        print(j)
        print(k)

        if j == 1:
            
            settime_sec[0] = jsondata.get(queueList[qpos]).get("set_len")
            next_time = timeleft
            msg = ("Now Playing" + ": " + jsondata.get(queueList[qpos]).get("tracks").get(str(k-1)).get("artist") + " - " + jsondata.get(queueList[qpos]).get("tracks").get(str(k-1)).get("title") + "\n")

        else:
            settime_sec.append(jsondata.get(queueList[qpos]).get("set_len"))
            msg = msg + (str(j-1) + ": " + jsondata.get(queueList[qpos]).get("tracks").get(str(k-1)).get("artist") + " - " + jsondata.get(queueList[qpos]).get("tracks").get(str(k-1)).get("title") + "\n")

            next_time = math.ceil(next_time + settime_sec[j-1])

        j += 1

    await ctx.send(embed=discord.Embed(title="Queue:", description=msg))


@bot.hybrid_command(name = "np", with_app_command = True, description ="see now playing track")
async def np(ctx: commands.Context):
    title = f"Now playing `{now_playing.get('artist')} - {now_playing.get('title')}`"
    if queueList[qpos][0].isdigit():
        set_title = f"Dischead Jockeys {jsondata.get(queueList[qpos]).get('set')}"
    else:
        set_title = f"{jsondata.get(queueList[qpos]).get('set')}"

    desc = f"{set_title}, performed by `{jsondata.get(queueList[qpos]).get('performer')}` \n {sec_to_hms(current_timestamp)}/{time_hms}"
    color_hold = jsondata.get(queueList[qpos]).get('color')
    color = int(color_hold[1:], 16)
    await ctx.send(embed=discord.Embed(title=title, description=desc, color=color))

@bot.hybrid_command(name = "socials", with_app_command = True, description ="socials of performer")
async def socials(ctx: commands.Context):
    socials = jsondata.get(queueList[qpos]).get('socials')
    desc = ""
    color_hold = jsondata.get(queueList[qpos]).get('color')
    color = int(color_hold[1:], 16)
    for i in socials:
        if socials.get(i):
            print(i, socials.get(i))
            if i == "setlink":
                j = "set link"
            else:
                j = i
            desc = desc + (f"[{j}]({socials.get(i)}) \n")
    await ctx.send(embed=discord.Embed(title=f"{jsondata.get(queueList[qpos]).get('performer')} Socials:", description=desc, color=color))

@bot.hybrid_command(name = "about", with_app_command = True, description ="about the bot")
async def about(ctx: commands.Context):
    kyllian_user = bot.get_user(264585115726905346)
    info_message_embed = discord.Embed(
        title=f"Jockey • Bot by {kyllian_user.name}#{(kyllian_user.discriminator)}", color=0x00aeff, timestamp=datetime.datetime.now())
    info_message_embed.set_thumbnail(url=kyllian_user.avatar.url)
    info_message_embed.set_footer(
        text=f"© 2023 Toxin_X", icon_url=bot.user.avatar.url)
    await ctx.send(embed=info_message_embed)


@tasks.loop(seconds=0.5)
async def setplay(queueList, jsondata):
    bot_voice_client = discord.utils.get(bot.voice_clients, guild=abc)
    global current_timestamp
    global qpos
    global played_tracks
    global sid_played
    global current_msgs
    if bot_voice_client.is_paused():
        pass
    elif bot_voice_client == None or bot_voice_client.is_playing() == False:
        current_timestamp = 0
        played_tracks = []
        if sid_played == True:
            qpos += 1
        # print(queueList)
        if bot_voice_client == None:
            vc = await discord.object(voice_channel).connect()
            vc.play(discord.FFmpegOpusAudio(
                source=jsondata.get(queueList[qpos]).get("file")))
        elif qpos >= len(queueList):
            random.shuffle(queueList)
            qpos = -1
        elif qpos < len(queueList):
            # print(qpos)
            if sid_played == True:
                global time_sec
                time_sec = jsondata.get(queueList[qpos]).get("set_len")
                global time_hms
                time_hms = sec_to_hms(time_sec)
                color_hold = jsondata.get(queueList[qpos]).get('color')
                color = int(color_hold[1:], 16)
                # print(queueList[qpos])

                if queueList[qpos][0].isdigit():
                    set_title = f"Dischead Jockeys {jsondata.get(queueList[qpos]).get('set')}"
                else:
                    set_title = f"{jsondata.get(queueList[qpos]).get('set')}"

                bot_voice_client.play(discord.FFmpegOpusAudio(
                    source=jsondata.get(queueList[qpos]).get("file")))
                await bot_voice_client.channel.send(embed=discord.Embed(title=f"Now Playing `{jsondata.get(queueList[qpos]).get('performer')} - {set_title}` ", description=f"Originally aired on:  `{jsondata.get(queueList[qpos]).get('date')}`", color=color))
                await socials(bot_voice_client.channel)
                sid_played = False
                # for j in current_msgs:
                #     await j.delete()
                #     asyncio.sleep(1)
            else:
                with open("sids/sids.json") as jsonfile:
                    data = json.load(jsonfile)
                    voxpath="sids/vox"
                    voxfolder = sorted([f for f in os.listdir(voxpath) if os.path.isfile(os.path.join(voxpath, f))])

                rand_track = random.choice(data.get("tracks"))
                file = rand_track.get("file")
                pos = rand_track.get("pos")
                has_vox = rand_track.get("vox")
                rand_vox = os.path.join(voxpath, random.choice(voxfolder))

                if rand_vox.endswith("silent_half-second.mp3"):
                    has_vox = 0

                if has_vox == 1:
                    bot_voice_client.play(discord.FFmpegOpusAudio(source=f"{rand_vox}", before_options=f"-i {file}", options=f'-filter_complex "[0]adelay=0:all=1,volume=0.85[0a];[1]adelay={pos}:all=1,volume=1.35[1a];[0a][1a]amix=inputs=2[a]" -map "[a]"'))
                else:
                    bot_voice_client.play(discord.FFmpegOpusAudio(source=f"{file}", options='-filter_complex "volume=0.6"'))
                sid_played = True
    else:
        current_timestamp += 0.5
        # print(jsondata.get(queueList[qpos]).get("tracks"))
        # print(sec_to_hms(current_timestamp))
        for i in jsondata.get(queueList[qpos]).get("tracks"):
            track_timestamp = mmss_to_sec(jsondata.get(
                queueList[qpos]).get("tracks").get(i).get("timestamp"))
            # print(i)
            # print(played_tracks)
            if not i in played_tracks and sid_played == False:
                track = jsondata.get(queueList[qpos]).get("tracks").get(i)
                # print(current_timestamp, time, track)
                # print(played_tracks)
                if current_timestamp > float(track_timestamp):
                    global now_playing
                    now_playing = track
                    played_tracks.append(i)
                    if queueList[qpos][0].isdigit():
                        set_title = f"Dischead Jockeys {jsondata.get(queueList[qpos]).get('set')}"
                    else:
                        set_title = f"{jsondata.get(queueList[qpos]).get('set')}"

                    title = f"Now playing `{track.get('artist')} - {track.get('title')}`"
                    desc = f"{set_title}, performed by `{jsondata.get(queueList[qpos]).get('performer')}` \n {sec_to_hms(current_timestamp)}/{time_hms}"
                    color_hold = jsondata.get(queueList[qpos]).get('color')
                    color = int(color_hold[1:], 16)
                    msg = await bot_voice_client.channel.send(embed=discord.Embed(title=title, description=desc, color=color))
                    current_msgs.append(msg)
                    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{track.get('artist')} - {track.get('title')}"))


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await queue_build()
    # await sidbuild()
    random.shuffle(queueList)
    print(len(queueList), queueList)
    print("ready")
if __name__ == "__main__":
    try:
        bot.run(TOKEN, reconnect=True)
    except:
        raise
