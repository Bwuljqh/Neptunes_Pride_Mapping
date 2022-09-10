# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 13:56:58 2022

@author: Bwuljqh
"""

import matplotlib.pyplot as plt
import requests
import json

from datetime import datetime
from numpy import  sqrt

EXTRACTED_DATA_FOLDER="extracted_data"

def getJsons(game_number, 
             codes, 
             api_version = "0.1", 
             url = "https://np.ironhelmet.com/api", save_files=True):
    
    """
    Returns a list of values collected via the API
    
    :param str game_number: Number of the game you wish to visualize data from
    :param list codes: Codes of players you wish to visualize data from
    :param str api_version: 0.1 is the current version
    :param str url: API url, should stay the same and can be left empty
    """
    
    jsons = []
    
    #No codes, abort
    if len(codes) == 0:
        print("No codes have been provided")
        return False
    
    #Fetch data from the API via a loop on the codes we have
    for i in codes:
        keys = {"api_version": api_version, "game_number": game_number, "code": i}
        req = requests.post(url, data = keys)
        temp = req.json()
        
        #Errors from the api are codified, if there is an error, we raise it but continue to loop on the codes
        if 'error' in temp:
            if temp["error"] == "code not found in game":
                print("code " + i + " not found in game " + game_number)
            else:
                print(temp['error'])
        else:
            if save_files:
                # TODO : save each JSON in a spearate file, named `extracted_data/<code>_yyyy-mm-dd_hh:mm:ss.json`
                with open(f"{EXTRACTED_DATA_FOLDER}/{i}_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.json", 'w') as data_file:
                    json.dump(temp, data_file)
            jsons.append(temp)
    
    #No data, abort
    if len(jsons) == 0:
        print('No data has been fetched')
        return False
    
    print("Raw Data fetched")
    return jsons


def getValues(jsons):
    """
    Retrieve stars  and fleets values from a list of jsons from the Neptune's Pride API. 
    Data verification must be done beforehand
    
    :param list jsons: Jsons retreived from the Neptune's Pride API'
    """
    #Get the number of players via the size of the players dict
    number_player = len(jsons[0]['scanning_data']['players'])
    
    #Label retreiving
    labels = [jsons[0]['scanning_data']['players'][str(j)]['alias'] for j in range(number_player)]
    #Add neutral planets
    labels += ['Neutral']
    
    #Create base dicts and prepare data
    data = {"stars" : dict(), "fleets": dict()}
    data["nb_player"] = number_player
    data["labels"] = labels
    
    #Loops on the datasets we have
    for i in jsons:
        
        #Updating data for the unnocupied planets
        i['scanning_data']['players']['-1'] = {'tech': 
                                               {'terraforming': 
                                                {'value':0}
                                               }
                                              }
        
        #Retreiving Stars values
        for j in i['scanning_data']['stars'].values():
            data["stars"][j['uid']] = {"x" : float(j["x"]),
                               "y" :    float(j["y"]),
                               "st" :   j["st"],
                               "nr" :   j["nr"],
                               "puid": j["puid"],
                               "uid" :  j["uid"],
                               "tr" :   i['scanning_data']['players'][str(j['puid'])]['tech']['terraforming']['value']}
            
        #Retreiving Fleets values
        for j in i["scanning_data"]['fleets'].values():
            data["fleets"][j['uid']] = {"x" :       float(j["x"]),
                                        "y" :       float(j["y"]),
                                        "lx":       float(j["lx"]),
                                        "ly":       float(j["ly"]),
                                        "st" :      j["st"],
                                        "uid" :     j["uid"],
                                        "orders":   j['o'],
                                        "puid" :    j["puid"]}
            if "ouid" in j:
                data["fleets"][j['uid']]["ouid"] = j['ouid']

    print("Values fetched")
    return data

def cleanStarsValues(stars, 
                     nb_player, 
                     ratio = 50):
    #TODO: Add parm description
    """
    Clean the star values for them to be displayed
    
    :param dict stars: The stars we retreived from getValues
    :param int nb_player: The number of players in the game (no neutrals, AI counted)
    :param int ratio: Determines the relative size of the stars, bigger the number, bigger the stars. 50 is nice for the mapping of a full galaxy with fleets of about ~1000
    """
    #Data preparation
    players = [ {"x": [], "y": [], "nr": [], "tr": [], "st": []} for i in range(nb_player + 1)]
    
    
    for i in stars.values():
        
        players[i["puid"]]["x"].append(i["x"])
        #Multiplying by -1 otherwise the data is upside down
        players[i["puid"]]["y"].append(i["y"]*-1)
        
        players[i["puid"]]["nr"].append(i["nr"])
        players[i["puid"]]["tr"].append(i["nr"] + int(i["tr"]))
        
        #Sizing the stars via their strength and the ratio
        players[i["puid"]]["st"].append((i["st"]+1)*ratio/1500)
        
    print('Stars Data cleaned')
    return players

def cleanFleetsValues(fleets,stars):
    """
    Clean the fleet values for them to be displayed
    
    :param dict fleets: The fleets we retreived from getValues
    :param dict stars: The stars we retreived from getValues
    """
    
    #More things may be added here, currently, it updates the plantes if a fleet is stationned on it
    for i in fleets.values():
        if "ouid" in i:
            stars[i["ouid"]]["st"] += i["st"]
    
    print('Fleets Data cleaned')

def plotMapFleets(fleets,
                  stars ,
                  markers, 
                  colors, 
                  labels,
                  nb_player,
                  arrows = True, 
                  troops = True, 
                  subsequentOrders = False, 
                  ratio = 50):
    
    """Plot the Fleets
    
    :param dict fleets: The fleets we retreived from getValues
    :param dict stars: The stars we retreived from getValues
    :param list markers: List of the players markers
    :param list colors: The 9 available colors 
    :param list labels: Players names in the game
    :param int nb_player: The number of players in the game (no neutrals, AI counted)
    :param bool arrows: True will disaply arrows to indiquate where the fleets are moving
    :param bool troops: True will make the size of the fleets represent the number of troops
    :param bool subsequentOrders: True will disaply the subsequent orders if known
    :param int ratio: Determines the relative size of the stars, bigger the number, bigger the stars. 50 is nice for the mapping of a full galaxy with fleets of about ~1000
    """
    
    ##Looping on each fleet
    for i in fleets.values():

        player = i["puid"]  
        
        #Attributing sizes
        if troops:    
            size = (i["st"]+1)*ratio/1500
        else:
            size = 10
    
        #Checking if arrows are to be disaplyed
        if i["orders"] == [] or not arrows:
            #If the fleet has no orders, don't display it
            continue
        else:
            
            #Define the color for the player
            if labels[player] == 'Neutral':
                color = colors[-1]
            else:
                color = colors[player%8]
            
            #Define the marker for the player
            if labels[player] == 'Neutral':
                marker = markers[0]
            else:
                marker = markers[int(player/8)]
                
                
            #Needed when looping on multiple orders
            startx = i["x"]
            starty = i["y"]
            
            #Determining how many order are displayed
            if subsequentOrders:
                orders_len = len(i["orders"])
            else:
                orders_len = 1
                
            for j in range(orders_len):
                
                #This is the objective star
                destinationUid = i["orders"][j][1] 
                    
                #If the destination si not known, we can still add an arrow thanks to the last position of the fleet
                if destinationUid not in stars:
                    dx = i["lx"] + -1*(startx - i["lx"])
                    dy = i["ly"] + -1*(starty - i["ly"])
                else:
                    #Determinating the arrow coordinates, it originates from the fleet, to the objective star
                    dx = stars[destinationUid]["x"] - startx
                    dy = (stars[destinationUid]["y"] - starty)
                    
                    
                    
                #Arrow formating
                length_arrow = min(sqrt(dx**2 + dy**2)/3,0.1)
                
                plt.arrow(startx, starty*-1, dx, dy*-1,
                          color = color,
                          length_includes_head = True, 
                          width = 0.01,
                          head_width = length_arrow/1.5,
                          head_length = length_arrow,
                          ec = 'black',
                          lw = 0.1)
                
                #Next destination, a fleet with destination not mapped should not have subsequent known orders (but this will probably bite me latter)
                if destinationUid in stars:
                    #Next starts are the last destination
                    startx =  stars[destinationUid]["x"]
                    starty = stars[destinationUid]["y"]
                    
            #Map the fleets
            plt.scatter(i["x"],i["y"]*-1, 
                        c=color,
                        marker = marker, 
                        s = size,
                        edgecolors = 'black',
                        linewidths = 0.5)
            
    print("Fleets plotted")
        
def plotMapStars(players,
                 markers, 
                 colors, 
                 labels, 
                 nb_player,
                 size = "st"):
    
    """ 
    Plot the stars
    
    :param lists players: All the stars belonging to the different players
    :param list markers: List of the players markers
    :param list colors: The 9 available colors
    :param list labels: Players names in the game
    :param str size: Can be nr to show the natural ressources, tr to show the actual ressources or st to display the troops.
    """

    #looping on players
    for i in range(len(players)):
        
        #Define the color for the player
        if labels[i] == 'Neutral':
            color = colors[-1]
        else:
            color = colors[i%8]
            
        #Define the marker for the player
        if labels[i] == 'Neutral':
            marker = markers[0]
        else:
            marker = markers[int(i/8)]
        
        #Map the stars
        plt.scatter(players[i]["x"],players[i]["y"], 
                    marker=marker, 
                    c=color, 
                    s=players[i][size], 
                    label= labels[i],
                    edgecolors = "#808080",
                    linewidths = 0.2)
    print("Stars plotted")

def mapTheGalaxy(planetSize = "st",
                 showFleets = True,
                 fleetTroops = True, 
                 fleetOrders = True, 
                 subsequentOrders = False, 
                 ratio = 50, 
                 save = True, 
                 dpi = 2400):
    """ 
    Create the map of the galaxy with the data.json file
    
    :param str planetSize: Can be nr to show the natural ressources, tr to show the actual ressources or st to display the troops.
    :param bool showFleets: True will disaply the fleets, False will not disaply fleets nor orders
    :param bool fleetTroops: True will make the size of the fleets represent the number of troops
    :param bool fleetOrders: True will display arrows to indiquate where the fleets are moving 
    :param bool subsequentOrders:  True will disaply the subsequent orders if they are known
    :param int ratio: Determines the relative size of the stars, bigger the number, bigger the stars. 50 is nice for the mapping of a full galaxy with fleets of about ~1000
    :param bool save: True will automatically save the map on your computer
    :param int dpi: Resolution of the saved map
    """

    if planetSize not in ["nr", "tr", "st"] :
        raise ValueError("results: status must be one of %r." % {"nr","tr","st"})

    f = open('data.json','r')
    data = json.load(f)
   
    colors = ['#0000ff','#009fdf','#40c000','#ffc000','#df5f00','#c00000','#c000c0','#6000c0','#808080']
    markers = ['o','s','h','^','p','d','*','$⬮$']
    
    jsons = getJsons(data["game_number"],
                     data["codes"],
                     data["api_version"],
                     data["url"])

    #if no jsons are found nor codes are provided, abort the program
    if jsons == False:
        print("Aborting")
        return
   
    values = getValues(jsons)
        
    cleanFleetsValues(values["fleets"], 
                      values["stars"])


    cleanStarValues = cleanStarsValues(values["stars"], 
                                       values["nb_player"], 
                                       ratio)
    
    #less than that resolution is unreadable
    plt.figure(dpi=1200)

    plotMapStars(cleanStarValues,
                 markers, 
                 colors,
                 values["labels"],
                 values["nb_player"],
                 planetSize)
    
    if showFleets:
        plotMapFleets(values["fleets"],
                      values["stars"],
                      markers, 
                      colors,
                      values["labels"],
                      values["nb_player"],
                      fleetOrders, 
                      fleetTroops,
                      subsequentOrders,
                      ratio)
   
    #Ploting stuff
    now = datetime.now()
    dt_string = now.strftime("%d%m%Y_%H%M%S")
   
   
    #Legend
    lgnd = plt.legend(loc = "upper left",
                      ncol = 1, 
                      markerscale = 1, 
                      labelspacing = 0.5, 
                      handlelength =1,
                      bbox_to_anchor=(1, 1))
    
    #Resizes the markers in the legend
    for i in range(11):
        lgnd.legendHandles[i]._sizes = [30]
        
    title = 'Galaxy map'  

    #Title may be off center, 0.65 has been found after testing
    plt.title(title, x=0.65)

    plt.axis('off')
    
    if save :
        plt.savefig('figures/last_figure_' + dt_string +'.png', bbox_inches = 'tight', dpi = dpi) 
        
    # plt.show()
   
mapTheGalaxy(planetSize = "st", showFleets = True, fleetTroops = True, fleetOrders = True, subsequentOrders = False, ratio = 50, save = True, dpi = 2400)