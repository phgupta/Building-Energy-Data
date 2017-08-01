"""
## this class imports the data from one or multiple .csv files
## Initially this will work for building-level meters data
## Initially this will work with .csv files, then it will incorporate the Lucid API (or others)
## --- Functionality with .csv
## Input (args):
    fileName = Specify file name 
    folder = and path, specify [(via config file?) name mapping to type of meters]
    folderAxis = The direction that the dataframes will be combined based on the folder to folder relationship
    fileAxis = The direction that the dataframes will be combined based on the folder to folder relationship
         - folderAxis/fileAxis = 'concat' or 'merge'
         - typically the folders will represent the time dimension and will be concat (default value)
         - the files will represnt different metering data and will be merged
    
    headRow = which rows to skip, can be a list or single value
    indexCol = which column from the file is the index, all merged dataframes will be merged on the index (dateTime index)

## Output (return): data in a dataframe, metadata table [does not return meta data at the moment]
## Note: may want to have a separate class for data + metadata


V0.1 
- works fine, not tested extensively

V0.2
- added: cast numeric on columns that are "object"

@author Marco Pritoni <marco.pritoni@gmail.com>
@author Jacob Rodriguez  <jbrodriguez@ucdavis.edu>

V0.3
- added functionality where multiple folders and files may be specified
- handles case where not all files are present in all folders, but the program still runs and fills missing data with NaN
- added folderAxis / fileAxis direction functionalities
- added functions: _combine, _head_and_index


TO DO:
    - meta data
    - what if I want to have different headers for different files (currently the header input header = [0,2,3] will skip rows 0,2,3 from all files that are being loaded)
    - add robust test cases
    - improve speed (?)

last modified: August 1 2017
@author Correy Koshnick <ckoshnick@ucdavis.edu>
"""

import os
import pandas as pd
import numpy as np
import timeit

class csv_importer(object):

####################################################################################################################################    
    def __init__(self,
                 fileName=None,
                 folder=None,
                 folderAxis = 'concat',
                 fileAxis = 'merge',
                 headRow=0,
                 indexCol=0,
                 convertCol=True # convertCol specifies if user wants data to all be of numeric type or not. Default is convert to numeric type
                ):
        '''
        When initializing this class it will do the following:
            -Scan the input folder/file structure to determine if there is a single/many files or a single/many folders
            -Manages headRow indexCol sizes with function _head_and_index
            -Loads data from CSV into temp DataFrame until it is properly shaped
            -Once shaped it combined temp DataFrame with main DataFrame
            -Stores final data in self.data
            
            # DOES NOT HANDLE THE list of list for headRow indexCol idea yet. Maybe we wont use that for this case?
        '''
        # the data imported is saved in a dataframe
        self.data=pd.DataFrame()
        self.tempData = pd.DataFrame()        
        
        self.folderAxis = folderAxis.lower()
        self.fileAxis = fileAxis.lower()
   
        if isinstance(folder, list): #########  MANY FOLDER CASES ############
            if isinstance(fileName, list): # MANY FOLDER MANY FILE 
               
                ###--##--## THIS CODE SHOULD BE REMOVED
                _fileList = []
                # Check files input to generate unique list
                for i, folder_ in enumerate(folder):
                    for j, file_ in enumerate(fileName):
                        _fileList.append(file_)
                _fileList = list(set(_fileList))
                ###--##--## END CODE REMOVAL SECTION
                
                for i, folder_ in enumerate(folder):
                    for j, file_ in enumerate(fileName):
                                    
                        # DOES NOT HANDLE THE list of list for headRow indexCol idea yet. Maybe we wont use that for this case?
                       
                        _headRow,_indexCol = self._head_and_index(headRow,indexCol,j)
                        
                        #If folderAxis = fileAxis. Simple _combine
                        if self.folderAxis == self.fileAxis:
                            newData = self._load_csv(file_,folder_,_headRow,_indexCol,convertCol)
                            self.tempData = self._combine(self.tempData,newData,self.fileAxis)
                        #if folderAxis = C and fileAxis = M (MOST COMMON CASE!!)
                        if self.folderAxis == 'concat' and self.fileAxis == 'merge':
                            newData = self._load_csv(file_,folder_,_headRow,_indexCol,convertCol)
                            self.tempData = self._combine(self.tempData,newData,self.fileAxis)
                        #if FolerAxis = M and FileAxis = C 
                        if self.folderAxis == 'merge' and self.fileAxis == 'concat':
                            newData = self._load_csv(file_,folder_,_headRow,_indexCol,convertCol)
                            self.tempData = self._combine(self.tempData,newData,self.fileAxis)
                    
                    self.data = self._combine(self.data,self.tempData,direction=self.folderAxis)
                    
                    self.tempData = pd.DataFrame() #Reset temp data to empty
                    
            else:   #### MANY FOLDER 1 FILE CASE ####
                for i, folder_ in enumerate(folder):
                    _headRow,_indexCol = self._head_and_index(headRow,indexCol,i)
                    newData = self._load_csv(fileName,folder_,_headRow,_indexCol,convertCol)
                    self.tempData = self._combine(self.tempData,newData, direction = self.folderAxis)
                self.data = self.tempData  
               
        else: ###################### SINGLE FOLDER CASES  #####################
            
            if isinstance(fileName, list): #### 1 FOLDER MANY FILES CASE  #####
                for i, file_ in enumerate(fileName):
                    _headRow,_indexCol = self._head_and_index(headRow,indexCol,i)        
                    newData = self._load_csv(file_,folder,_headRow,_indexCol,convertCol)
                    self.tempData = self._combine(self.tempData,newData, direction = self.fileAxis)
                self.data = self.tempData
            
            else: #### SINGLE FOLDER SINGLE FILE CASE ####
                print "#1 FOLDER 1 FILE CASE"
                self.data=self._load_csv(fileName,folder,headRow,indexCol)

