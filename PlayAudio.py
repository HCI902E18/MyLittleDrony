import wave

try:
    import pyaudio

    audio = True
except ImportError:
    audio = False
    # Does not work in windows
    pass

from threading import Thread


class PlayAudio(object):
    def play(self, file):
        thread = Thread(target=self.__play, args=(file,))
        thread.start()

    def __play(self, file):
        if not audio:
            return
        chunk = 1024

        # open a wav format music
        f = wave.open(r"./audio/{}".format(file), "rb")
        # instantiate PyAudio
        p = pyaudio.PyAudio()
        # open stream
        stream = p.open(format=p.get_format_from_width(f.getsampwidth()),
                        channels=f.getnchannels(),
                        rate=f.getframerate(),
                        output=True)
        # read data
        data = f.readframes(chunk)

        # play stream
        while data:
            stream.write(data)
            data = f.readframes(chunk)

        # stop stream
        stream.stop_stream()
        stream.close()

        # close PyAudio
        p.terminate()
