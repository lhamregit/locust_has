import random
from locust import TaskSet, task
#import hlslocust.hlsplayer as hlsplayer
import hlsplayer as hlsplayer

SECONDS = 1000  # ms in seconds

class UserBehavior(TaskSet):

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        print "on start called"
        #self.url = 'http://osmfhls.kutu.ru/static/vod/sl_vod.m3u8'
        self.url = 'http://c2.prod.playlists.ihrhls.com/177/playlist.m3u8?listeningSessionID=56d519b03a58f853_66946_6X7oubPu_0000000PtP2&downloadSessionID=0&at=0&fb_broadcast=1&init_id=8169&profileid=6&host=webapp.US&listenerId=1438704813593_7582&uid=1389802090447'
        #"http://c2.prod.playlists.ihrhls.com/177/playlist.m3u8?listeningSessionID=56d519b03a58f853_66946_6X7oubPu_0000000PtP2&downloadSessionID=0&at=0&clientType=web&fb_broadcast=1&init_id=8169&modTime=1456873265673&pname=OrganicWeb&profileid=6&birthYear=null&territory=US&host=webapp.US&listenerId=1438704813593_7582&uid=1389802090447&gender=1&age=40&amsparams=playerid%3AiHeartRadioWebPlayer%3Bskey%3A1456873265&terminalid=159&zipcode=null&&playedFrom=314"
        #http://osmfhls.kutu.ru/static/vod/sl_vod.m3u8

    @task
    def playHLS(self):
        #url = "http://c2.prod.playlists.ihrhls.com/177/playlist.m3u8?listeningSessionID=56d519b03a58f853_66946_6X7oubPu_0000000PtP2&downloadSessionID=0&at=0&clientType=web&fb_broadcast=1&init_id=8169&modTime=1456873265673&pname=OrganicWeb&profileid=6&birthYear=null&territory=US&host=webapp.US&listenerId=1438704813593_7582&uid=1389802090447&gender=1&age=40&amsparams=playerid%3AiHeartRadioWebPlayer%3Bskey%3A1456873265&terminalid=159&zipcode=null&&playedFrom=314"
        duration = random.randint(60, 600)
        self.client.play(self.url, duration=duration)

class HLSUser(hlsplayer.HLSLocust):
    task_set = UserBehavior
    min_wait = 2 * SECONDS  # 2 seconds
    max_wait = 15 * SECONDS  # 5 seconds
