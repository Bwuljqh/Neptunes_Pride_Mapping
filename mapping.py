# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 13:56:58 2022

@author: Bwuljqh
"""

import matplotlib.pyplot as plt
import requests
import json

from numpy import  sqrt

def getJsons(game_number, 
             codes, 
             api_version, 
             url = "https://np.ironhelmet.com/api"):
    """Returns a list of values collected via the api"""
    
    jsons = []
    
    for i in codes:
        keys = {"api_version": api_version, "game_number": game_number, "code": i}
        req = requests.post(url, data = keys)
        jsons.append(req.json())
    return jsons


def getValues(jsons):
    """Retrieve stars values from a list of jsons from the Neptune's Pride Api"""
    if type(jsons) != list:
        jsons = [jsons]
    
    # xs = []
    # ys = []
    
    # sts = []
    # nrs = []
    # trs = []
    
    # player = []
    
    number_player = len(jsons[0]['scanning_data']['players'])
    
    data = {"stars" : dict(), "fleets": dict()}
    data["nb_player"] = number_player
    for i in jsons:
        i['scanning_data']['players']['-1'] = {'tech': {'terraforming': {'value':0}}}
        
        for j in i['scanning_data']['stars'].values():
            data["stars"][j['uid']] = {"x" : float(j["x"]),
                               "y" : float(j["y"]),
                               "st" : j["st"],
                               "nr" : j["nr"],
                               "puid" : j["puid"],
                               "uid" : j["uid"],
                               "tr" : i['scanning_data']['players'][str(j['puid'])]['tech']['terraforming']['value']}
            
        for j in i["scanning_data"]['fleets'].values():
            data["fleets"][j['uid']] = {"x" : float(j["x"]),
                               "y" : float(j["y"]),
                               "st" : j["st"],
                               "uid" : j["uid"],
                               "orders": j['o'],
                               "puid" : j["puid"]}
            if "ouid" in j:
                data["fleets"][j['uid']]["ouid"] = j['ouid']

    # for i in jsons:
    #     values = i['scanning_data']['stars'].values()
    #     tempX = [float(j['x']) for j in values]
    #     tempY = [float(j['y']) for j in values]
        
    #     tempSt = [j['st'] for j in values]
    #     tempNr = [j['nr'] for j in values]
    #     i['scanning_data']['players']['-1'] = {'tech': {'terraforming': {'value':0}}}
    #     tempTr = [i['scanning_data']['players'][str(j['puid'])]['tech']['terraforming']['value']*5 for j in values]
       
    #     tempPlayer = [j['puid'] for j in values]
             
    #     xs += tempX
    #     ys += tempY
        
    #     nrs += tempNr
    #     sts += tempSt
    #     trs += tempTr

    #     player += tempPlayer

    labels = [jsons[0]['scanning_data']['players'][str(j)]['alias'] for j in range(number_player)]
    labels += ['Neutral']
    
    data["labels"] = labels
    
    # return {"xs":xs, "ys": ys, "sts":sts, "nrs":nrs,"trs":trs,"player": player, "labels": labels, "nb_player": number_player}
    return data

def cleanStarsValues(dictValue, nb_player):
    """Clean the values for it to be displayed"""
    
    
    players = [[ [] for j in range(5)] for i in range(nb_player + 1)]
    
    for i in dictValue.values():
        players[i["puid"]][0].append(i["x"])
        players[i["puid"]][1].append(i["y"]*-1)
        players[i["puid"]][2].append(i["nr"])

        
        players[i["puid"]][3].append(i["nr"] + int(i["tr"]))
        players[i["puid"]][4].append((i["st"]+1)*50/1500)
    
    # iys = list(array(dictValue["ys"])*-1*1)
    # ixs = list(array(dictValue["xs"])*1)
    # ists = 50*(array(dictValue["sts"]) + 1)/max(dictValue["sts"])

    return players

def cleanFleetsValues(fleets,stars):
    for i in fleets.values():
        if "ouid" in i:
            stars[i["ouid"]]["st"] += i["st"]

