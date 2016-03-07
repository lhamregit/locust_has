import random
from locust import TaskSet, task
import hlsplayer_IHR as hlsplayer
import string

SECONDS = 1000  # ms in seconds

LISTNER_ID = []
with open('users.csv') as f:
    for line in f:
        components = line.strip().split(',')
        LISTNER_ID.append({'listnerId': components[0]})
print "Read %d users from users.csv" % len(LISTNER_ID)

class UserBehavior(TaskSet):

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        print "on start called"

        if len(LISTNER_ID) > 0:
            users = LISTNER_ID.pop()
            self.listenerId = users['listnerId']
            print 'found --> ' + str(self.listenerId)
        else:
            self.listenerId = 'test-%s' % ''.join(random.choice(string.ascii_lowercase) for i in range(8))
            print "No more users, let's create a user"
            users = open('users.csv', 'a')
            line = '%s\n' % (self.listenerId)
            users.write(line)
            users.close()
        # call to get the url to pass in
        self.url = str(self.getFirstManifest()) + '&profileid=6&listenerId=%s&uid=1389802090447&listeningSessionID=%s' % (self.listenerId, self.listenerId)

    @task
    def playHLS(self):
        duration = random.randint(60, 600)
        self.client.play(self.url, duration=duration)

    def getFirstManifest(self):
        response = self.client.request('http://c1.stage.playlists.ihrhls.com/77/playlist.m3u8', 'init')
        print 'data --> ' +str(response.content)
        return self.parse(response.content)

    def parse(self, manifest):
        lines = manifest.split('\n')
        for i,line in enumerate(lines):
            if line.startswith('http'):
                return line

class HLSUser(hlsplayer.HLSLocust):
    task_set = UserBehavior
    min_wait = 2 * SECONDS  # 2 seconds
    max_wait = 5 * SECONDS  # 5 seconds

#http://c1.stage.playlists.ihrhls.com/1469/
#http://c2.prod.playlists.ihrhls.com/177/
#self.url = 'http://c2.prod.playlists.ihrhls.com/177/playlist.m3u8?listeningSessionID=56d519b03a58f853_66946_6X7oubPu_0000000PtP2&downloadSessionID=0&at=0&fb_broadcast=1&init_id=8169&profileid=6&host=webapp.US&listenerId=1438704813593_7582&uid=1389802090447'
#"http://c2.prod.playlists.ihrhls.com/177/playlist.m3u8?listeningSessionID=56d519b03a58f853_66946_6X7oubPu_0000000PtP2&downloadSessionID=0&at=0&clientType=web&fb_broadcast=1&init_id=8169&modTime=1456873265673&pname=OrganicWeb&profileid=6&birthYear=null&territory=US&host=webapp.US&listenerId=1438704813593_7582&uid=1389802090447&gender=1&age=40&amsparams=playerid%3AiHeartRadioWebPlayer%3Bskey%3A1456873265&terminalid=159&zipcode=null&&playedFrom=314"
#http://osmfhls.kutu.ru/static/vod/sl_vod.m3u8
