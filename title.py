#!/usr/bin/env python
# -*- coding: utf-8

# Copyright (C) 2013 Anthony Alves <cvballa3g0@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:

# - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# - Neither the name of the Mumble Developers nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# `AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#
# title.py
#

from mumo_module import (commaSeperatedIntegers,
                         commaSeperatedBool,
                         MumoModule)

import urllib2, re, BeautifulSoup




class title(MumoModule):
    default_config = {'title':(
                                ('servers', commaSeperatedIntegers, []),
                                ),
                                lambda x: re.match('(all)|(server_\d+)', x):(
                                    ('reactonregisteredonly', commaSeperatedBool, [True]),
                                )
                    }

    def __init__(self, name, manager, configuration = None):
        MumoModule.__init__(self, name, manager, configuration)
        self.murmur = manager.getMurmurModule()

    def connected(self):
        manager = self.manager()
        self.log().debug("Register [%s] callbacks", self.name())

        manager.subscribeServerCallbacks(self, self.cfg().title.servers or manager.SERVERS_ALL)

        
    def disconnected(self): pass

    def sendMessage(self, server, user, message, msg):
        if message.channels: # sent to a channel
            server.sendMessageChannel(user.channel, False, msg)
        else: # sent as a private message
            server.sendMessage(message.sessions[0], msg)
            
    def getYouTubeTitle(self, id):
        endpoint = 'http://youtube.com/get_video_info?video_id=' + id
        sock = urllib2.urlopen(endpoint)
        
        # get the file contents
        videostr = sock.read()
        sock.close()
        
        # parse the text for channel and title
        tagRegex = '&tag=([^\n^\r^&]*)'
        channel = re.findall(tagRegex.replace("tag", "author"), videostr)[0]
        title = re.findall(tagRegex.replace("tag", "title"), videostr)[0]
        
        # clean up the text
        channel = urllib2.unquote(channel).replace("+", " ")
        title = urllib2.unquote(title).replace("+", " ")
        
        
        # create the server message
        return channel + " :: " + title
                
   
    #
    #--- Server callback functions
    #
    def userTextMessage(self, server, user, message, current=None):
    
            sid = server.id()
            try:
                scfg = getattr(self.cfg(), 'server_%d' % sid)
            except AttributeError:
                scfg = self.cfg().all

            # check if the user is registered
            if scfg.reactonregisteredonly and user.userid == -1:
                self.log().debug('\'reactonregisteredonly\' is enabled; Ignored unregistered user \'%s\' (session id \'%s\')' % (user.name, user.session))
                return
                
            
            msg = message.text
            link = re.findall(r'href=[\'"]?([^\'" >]+)', msg)
            
            if len(link) < 1:
                # url was not included in this message
                return
                
            # check if it is a YouTube link
            idRegex = '(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/ ]{11})'
            videoId = re.findall(idRegex, msg)

            if len(videoId) >= 1: # YouTube link
                # not a YouTube link
                msg = self.getYouTubeTitle(videoId[0])
            else:
                msg = BeautifulSoup.BeautifulSoup(urllib2.urlopen(link[0])).title.string
                
            self.sendMessage(server, user, message, msg)



    def userConnected(self, server, state, context = None): pass
    def userDisconnected(self, server, state, context = None): pass
    def userStateChanged(self, server, state, context = None): pass

    def channelCreated(self, server, state, context = None): pass
    def channelRemoved(self, server, state, context = None): pass
    def channelStateChanged(self, server, state, context = None): pass
