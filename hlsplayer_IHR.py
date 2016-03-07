import random
import gevent
import time
from locust import events, Locust
import requests

import hlserror as hlserror
import hlsobject as hlsobject
import time

BUFFERTIME = 10.0 # time to wait before playing
MAXRETRIES = 2

class HLSLocust(Locust):
    def __init__(self, *args, **kwargs):
        super(HLSLocust, self).__init__(*args, **kwargs)
        self.client = Player()

class Player():
    def __init__(self):
        pass

    def play(self, url=None, quality=None, duration=None):
        print 'Start prep to download'
        # download and parse master playlist
        self.master_playlist = hlsobject.MasterPlaylist('master',url)
        r = self.master_playlist.download()
        print 'r = self.master_playlist.download()', r

        if r is False:
            return

        playlist = hlsobject.MediaPlaylist('media',url)

        # download and parse media playlist
        print 'download and parse media playlist = ' + str(playlist)
        r = playlist.download()
        last_manifest_time = time.time()

        if r is False:
            return

        # serves as an index for the fragments
        msq = playlist.first_media_sequence()
        print 'Player msq --> ' + str(msq)

        retries = 0
        start_time = None
        buffer_time = 0.0
        playing = False

        while True :
            # should I download an object?
            print 'playlist.last_media_sequence()  -->' + str(playlist.last_media_sequence())
            print 'msq --> ' +  str(msq)

            if msq <= playlist.last_media_sequence():
                try:
                    a = playlist.get_media_fragment(msq)
                    print 'a --> ' +  str(playlist.url)
                except hlserror.MissedFragment as e:
                    events.request_failure.fire(request_type="GET",
                                                name=playlist.url,
                                                response_time=play_time,
                                                exception=e)
                    play_time = None
                    print 'playing --> ' + str(playing)
                    if playing:
                        play_time = (time.time() - start_time)
                        print 'play_time --> ' + str(play_time)
                    return (buffer_time,play_time)

                r = a.download()
                print 'play r --> ' + str(r)
                if r == True:
                    msq+=1
                    print 'a.duration time --> ' + str(a.duration)
                    print 'buffer time --> ' + str(buffer_time)
                    buffer_time += a.duration
                else:
                    # TODO, think about this, if I fail to download a single
                    # segment enough times I stop playing. Should I not keep
                    # playing until I run out of buffer then 'buffer underrun'?
                    retries +=1
                    if retries >= MAXRETRIES:
                        play_time = 0
                        if start_time:
                            play_time = (time.time() - start_time)
                        return (buffer_time,play_time)
                gevent.sleep(11)

            else:
                print 'break'
                break
        return

    def request(self, url, name=None):
        start_time = time.time()

        try:
            print str(name) + ' reguest --> '+ str(url)
            r = requests.get(url, verify=False)
            r.raise_for_status() # requests wont raise http error for 404 otherwise
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects) as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="GET", name=name,
                                        response_time=total_time, exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            try:
                response_length = int(r.headers['Content-Length'])
            except KeyError:
                response_length = 0
            if response_length != len(r.content):
                e = hlserror.BadContentLength("content-length header did not match received content length")
                events.request_failure.fire(request_type="GET", name=name,
                                            response_time=total_time,
                                            exception=e)
            events.request_success.fire(request_type="GET", name=name,
                                        response_time=total_time,
                                        response_length=response_length)
            return r
        return None