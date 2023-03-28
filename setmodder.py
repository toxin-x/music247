import json
import os


mypath = "setlists"
setlists = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f)) ]

for set in setlists:
    with open(mypath + "/" + set) as json_file:
        data = json.load(json_file)
        if not "file" in data:
            x = input(set + " audio: ")
            data["file"] = x
            
            with open(mypath+"/"+set, "w") as json_file:
                json.dump(json_file, data, indent=2)
