#! /usr/bin/python -O
# Twitter Playlists
# Scans a user's latest tweets for a string + youtube video
# Adds any matching videos to a youtube playlist

from subprocess import check_call
import subprocess
import string
import random
import glob
from base64 import b64encode
import requests
from pprint import pprint
import time
import re
import threading
import sys
import ConfigParser
import httplib2
import tweepy
import argparse

from apiclient.discovery import build
from apiclient.http import BatchHttpRequest
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run
from oauth2client import tools

# Set up config so we can get basic data
config = ConfigParser.ConfigParser()
config.read("twplaylist.cfg")

# Constants
## General
sleep = config.get("General", "sleep_time")
match = config.get("General", "match")

## Twitter
t_count = config.get("Twitter", "count")
t_user = config.get("Twitter", "user")
t_id = config.get("Twitter", "client_id")
t_secret = config.get("Twitter", "client_secret")

twitter = ''

## YouTube
ytcomReg = r"youtube.com\/watch\?v=(.{11})"
ytbeReg = r"youtu.be\/(.{11})"
yt_id = config.get("YouTube", "client_id")
yt_secret = config.get("YouTube", "client_secret")
playlist = config.get("YouTube", "playlist")
scope = 'https://www.googleapis.com/auth/youtube'

youtube = ''

def twplaylist():

    flow = OAuth2WebServerFlow(yt_id, yt_secret, scope)
    storage = Storage('credentials.dat')
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    flags = parser.parse_args()
    credentials = tools.run_flow(flow, storage, flags)
    if credentials is None or credentials.invalid:
      credentials = run(flow, storage)

    global http
    http = httplib2.Http()
    http = credentials.authorize(http)

    global youtube 
    youtube = build('youtube', 'v3', http=http)

    global twitter
    twitter = tweepy.API(tweepy.OAuthHandler(t_id, t_secret))

    user = twitter.get_user(t_user)

    last_id = ''

    while True:
        try:

            ytlinks = []
            
            if last_id:
                print 'Grabbing ' + str(t_count) + ' latest tweets from ' + user.screen_name + ' since ' + str(last_id)
                statuses = twitter.user_timeline(id=t_user, since_id=int(last_id), count=t_count)

            else:
                print 'Grabbing ' + str(t_count) + ' latest tweets from ' + user.screen_name
                statuses = twitter.user_timeline(id=t_user, count=t_count)
            
            if len(statuses) > 0:

                last_id = statuses[0].id
                for status in statuses:
                    if (match in status.text.lower()) and (status.entities.has_key('urls')):
                        url = status.entities.get('urls')[0].get('expanded_url')
                        ytcomlink = re.findall(ytcomReg, url)
                        ytbelink = re.findall(ytbeReg, url)
                        if ytbelink != []: ytlinks += ytbelink
                        if ytcomlink != []: ytlinks += ytcomlink

                print 'Adding ' + str(len(ytlinks)) + ' video(s)'
                for video in ytlinks: 

                    insert = youtube.playlistItems().insert(
                        part="snippet",
                         body=dict(
                          snippet=dict(
                            playlistId=playlist,
                            resourceId=dict(
                                kind="youtube#video",
                                videoId=video
                                )
                            ))
                        )
                    response = insert.execute()

            else: print 'No new tweets since last attempt'
            print 'Waiting ' + str(sleep) + ' seconds'
            time.sleep(int(sleep))

        except Exception, e:
            print e



    exit()

main_thread = threading.Thread(target=twplaylist)

main_thread.start()
