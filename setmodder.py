import json
import os

builder = {}
mypath = "setlists"
setlists = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f)) ]

for set in setlists:
    with open(mypath + "/" + set, "r") as json_file:
        data = json.load(json_file)
        if not "file" in data:
            x,y = str(input(set + " id and audio: ")).split()
            builder["uid"] = str(x)
            builder["file"] = str(y)
            builder.update(data)
            #print(data)
            print(builder)
            with open(mypath + "/" + set, "w") as json_file:
                json.dump(builder, json_file, indent = 2)