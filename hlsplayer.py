import random
import gevent
import time
from locust import events, Locust

import hlserror as hlserror
import hlsobject as hlsobject

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

        if len(self.master_playlist.media_playlists) == 0:
            # in this case we looked for media playlists, but didn't find any.
            # maybe we're looking at a stream that only has a single bitrate
            # and all the fragments are in the master playlist
            playlist = hlsobject.MediaPlaylist('media',url)
            #print 'playlist 1 bit rate', playlist
        else:
            # I randomly pick a quality, unless it's specified...
            if quality is None:
                playlist = random.choice(self.master_playlist.media_playlists)
            else:
                i = quality%len(self.master_playlist.media_playlists)
                playlist = self.master_playlist.media_playlists[i]

        # download and parse media playlist
        print 'download and parse media playlist = ', playlist
        r = playlist.download()
        last_manifest_time = time.time()

        if r is False:
            return

        # serves as an index for the fragments
        msq = playlist.first_media_sequence()
        print 'Player msq', msq
        retries = 0
        start_time = None
        buffer_time = 0.0
        playing = False

        while True :
            # should I download an object?
            print 'playlist.last_media_sequence()', playlist.last_media_sequence()
            if msq <= playlist.last_media_sequence():
                try:
                    a = playlist.get_media_fragment(msq)
                    print 'a --> ', playlist.url
                except hlserror.MissedFragment as e:
                    events.request_failure.fire(request_type="GET",
                                                name=playlist.url,
                                                response_time=play_time,
                                                exception=e)
                    play_time = None
                    print 'playing', playing
                    if playing:
                        play_time = (time.time() - start_time)
                        print 'play_time', play_time
                    return (buffer_time,play_time)

                r = a.download()
                print 'play r ', r
                if r == True:
                    msq+=1
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

            print 'should play?'
            # should we start playing?
            if not playing and buffer_time > BUFFERTIME:
                playing = True
                start_time = time.time()

            print 'playing?', playing

            if playing:
                # should we grab a new manifest?
                if not playlist.endlist: # only update manifest on live
                    print ' if not playlist.endlist?'
                    manifest_age = (time.time() - last_manifest_time)
                    if manifest_age > playlist.targetduration*2:  # vlc does this
                        print 'get new manifest'
                        r = playlist.download()
                        if r == True:
                            last_manifest_time = time.time()

                play_time = (time.time() - start_time)
                if play_time >= buffer_time:
                    if msq <= playlist.last_media_sequence():
                        # we've run out of buffer but we still have parts to
                        # download
                        e = hlserror.BufferUnderrun('Buffer is empty with '
                                                    'files still to download')
                        events.request_failure.fire(request_type="GET",
                                                    name=playlist.url,
                                                    response_time=play_time,
                                                    exception=e)
                        return (buffer_time,play_time)
                    if playlist.endlist:
                        # we've finished a vod (or live stream ended)
                        return (buffer_time,play_time)
                    else:
                        # we've downloaded and played all the fragments, but
                        # we've not been told that the stream has finished
                        e = hlserror.StaleManifest('Buffer is empty with no '
                                                   'new files to download.')
                        events.request_failure.fire(request_type="GET",
                                                    name=playlist.url,
                                                    response_time=play_time,
                                                    exception=e)
                        return (buffer_time,play_time)

                # have we seen enough?
                if duration and play_time > duration :
                    return (buffer_time,play_time)
            gevent.sleep(1) # yield execution to another thread

