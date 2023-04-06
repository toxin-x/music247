import json
import os
import math

builder = {}
mypath = "setlists"
setlists = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f)) ]

for set in setlists:
    
    with open(mypath + "/" + set, "r") as json_file:
        data = json.load(json_file)
        builder = {}
        print(data)
        if not "file" in data:
                    
            x,y = str(input(set + " id and audio: ")).split()
            builder["uid"] = str(x)
            builder["file"] = str(y)
            builder.update(data)
            #print(data)
            print(builder)
            with open(mypath + "/" + set, "w") as json_file:
                json.dump(builder, json_file, indent = 2)
        if not "time_len" in data: 
            ffmpegcheck = os.system(f'ffprobe -i {data["file"]} -show_entries format=duration -of csv="p=0" > timequeue.txt')
            if ffmpegcheck == 1:
                raise FileNotFoundError
            with open("timequeue.txt", 'r') as myfile:
                set_length = float(str(myfile.readlines()[0]).strip())
                builder["set_len"] = set_length
                builder.update(data)
                print(builder)
                print(set_length, data["performer"])
                with open(mypath + "/" + set, "w") as json_file:
                    json.dump(builder, json_file, indent = 2)

                