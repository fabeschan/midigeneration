import muse, parsemidi, sys, pickle

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
		lastNoteInRiff = riff[i][0][1]
		prevNote = master[lastNoteInRiff][0][4] #take first note in chord
		nextSection = riff[i + 1][-1]
		
		if prevNote not in noteDict:
			noteDict[prevNote] = [nextSection]
		else:
			noteDict[prevNote].append(nextSection)
	#print noteDict
	return (pMat, noteDict)

if __name__ == '__main__':
	if len(sys.argv) != 1:
		raise ValueError("Usage is: python createmodel.py")
	
	# strips off the extension from file names
	songname = raw_input('Enter midi file for model: ')[:-4]
	model = raw_input('Enter the name for the output model: ')
    
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
	writer.close()
	
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
	(pMat, noteDict) = generateProbMatrix(riff, master)

	# pickle the variables and write them to the file to be used later
	writemodel = open(model, "w")
	writemodel.write("---RIFF---\n")
	pickle.dump(riff, writemodel)
	writemodel.write("\n---MASTER---\n")
	pickle.dump(master, writemodel)
	writemodel.write("\n---PMAT---\n")
	pickle.dump(pMat, writemodel)
	writemodel.write("\n---NOTEDICT---\n")
	pickle.dump(noteDict, writemodel)
	writemodel.write("\n---MODEL---\n")
	pickle.dump(midiFile, writemodel)
	writemodel.close()
