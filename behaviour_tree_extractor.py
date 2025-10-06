import json
from bson import json_util

root_behaviours = []
all_behaviours = {}
all_behaviour_outputs = {}

def get_tree(tag):
    tree = []
    next_data = all_behaviour_outputs[tag]
    while next_data != []:
        tree.append(next_data)
        nd = []
        for x in next_data:
            for y in all_behaviour_outputs[x]:
                nd.append(y)
        next_data = nd
    return tree

with open('results/data.json', 'r') as file:
    data = json.load(file)

    # Get all root behaviours
    for x in data["ZBEHAVIOURDATA"]:
        if x["ZISROOT"] == 1:
            root_behaviours.append(x["ZTAG"])

        if "outputs" in x["ZACTIONS"]:
            all_behaviour_outputs[x["ZTAG"]] = x["ZACTIONS"]["outputs"]["NS.objects"]
        else:
            all_behaviour_outputs[x["ZTAG"]] = []

    all_trees = {}
    for x in root_behaviours:
        all_trees[x] = get_tree(x)

    with open('results/all_behaviour_trees.json', 'a') as f:
        f.write(json_util.dumps(all_trees))
                

    
    