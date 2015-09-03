#!/usr/bin/python3
# -*- coding: utf8 -*-
#Copyright (C) 2015 Guillaume DUPUY <glorf@glorf.fr>
#This file is part of Watch Poe.

#Watch PoE is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#Watch PoE is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>
from watchdog.observers import Observer
from map_recorder import * 
from notifier import *
from generic_recorder import *
from poe_handler import *
from util import *
import config as c


##Init stuff
map_recorder = MapRecorder(c.map_actions, c.separator, c.map_output_path)
notifier = Notifier(c.notifier_channels, c.notifier_title, c.notifier_icon_path, windows)
generic_recorder = GenericRecorder(c.generic_actions, c.separator, c.generic_output_path, c.generic_headers)
poe_handler = PoeHandler(c.usernames, c.handler_actions, c.log_path)
observer = Observer()
observer.schedule(poe_handler, c.log_path, recursive=False)
observer.start()

##Main loop
try:
    while True:
        time.sleep(1)
        ##Where all the dirty work is done
        for message in poe_handler.messages:
            if not poe_active() and poe_handler.notifier:
                notifier.parse_message(message)
            stripped, name = poe_handler.strip_username(message)
            name = c.logged_username if c.logged_username else name
            if stripped:
                old_state = map_recorder.running()
                map_recorder.parse_message(stripped, name)
                generic_recorder.parse_message(poe_handler.strip_username(message))
                state = map_recorder.running()
                #Change of stat (either map started/map ended)
                if c.offline_while_maps and state != old_state:
                    if state:
                        poe_handler.poetrade_off()
                    else:
                        poe_handler.poetrade_on()
        
        poe_handler.messages.clear()
            

            
except KeyboardInterrupt:
    observer.stop()
observer.join()


