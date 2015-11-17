import muse, parsemidi, sys

# extracts the chord from each track to generate a list of lists of midi values
def chordsInTrack(masterTrack):
	chordedTracks = []
	for track in masterTrack:
		if track[0][0] == 'note':
			chordTrack = []
			currentChord = []
			for note in track:
				if currentChord == [] or note[1] == currentChord[0][1]:
					currentChord.append(note)
				else:
					chordTrack.append(currentChord)
					currentChord = []
					currentChord.append(note)
			if currentChord != []:
				chordTrack.append(currentChord)
			chordedTracks.append(chordTrack)
	return chordedTracks

# generate chords between tracks by finding the note values that occur
# simultaneously and groups them together in a single list sorted by time value
def otherTracks(chordTrack):
	newMaster = []
	masterChord = chordTrack[0]
	trackToAdd = chordTrack[1]
	
	while len(trackToAdd) > 0:		
		#continually add to newMaster since masterChord is empty
		if len(masterChord) == 0:
			newMaster += masterChord
			break

		# find time values to compare
		masterVal = masterChord[0][0][1]
		trackVal = trackToAdd[0][0][1]
		
		if masterVal == trackVal:
			newChord = masterChord[0]
			newChord += trackToAdd[0]
			newMaster.append(newChord)
			masterChord.pop(0)
			trackToAdd.pop(0)
		elif masterVal < trackVal:
			newMaster.append(masterChord[0])
			masterChord.pop(0)
		else:
			newMaster.append(trackToAdd[0])
			trackToAdd.pop(0)
	if len(masterChord) > 0:
		newMaster += trackToAdd
	return newMaster

# finds all the riffs that are similar in the track with the threshold value 
# specified (currently 0.85) by using parsemidi.similarity
def findRiff(master, start, riffLength, riffCounter):
	accuracies = []
	riff = master[start:riffLength]
	for i in range(start+riffLength, len(master)-riffLength, 1):
		result = parsemidi.similarity(riff, master[i:i+riffLength])
		if result >= 0.85:
			accuracies.append([(i, i+riffLength, result), riffCounter])
	return accuracies

# generates a probability matrix that holds the probabilities of expected
# sequence based on previous sequences. Also generates a dictionary of 
# different transition sections; the key is the note and the values are the
# different sections that it can transition to. This is based on finding the 
# last note in the section and seeing which section follows
def generateProbMatrix(riff, master):
	sequence = []
	pMat = []
	
	# store the sequence from the riff
	for i in range(len(riff)):
		sequence.append(riff[i][-1])
	# create empty matrix to hold probabilities
	for i in range(max(sequence)):
		pMat.append([0] * max(sequence))
	for sec in range(len(sequence)-2):
		pMat[sequence[sec]][sequence[sec+1]] += 1
	for i in range(len(pMat)):
		for j in range(len(pMat[i])):
			if sum(pMat[i]) != 0:
				newSum = float(pMat[i][j]) / float(sum(pMat[i]))
				pMat[i][j] = newSum
	print 'Original sequence:\n', sequence

	#THE BELOW CODE GENERATES A DICT BASED ON TRANSITION POINTS
	#noteDict has the note as a key and the next sections as the value
	noteDict = {}
	for i in range(len(riff) - 1):
		lastNoteInRiff = riff[i][0][1] - 1
		prevNote = master[lastNoteInRiff][0][4] #take first note in chord
		nextSection = riff[i + 1][-1]
		
		if prevNote not in noteDict:
			noteDict[prevNote] = [nextSection]
		else:
			noteDict[prevNote].append(nextSection)
	print noteDict
	return (pMat, noteDict)

# returns the next section based on the probabilities in pMat
# if the next section is not a transition point from the last note in the
# previous section, the pop that sequence and return
def getNextRiff(generatedSeq, pMat, noteDict, listedSong):
	import random
	
	totals = []	
	running_total = 0
	for w in pMat[generatedSeq[-1]]:
		running_total += w
		totals.append(running_total)
	rnd = random.random() * running_total
	for i in range(len(totals)):
		total = totals[i]
		if rnd < total:
			generatedSeq.append(i)
			lastLastSec = generatedSeq[-2]
			lastNote = listedSong[-1][0][4]
			if lastNote in noteDict:
				if i not in noteDict[lastNote]:
					generatedSeq.pop()
			else:
				generatedSeq.pop()
			break;
	return generatedSeq

# a helper function for generateNotes
# returns a dictionary of the section number as the key and the different
# sections in the song as values 
def generateRiffDictionary(riff):
	riffChoice = {}
	for i in range(len(riff)):
		if riff[i][-1] not in riffChoice:
			riffChoice[riff[i][-1]] = [(riff[i][0][0], riff[i][0][1])]
		else:
			riffChoice[riff[i][-1]].append((riff[i][0][0], riff[i][0][1]))
	print "Riff Dictionary:"
	print riffChoice
	return riffChoice

