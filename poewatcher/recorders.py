#!/usr/bin/python3
# -*- coding: utf8 -*-
#Copyright (C) 2015 Guillaume DUPUY <glorf@glorf.fr>
#This file is part of Poe Watcher.

#PoE Watcher is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#PoE Watcher is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.

#You should have received a copy of the GNU Affero General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>
from . import config as c
from . import utils
import os
import re
import time
import inspect
import pyperclip
import logging
loggerGen = logging.getLogger(__name__+".GenericRecorder")
loggerMap = logging.getLogger(__name__+".MapRecorder")
class GenericRecorder():
    def __init__(self, actions, separator, output_path, headers):
        
        self.output_path = output_path
        self.separator = separator
        self.headers = headers
        self.actions = []
        for pr in actions:
            self.actions.append((pr[1], getattr(self, pr[2])))
        if not os.path.isfile(output_path):
            open(output_path, "w+", encoding='utf8')
        with open(output_path, "r+", encoding='utf8') as file:
            if os.path.getsize(output_path) == 0:
                file.write(','.join(headers))
                file.write("\n")
                loggerGen.info("Created output csv file for GenericRecorder")
    def parse_message(self, msg, char_name):
        for abbr,func in self.actions:
            if abbr in msg:
                func(msg.replace(abbr,""), char_name)
    def add_loot(self, msg, char_name):
        info = [char_name, str(int(time.time()))]
        info += msg.split(self.separator)
        while len(info) < len(self.headers):
            info.append("")
        csv = ",".join(info)
        with open(self.output_path, "a", encoding='utf8') as file:
            file.write(csv)
            file.write("\n")
        loggerGen.info("GenericRecorder wrote : {0}".format(csv))
        
        

MAP_HEADERS = "timestamp,character,level,pack size,IIQ,boss,ambush,beyond,domination,magic,zana,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,notes"

