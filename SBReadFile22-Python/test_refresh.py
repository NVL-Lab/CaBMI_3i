__copyright__  = "Copyright (c) 2022, Intelligent Imaging Innovations, Inc. All rights reserved.  All rights reserved."
__license__  = "This source code is licensed under the BSD-style license found in the LICENSE file in the root directory of this source tree."

from SBReadFile import *
from matplotlib import pyplot as plt
import numpy as np
import sys, getopt
import time

import random

def print_usage():
    print ('usage:\npython ',os.path.basename(__file__),' -s sldy_file [-i image_number] [-c channel_number] [-p plot_interval]')
    print ('or (long form)\npython ',os.path.basename(__file__),' --sldy_file=file_path [--image_number=value] [--channel_number=value] [--plot_interval=value]')

def main(argv):
    theSBFileReader = SBReadFile()

    #work on the first capture
    theCapture = 0
    #work on the first channel
    theChannel = 0
    #plot frequency in timepoints
    thePlotFrequency = 10

    if len(sys.argv) < 3:
        print_usage()
        sys.exit(2)

    theFileName = ''
    try:
        opts, args = getopt.getopt(argv,"hi:c:p:s:",["help","sldy_file=","image_number=","channel_number=","plot_interval="])
    except getopt.GetoptError as err:
        print(err)
        print_usage()
        sys.exit()
    for opt, arg in opts:
        if opt in ("-h","--help"):
            print_usage()
            sys.exit()
        elif opt in ("-s", "--sldy_file"):
            theFileName = arg
        elif opt in ("-i", "--image_number"):
            theCapture = int(arg)
        elif opt in ("-c", "--channel_number"):
            theChannel = int(arg)
        elif opt in ("-p", "--plot_interval"):


            thePlotFrequency = int(arg)

    if theFileName == "":
        print_usage()
        sys.exit()
    print ('Input file: ', theFileName,' image number: ',theCapture, ' channel number: ',theChannel)

    theSecToWait = 500
    #this secion tries to open the file and see if there is data
    #otherwise it retries every second up to "theSecToWait" seconds
    for theTry in range(1,theSecToWait):
        if os.path.isfile(theFileName) == True:
            try:
                theRes = theSBFileReader.Open(theFileName,All=False) # do not load all the metadata, just essential
                theImageName = theSBFileReader.GetImageName(theCapture)
                break
            except:
                time.sleep(1) # sleep 1 sec
                print (theTry,"...")
                continue
        elif theTry==1:
            print ('Input file does not exist, retrying for up to ' , theSecToWait, " seconds\nOr hit Ctrl+c to exit")
        if theTry == theSecToWait-1:
            print ('Giving up')
            sys.exit()
        time.sleep(1) # sleep 1 sec
        print (theTry,"...")
        

    theRes = theSBFileReader.Open(theFileName,All=False) # do not load all the metadata, just essential
    if not theRes:
        #print ('Cannot open the file: ', theFileName)
        sys.exit()


    
    theImageName = theSBFileReader.GetImageName(theCapture)
    print ("*** the image name: ",theImageName)

    theImageComments = theSBFileReader.GetImageComments(theCapture)
    print ("*** the image comments: ",theImageComments)

    theNumPositions = theSBFileReader.GetNumPositions(theCapture)
    print ("*** the image num positions: ",theNumPositions)

    theNumTimepoints = theSBFileReader.GetNumTimepoints(theCapture)
    print ("*** the image num timepoints: ",theNumTimepoints)

    theNumChannels = theSBFileReader.GetNumChannels(theCapture)
    print ("*** the image num channels: ",theNumChannels)

    theX,theY,theZ = theSBFileReader.GetVoxelSize(theCapture)
    print ("*** the voxel x,y,z size is: ",theX,theY,theZ)

    theY,theM,theD,theH,theMn,theS = theSBFileReader.GetCaptureDate(theCapture)
    print ("*** the date yr/mn/day/hr/min/sec is: ",theY,theM,theD,theH,theMn,theS)

    #theXmlDescriptor = theSBFileReader.GetAuxDataXMLDescriptor(theCapture,theChannel)
    #print ("*** theXmlDescriptor is " ,theXmlDescriptor)

    #theLen,theType = theSBFileReader.GetAuxDataNumElements(theCapture,theChannel)
    #print ("*** theLen,theType ",theLen,theType)

    #theXmlData =   theSBFileReader.GetAuxSerializedData(theCapture,theChannel,0)
    #print ("*** theXmlData is " ,theXmlData)


    theNumRows = theSBFileReader.GetNumYRows(theCapture)
    theNumColumns = theSBFileReader.GetNumXColumns(theCapture)
    theNumPlanes = theSBFileReader.GetNumZPlanes(theCapture)
    theZplane = int(theNumPlanes/2)
    #create a figure for animation
    fig = plt.figure(0)
    title = "Timepoint: {tp:6d}, Mean: {mn:.1f}"
    theFirstTP = 0
    theNoProgress = 0;
    theTimePaused = 0;
    theMaxWaitS = 5 # wait at most 5 seconds. If over this, quit
    #theSleepS = 0.1 # sleep between refreshes
    theSleepS = 0.01 # sleep between refreshes
    #st = time.time()
    total_time_elapsed = []
    try:
        for theRetry in range(0,10000):
            for theTimepoint in range(theFirstTP,theNumTimepoints):
                st = time.time()
                image = theSBFileReader.ReadImagePlaneBuf(theCapture,0,theTimepoint,theZplane,0,True) #captureid,position,timepoint,zplane,channel,as 2d
                #print ("*** The read buffer len is: " , len(image))
                #calculate mean intensity using numpy
                theMean = np.mean(image)
               
                '''
                Access random cell amount (16x16)
                '''
                start_row = random.randint(0, theNumRows - 16)
                start_col = random.randint(0, theNumColumns - 16)
                sub_image = image[start_row:start_row + 16, start_col:start_col + 16]
                theSubMean = np.mean(sub_image)
                
                print ("*** theTimepoint: " , theTimepoint, "The mean: ",theMean)
                print ("Sub-image shape: ", sub_image.shape, " The mean of sub matrix: ",theSubMean)
                if theMean==0:
                    #streaming has missed a timepoint
                    #insert a break here
                    print ("****** Mean is 0 ****** ")

                #plot the slice every n timepoints
                if theTimepoint%thePlotFrequency==999: # For now
                    if theTimepoint == 0:
                        img_artist = plt.imshow(image)
                    else:
                        img_artist.set_data(image)
                    plt.draw()
                    fig.canvas.flush_events()
                    plt.title(title.format(tp=theTimepoint,mn=theMean),loc='left')
                    try:
                        plt.pause(0.01)
                    except KeyboardInterrupt:
                        print("Keyboard Interrupt")
                        sys.exit()

                et = time.time()
                elapsed_time = et - st - theTimePaused
                total_time_elapsed.append(elapsed_time)
                print(f"****** Time is {elapsed_time} ******\n")

            # see if there are any new timepoints
            theSBFileReader.Refresh(theCapture)
            if theFirstTP == theNumTimepoints:
                theNoProgress += 1
                time.sleep(theSleepS) # sleep 10 ms
                theTimePaused += theSleepS
            else:
                theNoProgress = 0
                time.sleep(theSleepS)

            # if we have waited too long, quit
            if theNoProgress * theSleepS  > theMaxWaitS:
                break

            #loop again
            theFirstTP = theNumTimepoints;
            theNumTimepoints = theSBFileReader.GetNumTimepoints(theCapture)-1
            
    except:
        print("Keyboard Interrupt")
        
    #et = time.time()
    #elapsed_time = et - st - theTimePaused
    #print('Execution time per loop iteration:', elapsed_time/theNumTimepoints, " s", ", waited for: ",theTimePaused," s")

    time_mean = sum(total_time_elapsed) / len(total_time_elapsed)
    diffs = [total_time_elapsed[i+1] - total_time_elapsed[i] for i in range(len(total_time_elapsed)-1)]
    diffs_mean = abs(sum(diffs) / len(diffs))
    print('Execution time per loop iteration:', time_mean, " s", ", waited for: ",theTimePaused," s")
    print('Mean difference per loop iteration:', diffs_mean)

    thresh = 0.03 #ms
    plt.plot(total_time_elapsed, marker='o', linestyle='-')
    if max(total_time_elapsed) >= thresh:
        plt.axhline(y=thresh, linestyle='--', color='r')
    plt.title('Iteration Time')
    plt.xlabel('Timepoint')
    plt.ylabel('Time (seconds)')
    plt.show()

    data = input("Please hit Enter to exit:\n")
    print("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
    


