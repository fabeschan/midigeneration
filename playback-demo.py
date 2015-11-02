import data
import time
import mido
import playback

def main():
    # initialize a PlaybackUtility for each midi file, put them into a list -> playback_utils
    playback_utils = []
    for f in ['mid/owl.mid', 'mid/lost.mid']:
        musicpiece = data.piece(f)
        pbu = playback.PlaybackUtility()
        pbu.add_notes(musicpiece.unified_track.notes)
        playback_utils.append(pbu)

    tempo_reciprocal = 3000 # 'speed' of playback. need to adjust this carefully
    playback.init_midi_channel() # set up channel, and prompt MIDI device reset before continuing

    # loop
    loop = True
    piece_index = 0 # index of the piece currently playing
    start_time = time.clock()
    while loop:
        # read/poll the trigger file
        text = playback.read_trigger_file('trigger_file')
        if text:
            print 'read triggerfile:', text
            piece_index = (piece_index + 1) % 2 # switch pieces

        cur_time = time.clock()
        playback_pos = int((cur_time - start_time) * 1000000) / tempo_reciprocal

        # play those notes using the corresponding PlaybackUtility
        playback_utils[piece_index].run(playback_pos)
        if playback_utils[piece_index].isTerminated():
            loop = False

if __name__ == '__main__':
    main()