def generateNotes(riff, master, pMat, noteDict, model, filename):
	#generate dictionary of all possible riffs
	riffChoice = generateRiffDictionary(riff)
	
	#from the dictionary of riffs, get a random one for the sequence
	from random import choice
	noteOn = 0
	song = []
	listedSong = []
	listedTimes = []
	temp = []
	seq = [0]	
	#choose a random sequence from the dictionary and put the chorded notes
	# in listedSong
	#for i in range(len(seq)):
	while seq[-1] != (len(pMat) - 1):
		selectedRiff = choice(riffChoice[seq[-1]])
		riffNotes = master[selectedRiff[0]:selectedRiff[1]+1]
		if riffNotes == []:
			continue
		# subtracts first note from the noteOn value in order to set relative duration
		duration = riffNotes[0][0][1] - noteOn
		for k in range(len(riffNotes)):
			currentChord = []
			#adjusts duration from riff to be relative to new placement
			for j in range(len(riffNotes[k])):
				currentNote = ['note', riffNotes[k][j][1] - duration]
				currentNote.append(riffNotes[k][j][2] - riffNotes[k][j][1])
				currentNote.append(riffNotes[k][j][3])
				currentNote.append(riffNotes[k][j][4])
				currentChord.append(currentNote)
				# this finds the correct placement of the next note
				noteOn = currentNote[1] + currentNote[2]
				#noteOn = currentNote[1]
			listedSong.append(currentChord)
	
		prevseq = seq
		seq = getNextRiff(seq, pMat, noteDict, listedSong)
		# Attempt to not have repeated sections
		#if len(seq) > 2 and seq[-1] == seq[-2]:
			#seq.pop()
			#seq = getNextRiff(seq, pMat, noteDict, listedSong)
		if len(seq) == len(prevseq):
			listedSong.pop()
	print 'New Sequence:', seq
	
	# append final riff
	selectedRiff = choice(riffChoice[len(pMat)])
	riffNotes = master[selectedRiff[0]:selectedRiff[1]]
	duration = riffNotes[0][0][1] - noteOn
	for k in range(len(riffNotes)):
		currentChord = []
		#adjusts duration from riff to be relative to new placement
		for j in range(len(riffNotes[k])):
			currentNote = ['note', riffNotes[k][j][1] - duration]
			currentNote.append(riffNotes[k][j][2] - riffNotes[k][j][1])
			currentNote.append(riffNotes[k][j][3])
			currentNote.append(riffNotes[k][j][4])
			currentChord.append(currentNote)
		listedSong.append(currentChord)

	#notes are ['note', noteon, duration, track, noteval]
	#right now the master track has the ['note', noteon, noteoff, track, noteval, duration]

	#remove the notes from the embedded list
	for i in range(len(listedSong)):
		for j in range(len(listedSong[i])):
			temp += [listedSong[i][j]]

	#sort the notes by track
	temp.sort(key=lambda x: int(x[3]))
	tracks = []
	#create empty arrays for the tracks
	for i in range(temp[-1][3] + 1):
		tracks.append([])
	#insert the notes into the right tracks
	for i in range(len(temp)):
		tracks[temp[i][3]].append(temp[i])
	#insert the tracks into the song
	for i in range(len(tracks)):
		song.append(tracks[i])
	#insert the header
	song.insert(0, [["ticks",0,256],["time",0,model[0][1][2],model[0][1][3]]])
	import midi
	midi.write(filename, song)
	return

if __name__ == '__main__':
	if len(sys.argv) != 2:
		raise ValueError("Usage is: python findchords.py <midifile>")
    
	# strips off the extension
	songname = sys.argv[1][:-4]
	# turns the midi file into an iterable list
	midiFile = muse.make(songname + ".mid", 1)
	# pulls the notes from the track to find chords
	tracks = chordsInTrack(midiFile)
	# group the chords together as one index in a list; master is a list
	# of lists
	master = otherTracks(tracks)
	# txt file of master for reference
	writer = open(songname + ".txt", "w")
	writer.write(str(master))
	
	riff = []
	riffCounter = 0
	start = 0
	riffLength = 2 # start comparing riffs/sections in groups of 2
	prevaccuracies = []
	while start < len(master):
		# repeatedly call findRiff until the current section does not
		# pass the threshold of similarity. Every time it passes,
		# increase the section length by 1 note
		accuracies = findRiff(master, start, riffLength, riffCounter)
		while(accuracies != []):
			riffLength += 1
			prevaccuracies = accuracies
			accuracies = findRiff(master, start, riffLength, riffCounter)
		# label the first riff as "reference"
		riff.append([(start, start+riffLength-1, "reference"), riffCounter])
		if prevaccuracies != []:
			riff += prevaccuracies
		prevaccuracies = []
		start += riffLength-1
		riffLength = 2
		riffCounter += 1
	riff.sort()
	(pMat, noteDict) = generateProbMatrix(riff, master) #probability matrix
	#newSeq = generateLogicalSequence(pMat, noteDict, master)
	#newSeq = generateSequence(pMat) #new sequence of sections
	generateNotes(riff, master, pMat, noteDict, midiFile, songname + "OP.mid")
	#print midiFile[1]