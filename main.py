import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import bot
from dotenv import load_dotenv
import os
import json
from typing import Optional
import random

load_dotenv()
TOKEN = os.getenv('TOKEN')
OWNER_ID = os.getenv('OWNER_ID')
SERVER_ID =os.getenv('SERVER_ID')
VC_ID = os.getenv('VC_ID')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, max_messages=10000, help_command=None)

queue = []
played = []
jsondata = {}
current_timestamp=0


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
            
    #print(jsondata)
    queue.append(set)
    #print(jsondata[queue[0]].get("color"))


# @tasks.loop(seconds=0.5)
# async def tracklisting():
#     if queue != []:
#         i = 1
#         qdata = jsondata[queue[0]]
        
#         while i < len(qdata.get("tracks")):
#             if i.get("timestamp") > current_timestamp:
#             print(i, len(qdata.get("tracks")))
#             print(qdata.get("tracks").get(str(i)))
#             i += 1

@tasks.loop(seconds=0.5)
async def play():
    vc = discord.utils.get(bot.voice_clients, guild=discord.object(SERVER_ID))
    
    if vc.is_paused():
        pass
    elif vc.source() == None or vc.is_playing() == False:
        current_timestamp = 0
        if vc.source == None:
           vv = await discord.object(VC_ID).connect()
           vv.play(discord.FFmpegOpusAudio(source=jsondata(queue[0]).get("file")))
        elif len(queue) == 0:
            queue = random.shuffle(played)
            await play()
        elif len(queue) > 0:
            played.append(queue.pop(0))
            file = jsondata(queue[0]).get("file")
            ffmpegcheck = os.system(f'ffprobe -i {file} -show_entries format=duration -of csv="p=0" > time.txt')
            if ffmpegcheck == 1:
                raise FileNotFoundError
            with open("time.txt",'r') as myfile:
                time_sec = float(str(myfile.readlines()[0]).strip())    
                time_hms = sec_to_hms(time_sec)
            vc.play(discord.FFmpegOpusAudio(source=jsondata(queue[0]).get("file")))
            await bot.get_channel(VC_ID).send(embed=discord.Embed(title =f"Now Playing `{queue[0].get('title')}`", description=f"{queue[0].get('desc')} \n", color=0x00aeff))
    else:
        current_timestamp += 0.5




@app_commands.command(name="test", description="test")
async def test(self):
    event_text = VC_ID
    self.bot.get_channel(event_text).send(embed = discord.Embed(title =f"Now Playing", description=f"hi"))


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await queuebuild()
    #await tracklisting.start()
    
    # bot.synced=False
    
    # if not bot.synced:
    #     await bot.tree.sync()
    #     bot.tree.copy_global_to(guild = discord.Object(id = 1001619464401457253))
    #     bot.synced = True
    
        
if __name__ == "__main__":
    try:
        bot.run(TOKEN, reconnect=True)
    except:
        raise