#### End __init__
###############################################################################
    
    def _combine(self,
                 oldData,
                 newData,
                 direction
                 ):
        '''
        This function uses merge or concat on newly loaded data 'newData' with the self.tempData storage variable
        '''
        if oldData.empty == True:
            return newData
        else:   
            
            if direction == 'merge':
                return pd.merge(oldData,newData,how='outer',left_index=True,right_index=True,copy=True)
            elif direction == 'concat' or direction.lower == 'concatentate':
                return pd.concat([oldData,newData],copy=True)              
        
    def _head_and_index(self,headRow,indexCol,i):
        # to accept different head and index for each file - following the order in the fileName array
        # example call CSV_Importer( [file1,file2], folder, headRow=[0,4], indexCol=[0,1])
        if isinstance(headRow, list):
            _headRow=headRow[i]
        else:
            _headRow=headRow 
        if isinstance(indexCol, list): 
            _indexCol=indexCol[i]
        else:
            _indexCol=indexCol           
        return _headRow,_indexCol
                    
    def _load_csv(self, 
                  fileName,
                  folder,
                  headRow,
                  indexCol,
                  convertCol
                 ):
        
        #start_time = timeit.default_timer()
        
        if fileName:
            try:
                folder = os.path.join('..',folder) # Appending onto current folder to get relative directory
                path = os.path.join(folder,fileName)
                
                print "Current path is %s " %path
                
                if headRow >0:                
                    data = pd.read_csv(path, index_col=indexCol,skiprows=[i for i in (range(headRow-1))]) # reads file and puts it into a dataframe                
                    try: # convert time into datetime format
                        data.index = pd.to_datetime(data.index, format = '%m/%d/%y %H:%M') #special case format 1/4/14 21:30
                    except:
                        data.index = pd.to_datetime(data.index, dayfirst=False, infer_datetime_format = True)             
    
                else:
                    data = pd.read_csv(path, index_col=indexCol)# reads file and puts it into a dataframe
                    try: # convert time into datetime format
                        data.index = pd.to_datetime(data.index, format = '%m/%d/%y %H:%M') #special case format 1/4/14 21:30
                    except:
                        data.index = pd.to_datetime(data.index, dayfirst=False, infer_datetime_format = True)   

            except IOError:
                  print 'Failed to load %s' %path + ' file missing!'
                  return pd.DataFrame()      
        else: 
            print 'NO FILE NAME'
            return
    
            if convertCol == True: # Convert all columns to numeric type if option set to true. Default option is true.
                for col in data.columns: # Check columns in dataframe to see if they are numeric
                    if(data[col].dtype != np.number): # If particular column is not numeric, then convert to numeric type
                          data[col]=pd.to_numeric(data[col], errors="coerce")
        return data
# END functions   
###############################################################################

def _test():
    start_time = timeit.default_timer()
    folder=['test2','test3']
    fileName=["data1.csv","data3.csv"]
    rows = [0,4]
    cols = 0
    p = csv_importer(fileName,folder,headRow=rows,indexCol=cols,folderAxis='merge',fileAxis = 'concat')
    elapsed = timeit.default_timer() - start_time
    print p.data.head(10)
    print p.data.shape
    print elapsed, ' seconds to run'

if __name__=='__main__':
    _test()