class MapRecorder():
    def __init__(self, actions, separator, output_path):
        self.actions = []
        for pr in actions:
            self.actions.append((pr[1], getattr(self, pr[2]))) 
        self.separator = separator
        self.output_path = output_path
        self.data = []
        if not os.path.isfile(output_path):
            open(output_path, "w+", encoding='utf-8')
        with open(output_path, "r+", encoding='utf-8') as file:
            if os.path.getsize(output_path) == 0:
                file.write(MAP_HEADERS)
                file.write("\n")
                loggerMap.info("Created output csv file for MapRecorder")
                
        
    def parse_message(self, msg, char_name):
        for abbr,func in self.actions:
            if abbr in msg:
                #We don't need to pass char_name to other function than add_map [still kinda ugly, will works on this to make it better]
                if len(inspect.getargspec(func)[0]) == 3:
                    func(msg.replace(abbr,""), char_name)
                else:
                    func(msg.replace(abbr, ""))


         
                
    def running(self):
        return len(self.data) > 0
        
                      
    def add_map(self, msg, char_name):
        #We get the information from the clipboard if the msg is empty
        if not msg:
            tmp = self.add_map_from_clipboard(msg, char_name)
        else:
            tmp = self.add_map_from_user_input(msg, char_name)
        self.data.append(tmp)
        loggerMap.info("Started map, with level = {0}, psize = {1}, iiq = {2}, ambush = {5}, beyond = {3}, domination = {4}, magic = {6}, zana = {7}".format(tmp["level"], tmp["psize"], tmp["iiq"], tmp["beyond"], tmp["domination"], tmp["ambush"], tmp["magic"], tmp["zana"]))
       
        
    def add_map_from_clipboard(self, msg, char_name):
        info = pyperclip.paste()
        regex_level = re.compile("Map Level: \d{2}")
        regex_psize = re.compile("Monster Pack Size: \+\d{1,3}")
        regex_quantity = re.compile("Item Quantity: \+\d{1,3}")
        level = psize = quantity = 0
        magic = "more Magic Monsters" in info
        if regex_level.search(info):
            level = int(regex_level.findall(info)[0].replace("Map Level: ",""))
        if regex_psize.search(info):
            psize = int(regex_psize.findall(info)[0].replace("Monster Pack Size: +",""))
        if regex_quantity.search(info):
            quantity = int(regex_quantity.findall(info)[0].replace("Item Quantity: +",""))  
        quantity += int(c.get("map_recorder", "additional_iiq"))
        tmp = {"character":char_name,"level":level, "psize":psize, "iiq":quantity, "ambush": False, "beyond": False,"domination": False,  "magic": magic, "zana" : False, "boss":0, "loot":[], "note":[]}
        return tmp
            
            
    def add_map_from_user_input(self, msg, char_name):
        #We want lvl,psize,iiq,[mods]
        info = msg.split(self.separator)
        #In case of user input error, assume empty
        while len(info) < 4:
            info.append("")            
        tmp={"character":char_name,"level":0, "psize":0, "iiq":0, "ambush": ("a" in info[3]), "beyond": ("b" in info[3]),"domination": ("d" in info[3]),  "magic": ("m" in info[3]),"zana" : ("z" in info[3]), "boss":0, "loot":[], "note":[]}
        #We remove all non-digit character
        for i in range(0,3):
            info[i] = ''.join(filter(lambda x: x.isdigit(), info[i]))
            info[i] = info[i] if info[i] else 0
        tmp["level"] = info[0]
        tmp["psize"] = info[1]
        tmp["iiq"] = info[2]
        return tmp

    def edit_map(self, msg):
        #We want mods[,real_iiq,real_psize]
        info = msg.split(self.separator)
        log = "Edited map"
        while len(info)< 3:
            info.append("")
        self.data[-1]["zana"] = "z" in info[0]
        self.data[-1]["ambush"] = "a" in info[0]
        self.data[-1]["domination"] = "d" in info[0]
        self.data[-1]["magic"] = "m" in info[0]
        if self.data[-1]["zana"]:
            log +=", with Zana"
        if self.data[-1]["ambush"]:
            log +=", with Ambush"
        if self.data[-1]["domination"]:
            log +=", with Domination"
        if self.data[-1]["magic"]:
            log +=", with magic monsters"            
        #Remove non-digit from info (for real_iiq, real_psize)
        info[1] = ''.join(filter(lambda x: x.isdigit(), info[1]))
        info[2] = ''.join(filter(lambda x: x.isdigit(), info[2]))
        if info[1]:
            self.data[-1]["iiq"] = info[1]
            log += ", with new IIQ " + info[1]
        if info[2]:
            self.data[-1]["psize"] = info[2]
            log +=", with new Pack Size " + info[2]
        loggerMap.info(log)
                                    
    def add_loot(self, msg):
        if len(self.data) > 0:
            info = [''.join(filter(lambda x: x.isdigit(), y)) for y in msg.split(self.separator)]
            info = [x if x.isdigit() else 0 for x in info]
            self.data[-1]["loot"] += info
            loggerMap.info("Adding loot : {0}".format(', '.join(str(x) for x in info)))
        else:
            loggerMap.error("adding loot with no active map")
            
            
    def add_note(self, msg):
        if len(self.data) > 0:
            #Remove the comma to not break the .csv
            self.data[-1]["note"].append(msg.replace(",",""))
            loggerMap.info("Adding note : {0}".format(msg))
        else:
            loggerMap.error("ERR: adding note with no active map")


    def abort_map(self, msg):
        if len(self.data) > 0:
            loggerMap.info("Removing last map")
            self.data = self.data[:-1]       
        else:
            loggerMap.error("ERR: aborting map with no active map")
            
    def end_map(self, msg):
        if len(self.data) > 0:
            self.data[-1]["boss"] = ''.join(filter(lambda x: x.isdigit(), msg))
            self.data[-1]["boss"] = self.data[-1]["boss"] if self.data[-1]["boss"] else c.get("map_recorder","default_boss")
            output = utils.dict_to_csv(self.data[-1])
            with open(self.output_path, "a", encoding='utf-8') as file_out:
                file_out.write(output)
                file_out.write("\n")
            loggerMap.info("Map ended, i wrote : {0}".format(output))
            if c.getboolean("map_recorder", "send_data"):
                self.data[-1]["timestamp"] = int(time.time())
                self.data[-1]["username"] = self.data[-1]["character"] if c.getboolean("map_recorder", "send_data") else "anonymous"
                response = utils.contact_server(self.data[-1])
                if "OK" in response:
                    loggerMap.info("Server response: {0}".format(response))
                else:
                    loggerMap.error("Server response: {0}".format(response))
            self.data = self.data[:-1]
        else:
            loggerMap.error("ERR: ending map with no active map")        