def plotMapFleets(fleets,stars ,markers, colors, arrows = True, troops = True, subsequentOrders = False):
    """Plot the Fleets in the graph
    arrows is a Boolean value, True will disaply arrows to indiquate where the fleets are moving
    troops is a Boolean value, True will make the size of the fleets represent the number of troops
    subsequentOrders is a Boolean value, True will disaply the subsequent orders if known"""
    for i in fleets.values():

        player = i["puid"]  
        
        if troops:    
            size = (i["st"]+1)*50/1500
        else:
            size = 10
    
        if i["orders"] == [] or not arrows:
            #If the fleet has no orders, don't display it
            continue
        else:
            
            startx = i["x"]
            starty = i["y"]
            
            if subsequentOrders:
                orders_len = len(i["orders"])
            else:
                orders_len = 1
                
            for j in range(orders_len):
                
                destinationUid = i["orders"][j][1] 
                    
                if destinationUid not in stars:
                    continue
                else:
                    dx = stars[destinationUid]["x"] - startx
                    dy = (stars[destinationUid]["y"] - starty)*-1
                    
                    length_arrow = min(sqrt(dx**2 + dy**2)/3,0.1)
                    
                    plt.arrow(startx, starty*-1, dx, dy,
                              color = colors[player],
                              length_includes_head = True,
                              width = 0.01,
                              head_width = length_arrow/1.5,
                              head_length = length_arrow,
                              ec = 'black',
                              lw = 0.1)
                    
                    startx =  stars[destinationUid]["x"]
                    starty = stars[destinationUid]["y"]
 
            plt.scatter(i["x"],i["y"]*-1, 
                        c=colors[player],
                        marker = markers[player], 
                        s = size,
                        edgecolors = 'black',
                        linewidths = 0.5)
        
def plotMapStars(players,markers, colors, labels, size = "nr"):
    """Plot the value, size can be nr, tr or troops"""
    
    title = 'Star Map'
    if size == "nr":
        size_nbr = 2
        title += ' and Natural Ressources'

    elif size == "tr":
        size_nbr = 3
        title += ' and Terraformation'
    elif size == "troops":
        size_nbr = 4
        title += ' and Troops'
        
    else:
        raise ValueError("results: status must be one of %r." % {"nr","tr","troops"})
    
    

    for i in range(len(players)):
        plt.scatter(players[i][0],players[i][1], 
                    marker=markers[i], 
                    c=colors[i], 
                    s=players[i][size_nbr], 
                    label= labels[i],
                    edgecolors = "#808080",
                    linewidths = 0.2)
   
    lgnd = plt.legend(loc = "upper left",
                      ncol = 1, 
                      markerscale = 1, 
                      labelspacing = 0.5, 
                      handlelength =1,
                      bbox_to_anchor=(1, 1))
    
    for i in range(11):
        lgnd.legendHandles[i]._sizes = [30]
    
    plt.axis('off')
    
    plt.title(title)


def mapTheGalaxy(planetSize = "troops", fleetTroops = True, fleetOrders = True, subsequentOrders = False):
   """ planetSize is a String and can be nr to show the natural ressources, tr to show the actual ressources or troops to display the troops.
       fleetOrders is a Boolean value, True will disaply arrows to indiquate where the fleets are moving
       fleetTroops is a Boolean value, True will make the size of the fleets represent the number of troops
       subsequentOrders is a Boolean value, True will disaply the subsequent orders if known"""

   f = open('data.json','r')
   data = json.load(f)
   
   colors = ['#0000ff','#009fdf','#40c000','#ffc000','#df5f00','#c00000','#c000c0','#6000c0','#0000ff','#009fdf','#808080']
   markers = ['o','o','o','o','o','o','o','o','s','s','o']
    
   jsons = getJsons(data["game_number"],data["codes"],data["api_version"],data["url"])

   values = getValues(jsons)

   cleanFleetsValues(values["fleets"], values["stars"])

   plt.figure(dpi=1200)

   cleanValues = cleanStarsValues(values["stars"], values["nb_player"])

   plotMapStars(cleanValues, markers, colors, values["labels"], planetSize)
   plotMapFleets(values["fleets"],values["stars"], markers, colors,fleetOrders, fleetTroops,subsequentOrders)
    
   plt.show()
   
mapTheGalaxy()