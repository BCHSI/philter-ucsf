import re
import warnings
import json
import os
import nltk
import itertools
import chardet
import pickle
from chardet.universaldetector import UniversalDetector
from nltk.stem.wordnet import WordNetLemmatizer
from coordinate_map import CoordinateMap
from nltk.tag.stanford import StanfordNERTagger
import subprocess
import numpy
import random
import string


class Philter:
    """ 
        General text filtering class,
        can filter using whitelists, blacklists, regex's and POS
    """
    def __init__(self, config):
        if "verbose" in config:
            self.verbose = config["verbose"]
        if "run_eval" in config:
            self.run_eval = config["run_eval"]
        if "freq_table" in config:
            self.freq_table = config["freq_table"]
        if "initials" in config:
            self.initials = config["initials"]                     
        if "finpath" in config:
            if not os.path.exists(config["finpath"]):
                raise Exception("Filepath does not exist", config["finpath"])
            self.finpath = config["finpath"]
        if "foutpath" in config:
            if not os.path.exists(config["foutpath"]):
                raise Exception("Filepath does not exist", config["foutpath"])
            self.foutpath = config["foutpath"]
        if "anno_folder" in config:
            if not os.path.exists(config["anno_folder"]):
                raise Exception("Filepath does not exist", config["anno_folder"])
            self.anno_folder = config["anno_folder"]
        
        if "coords" in config:
            self.coords = config["coords"]
        
        if "eval_out" in config:
            self.eval_outpath = config["eval_out"]

        if "outformat" in config:
            self.outformat = config["outformat"]
        else:
            self.outformat = "asterisk"
        
        if "ucsfformat" in config:
            self.ucsf_format = config["ucsfformat"]
       
        if "filters" in config:
            if not os.path.exists(config["filters"]):
                raise Exception("Filepath does not exist", config["filters"])
            self.patterns = json.loads(open(config["filters"], "r").read())

        if "xml" in config:
            if not os.path.exists(config["xml"]):
                raise Exception("Filepath does not exist", config["xml"])
            self.xml = json.loads(open(config["xml"], "r", encoding='utf-8').read())

        if "stanford_ner_tagger" in config:
            if not os.path.exists(config["stanford_ner_tagger"]["classifier"]) and config["stanford_ner_tagger"]["download"] == False:
                raise Exception("Filepath does not exist", config["stanford_ner_tagger"]["classifier"])
            else:
                #download the ner data
                process = subprocess.Popen("cd generate_dataset && ./download_ner.sh".split(), stdout=subprocess.PIPE)
                output, error = process.communicate()
            self.stanford_ner_tagger_classifier = config["stanford_ner_tagger"]["classifier"]
            if not os.path.exists(config["stanford_ner_tagger"]["jar"]):
                raise Exception("Filepath does not exist", config["stanford_ner_tagger"]["jar"])
            self.stanford_ner_tagger_jar = config["stanford_ner_tagger"]["jar"]
                #we lazy load our tagger only if there's a corresponding pattern
        self.stanford_ner_tagger = None

        if "cachepos" in config and config["cachepos"]:
            self.cache_to_disk = True
            self.pos_path = config["cachepos"]
            if not os.path.isdir(self.pos_path):
                os.makedirs(self.pos_path)
        else:
            self.cache_to_disk = False
            self.pos_path = None 

        #All coordinate maps stored here
        self.coordinate_maps = []

        #create a memory for pos tags
        self.pos_tags = {}

        #create a memory for tokenized text
        self.cleaned = {}

        #create a memory for include coordinate map
        self.include_map = CoordinateMap()

        #create a memory for exclude coordinate map
        self.exclude_map = CoordinateMap()

        #create a memory for FULL exclude coordinate map (including non-whitelisted words)
        self.full_exclude_map = {}

        #create a memory for the list of known PHI types
        self.phi_type_list = ['DATE','Patient_Social_Security_Number','Email','Provider_Address_or_Location','Age','Name','OTHER','ID','NAME','LOCATION','CONTACT','AGE']
        
        #create a memory for the corrdinate maps of known PHI types    
        self.phi_type_dict = {}
        for phi_type in self.phi_type_list:
            self.phi_type_dict[phi_type] = [CoordinateMap()]

        #create a memory for stored coordinate data
        self.data_all_files = {}

        #create a memory for pattern index, with titles
        self.pattern_indexes = {}

        #create a memory for clean words
        #self.clean_words = {}

        #create directory for pos data if it doesn't exist
        #pos_path = "./data/pos_data/"
        #self.pos_path = "./data/pos_data/" + self.random_string(10) + "/"


        #initialize our patterns
        self.init_patterns()


    def get_pos(self, filename, cleaned):
        if self.cache_to_disk:
            pos_path = self.pos_path
            filename = filename.split("/")[-1]
            file_ = os.path.join( pos_path , filename )
            if filename not in self.pos_tags:
                self.pos_tags = {}
                if not os.path.isfile(file_):
                    with open(file_, 'wb') as f:
                        tags = nltk.pos_tag(cleaned)
                        pickle.dump(tags, f)
                        return tags
                else:
                    with open(file_, 'rb') as f:
                        self.pos_tags[filename] = pickle.load(f)
        else:
            if filename not in self.pos_tags:
                self.pos_tags = {}
                self.pos_tags[filename] = nltk.pos_tag(cleaned)
            return self.pos_tags[filename]



            #self.pos_tags[filename] = nltk.pos_tag(cleaned)
        return self.pos_tags[filename]
    #def get_pos_original(self, filename, cleaned):
    #    if filename not in self.pos_tags:
    #        self.pos_tags = {}
    #        self.pos_tags[filename] = nltk.pos_tag(cleaned)
    #    return self.pos_tags[filename]
    
    def get_clean(self, filename, text, pre_process= r"[^a-zA-Z0-9]"):
        if filename not in self.cleaned:
            self.cleaned = {}
            # Use pre-process to split sentence by spaces AND symbols, while preserving spaces in the split list
            lst = re.split("(\s+)", text)
            cleaned = []
            for item in lst:
                if len(item) > 0:
                    if item.isspace() == False:
                        split_item = re.split("(\s+)", re.sub(pre_process, " ", item))
                        for elem in split_item:
                            if len(elem) > 0:
                                cleaned.append(elem)
                    else:
                        cleaned.append(item)
            self.cleaned[filename] = cleaned
        return self.cleaned[filename]
    #def get_clean_word(self, filename, word):
    #    if filename not in self.cleaned:
    #        self.clean_words = {}
    #        self.clean_words[filename] = {}
    #    if word not in self.clean_words[filename]:
    #        self.clean_words[filename][word] = re.sub(r"[^a-zA-Z0-9]+", "", word.lower().strip())
    #    return self.clean_words[filename][word]

    #def get_clean_word2(self, filename, word):
    #    return re.sub(r"[^a-zA-Z0-9]+", "", word.lower().strip())
    #    if word not in self.clean_words:
    #        self.clean_words[word] = re.sub(r"[^a-zA-Z0-9]+", "", word.lower().strip())
    #    return self.clean_words[word]
    
    def init_patterns(self):
        """ given our input pattern config will load our sets and pre-compile our regex"""

        known_pattern_types = set(["regex", "set", "regex_context","stanford_ner", "pos_matcher", "match_all"])
        require_files = set(["regex", "set"])
        require_pos = set(["pos_matcher"])
        set_filetypes = set(["pkl", "json"])
        regex_filetypes = set(["txt"])
        reserved_list = set(["data", "coordinate_map"])

        #first check that data is formatted, can be loaded etc. 
        for i,pattern in enumerate(self.patterns):
            self.pattern_indexes[pattern['title']] = i
            if pattern["type"] in require_files and not os.path.exists(pattern["filepath"]):
                raise Exception("Config filepath does not exist", pattern["filepath"])
            for k in reserved_list:
                if k in pattern:
                    raise Exception("Error, Keyword is reserved", k, pattern)
            if pattern["type"] not in known_pattern_types:
                raise Exception("Pattern type is unknown", pattern["type"])
            if pattern["type"] == "set":
                if pattern["filepath"].split(".")[-1] not in set_filetypes:
                    raise Exception("Invalid filteype", pattern["filepath"], "must be of", set_filetypes)
                self.patterns[i]["data"] = self.init_set(pattern["filepath"])  
            if pattern["type"] == "regex":
                if pattern["filepath"].split(".")[-1] not in regex_filetypes:
                    raise Exception("Invalid filteype", pattern["filepath"], "must be of", regex_filetypes)
                self.patterns[i]["data"] = self.precompile(pattern["filepath"])
            elif pattern["type"] == "regex_context":
                if pattern["filepath"].split(".")[-1] not in regex_filetypes:
                    raise Exception("Invalid filteype", pattern["filepath"], "must be of", regex_filetypes)
                self.patterns[i]["data"] = self.precompile(pattern["filepath"])
                #print(self.precompile(pattern["filepath"]))
    
    def precompile(self, filepath):
        """ precompiles our regex to speed up pattern matching"""
        regex = open(filepath,"r").read().strip()
        re_compiled = None
        with warnings.catch_warnings(): #NOTE: this is not thread safe! but we want to print a more detailed warning message
            warnings.simplefilter(action="error", category=FutureWarning) # in order to print a detailed message
            try:
                re_compiled = re.compile(regex)
            except FutureWarning as warn:
                print("FutureWarning: {0} in file ".format(warn) + filepath)
                warnings.simplefilter(action="ignore", category=FutureWarning)
                re_compiled = re.compile(regex) # assign nevertheless
        return re_compiled
               
    def init_set(self, filepath):
        """ loads a set of words, (must be a dictionary or set shape) returns result"""
        map_set = {}
        if filepath.endswith(".pkl"):
            try:
                with open(filepath, "rb") as pickle_file:
                    map_set = pickle.load(pickle_file)
            except UnicodeDecodeError:
                with open(filepath, "rb") as pickle_file:
                    map_set = pickle.load(pickle_file, encoding = 'latin1')
        elif filepath.endswith(".json"):
            map_set = json.loads(open(filepath, "r").read())

        else:
            raise Exception("Invalid filteype",filepath)
        return map_set

    def map_coordinates(self, allowed_filetypes=set(["txt", "ano"])):
        """ Runs the set, or regex on the input data 
            generating a coordinate map of hits given 
            (this performs a dry run on the data and doesn't transform)
        """
        in_path = self.finpath
        if not os.path.exists(in_path):
            raise Exception("Filepath does not exist", in_path)
        
        #create coordinate maps for each pattern
        for i,pat in enumerate(self.patterns):
            self.patterns[i]["coordinate_map"] = CoordinateMap()

        for root, dirs, files in os.walk(in_path):
            for f in files:

                filename = os.path.join(root, f)

                if filename.split(".")[-1] not in allowed_filetypes:
                    if self.verbose:
                        print("Skipping: ", filename)
                    continue                
                #self.patterns[i]["coordinate_map"].add_file(filename)

                encoding = self.detect_encoding(filename)
                if __debug__: print("reading text from " + filename)
                txt = open(filename,"r", encoding=encoding['encoding'], errors='surrogateescape').read()

                # Get full self.include/exclude map before transform
                self.data_all_files[filename] = {"text":txt, "phi":[],"non-phi":[]}

                #create an intersection map of all coordinates we'll be removing
                self.exclude_map.add_file(filename)

                #create an interestion map of all coordinates we'll be keeping
                self.include_map.add_file(filename)

                # add file to phi_type_dict
                for phi_type in self.phi_type_list:
                    self.phi_type_dict[phi_type][0].add_file(filename)

                # initialize phi type
                phi_type = "OTHER"

                #### Create inital self.exclude/include for file

                for i,pat in enumerate(self.patterns):
                    if pat["type"] == "regex":
                        self.map_regex(filename=filename, text=txt, pattern_index=i)
                    elif pat["type"] == "set":
                        self.map_set(filename=filename, text=txt, pattern_index=i)
                    elif pat["type"] == "regex_context":
                        self.map_regex_context(filename=filename, text=txt, pattern_index=i)
                    elif pat["type"] == "stanford_ner":
                        self.map_ner(filename=filename, text=txt, pattern_index=i)
                    elif pat["type"] == "pos_matcher":
                        self.map_pos(filename=filename, text=txt, pattern_index=i)
                    elif pat["type"] == "match_all":
                        self.match_all(filename=filename, text=txt, pattern_index=i)
                    else:
                        raise Exception("Error, pattern type not supported: ", pat["type"])
                    self.get_exclude_include_maps(filename, pat, txt)


                #create intersection maps for all phi types and add them to a dictionary containing all maps

                # get full exclude map (only updated either on-command by map_regex_context or at the very end of map_coordinates)
                self.full_exclude_map[filename] = self.include_map.get_complement(filename, txt)
                
                for phi_type in self.phi_type_list:
                    for start,stop in self.phi_type_dict[phi_type][0].filecoords(filename):
                        self.data_all_files[filename]["phi"].append({"start":start, "stop":stop, "word":txt[start:stop],"phi_type":phi_type, "filepath":""})


        #clear out any data to save ram
        for i,pat in enumerate(self .patterns):
            if "data" in pat:
                del self.patterns[i]["data"]

        return self.full_exclude_map
                
    def map_regex(self, filename="", text="", pattern_index=-1, pre_process= r"[^a-zA-Z0-9]"):
        """ Creates a coordinate map from the pattern on this data
            generating a coordinate map of hits given (dry run doesn't transform)
        """

        if not os.path.exists(filename):
            raise Exception("Filepath does not exist", filename)

        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(patterns))
        coord_map = self.patterns[pattern_index]["coordinate_map"]
        regex = self.patterns[pattern_index]["data"]

        # All regexes except matchall
        if regex != re.compile('.'):
            #if __debug__: print("map_regex(): searching for regex with index " + str(pattern_index))
            #if __debug__ and pattern_index: print("map_regex(): regex is " + str(regex))
            matches = regex.finditer(text)
            
            for m in matches:
                # print(m.group())
                # print(self.patterns[pattern_index]['title'])


                coord_map.add_extend(filename, m.start(), m.start()+len(m.group()))
        
            self.patterns[pattern_index]["coordinate_map"] = coord_map
        
        #### MATCHALL/CATCHALL ####
        elif regex == re.compile('.'):
            # Split note the same way we would split for set or POS matching
            matchall_list = re.split("(\s+)", text)
            matchall_list_cleaned = []
            for item in matchall_list:
                if len(item) > 0:
                    if item.isspace() == False:
                        split_item = re.split("(\s+)", re.sub(pre_process, " ", item))
                        for elem in split_item:
                            if len(elem) > 0:
                                matchall_list_cleaned.append(elem)
                    else:
                        matchall_list_cleaned.append(item)          

            start_coordinate = 0
            for word in matchall_list_cleaned:
                start = start_coordinate
                stop = start_coordinate + len(word)
                word_clean = re.sub(r"[^a-zA-Z0-9]+", "", word.lower().strip())
                if len(word_clean) == 0:
                    #got a blank space or something without any characters or digits, move forward
                    start_coordinate += len(word)
                    continue

                if regex.match(word_clean):
                    coord_map.add_extend(filename, start, stop)
                    
                #advance our start coordinate
                start_coordinate += len(word)

            self.patterns[pattern_index]["coordinate_map"] = coord_map


    def map_regex_context(self, filename="", text="", pattern_index=-1,  pre_process= r"[^a-zA-Z0-9]"):
        """ map_regex_context creates a coordinate map from combined regex + PHI coordinates 
        of all previously mapped patterns
        """

        punctuation_matcher = re.compile(r"[^a-zA-Z0-9*]")

        if not os.path.exists(filename):
            raise Exception("Filepath does not exist", filename)

        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(patterns))
        
        coord_map = self.patterns[pattern_index]["coordinate_map"]
        regex = self.patterns[pattern_index]["data"]
        context = self.patterns[pattern_index]["context"]
        try:
            context_filter = self.patterns[pattern_index]["context_filter"]
        except KeyError:
            warnings.warn("deprecated missing context_filter field in filter " + str(pattern_index) + " of type regex_context, assuming \'all\'", DeprecationWarning)
            context_filter = 'all'

        # Get PHI coordinates
        if context_filter == 'all':
            # current_include_map = self.get_full_include_map(filename)
            current_include_map = self.include_map
            # Create complement exclude map (also excludes punctuation)      
            full_exclude_map = current_include_map.get_complement(filename, text)

        else:
            context_filter_pattern_index = self.pattern_indexes[context_filter]
            full_exclude_map_coordinates = self.patterns[context_filter_pattern_index]['coordinate_map']
            full_exclude_map = {}
            for start,stop in full_exclude_map_coordinates.filecoords(filename):
                full_exclude_map[start] = stop


        # 1. Get coordinates of all include and exclude mathches

        punctuation_matcher = re.compile(r"[^a-zA-Z0-9*]")
        # 2. Find all patterns expressions that match regular expression
        matches = regex.finditer(text)
        # print(full_exclud_map)
        for m in matches:
            
            # initialize phi_left and phi_right
            phi_left = False
            phi_right = False
            
            match_start = m.span()[0]
            match_end = m.span()[1]

            # PHI context left and right
            phi_starts = []
            phi_ends = []
            for start in full_exclude_map:
                phi_starts.append(start)
                phi_ends.append(full_exclude_map[start])
            
            if match_start in phi_ends:
                phi_left = True
            
            if match_end in phi_starts:
                phi_right = True

            # Get index of m.group()first alphanumeric character in match
            tokenized_matches = []
            match_text = m.group()
            split_match = re.split("(\s+)", re.sub(pre_process, " ", match_text))

            # Get all spans of tokenized match (because remove() function requires tokenized start coordinates)
            coord_tracker = 0
            for element in split_match:
                if element != '':
                    if not punctuation_matcher.match(element[0]):
                        current_start = match_start + coord_tracker
                        current_end = current_start + len(element)
                        tokenized_matches.append((current_start, current_end))

                        coord_tracker += len(element)
                    else:
                        coord_tracker += len(element)

            ## Check for context, and add to coordinate map
            if (context == "left" and phi_left == True) or (context == "right" and phi_right == True) or (context == "left_or_right" and (phi_right == True or phi_left == True)) or (context == "left_and_right" and (phi_right == True and phi_left == True)):
                for item in tokenized_matches:
                    coord_map.add_extend(filename, item[0], item[1])

    
        self.patterns[pattern_index]["coordinate_map"] = coord_map


    def match_all(self, filename="", text="", pattern_index=-1):
        """ Simply maps to the entirety of the file """
        if not os.path.exists(filename):
            raise Exception("Filepath does not exist", filename)

        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(patterns))

        coord_map = self.patterns[pattern_index]["coordinate_map"]
        #add the entire length of the file
        coord_map.add(filename, 0, len(text))
        print(0, len(text))
        self.patterns[pattern_index]["coordinate_map"] = coord_map


    def map_set(self, filename="", text="", pattern_index=-1,  pre_process= r"[^a-zA-Z0-9]"):
        """ Creates a coordinate mapping of words any words in this set"""
        if not os.path.exists(filename):
            raise Exception("Filepath does not exist", filename)

        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(patterns))

        map_set = self.patterns[pattern_index]["data"]
        coord_map = self.patterns[pattern_index]["coordinate_map"]
        
        #get part of speech we will be sending through this set
        #note, if this is empty we will put all parts of speech through the set
        check_pos = False
        pos_set = set([])
        if "pos" in self.patterns[pattern_index]:
            pos_set = set(self.patterns[pattern_index]["pos"])
        if len(pos_set) > 0:
            check_pos = True


        cleaned = self.get_clean(filename,text)
        if check_pos:
            pos_list = self.get_pos(filename, cleaned)# pos_list = nltk.pos_tag(cleaned)
        else:
            pos_list = zip(cleaned,range(len(cleaned)))

        pos_list = nltk.pos_tag(cleaned)

        # if filename == './data/i2b2_notes/160-03.txt':
        #     print(pos_list)
        start_coordinate = 0
        for tup in pos_list:
            word = tup[0]
            pos  = tup[1]
            start = start_coordinate
            stop = start_coordinate + len(word)

            # This converts spaces into empty strings, so we know to skip forward to the next real word
            word_clean = re.sub(r"[^a-zA-Z0-9]+", "", word.lower().strip())
            if len(word_clean) == 0:
                #got a blank space or something without any characters or digits, move forward
                start_coordinate += len(word)
                continue

            if check_pos == False or (check_pos == True and pos in pos_set):
                # if word == 'exlap':
                #     print(pos)
                #     print(filename)
                #     print(pos_set)
                #     print(check_pos)

                if word_clean in map_set or word in map_set:
                    coord_map.add_extend(filename, start, stop)
                    #print("FOUND: ",word, "COORD: ",  text[start:stop])
                else:
                    #print("not in set: ",word, "COORD: ",  text[start:stop])
                    #print(word_clean)
                    pass
                    
            #advance our start coordinate
            start_coordinate += len(word)

        self.patterns[pattern_index]["coordinate_map"] = coord_map
  

    def map_pos(self, filename="", text="", pattern_index=-1, pre_process= r"[^a-zA-Z0-9]"):
        """ Creates a coordinate mapping of words which match this part of speech (POS)"""
        if not os.path.exists(filename):
            raise Exception("Filepath does not exist", filename)

        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(patterns))

        if "pos" not in self.patterns[pattern_index]:
            raise Exception("Mapping POS must include parts of speech", pattern_index, "pattern length", len(patterns))
            
        coord_map = self.patterns[pattern_index]["coordinate_map"]
        pos_set = set(self.patterns[pattern_index]["pos"])
        
        # Use pre-process to split sentence by spaces AND symbols, while preserving spaces in the split list

        cleaned = self.get_clean(filename,text)

        pos_list = self.get_pos(filename, cleaned)#pos_list = nltk.pos_tag(cleaned)
        # if filename == './data/i2b2_notes/160-03.txt':
        #     print(pos_list)
        start_coordinate = 0
        for tup in pos_list:
            word = tup[0]
            pos  = tup[1]
            start = start_coordinate
            stop = start_coordinate + len(word)
            #word_clean = self.get_clean_word2(filename,word)
            word_clean = re.sub(r"[^a-zA-Z0-9]+", "", word.lower().strip())
            if len(word_clean) == 0:
                #got a blank space or something without any characters or digits, move forward
                start_coordinate += len(word)
                continue

            if pos in pos_set:    
                coord_map.add_extend(filename, start, stop)
                #print("FOUND: ",word,"POS",pos, "COORD: ",  text[start:stop])
                
            #advance our start coordinate
            start_coordinate += len(word)

        self.patterns[pattern_index]["coordinate_map"] = coord_map

    def map_ner(self, filename="", text="", pattern_index=-1, pre_process= r"[^a-zA-Z0-9]+"):
        """ map NER tagging"""
      
        if not os.path.exists(filename):
            raise Exception("Filepath does not exist", filename)

        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(patterns))

        #load and create an NER tagger if it doesn't exist
        if self.stanford_ner_tagger == None:
            classifier_path = self.stanford_ner_tagger_classifier #'/usr/local/stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz'
            jar_path = self.stanford_ner_tagger_jar #'/usr/local/stanford-ner/stanford-ner.jar'     
            self.stanford_ner_tagger = StanfordNERTagger(classifier_path,jar_path)
        
        coord_map = self.patterns[pattern_index]["coordinate_map"]
        pos_set = set([])
        if "pos" in self.patterns[pattern_index]:
            pos_set = set(self.patterns[pattern_index]["pos"])
        if len(pos_set) > 0:
            check_pos = True

        lst = re.split("(\s+)", text)
        cleaned = []
        for item in lst:
            if len(item) > 0:
                cleaned.append(item)
        
        ner_no_spaces = self.stanford_ner_tagger.tag(cleaned)
        #get our ner tags
        ner_set = {}
        for tup in ner_no_spaces:
            ner_set[tup[0]] = tup[1]
        ner_set_with_locations = {}
        start_coordinate = 0
        for w in cleaned:
            if w in ner_set:
                ner_set_with_locations[w] = (ner_set[w], start_coordinate)
            start_coordinate += len(w)


        #for the text, break into words and mark POS
        #with the parts of speech labeled, match any of these to our coordinate
        #add these coordinates to our coordinate map
        start_coordinate = 0
        for word in cleaned:

            word_clean = re.sub(pre_process, "", word.lower().strip())
            if len(word_clean) == 0:
                #got a blank space or something without any characters or digits, move forward
                start_coordinate += len(word)
                continue
            
            if word in ner_set_with_locations:
                ner_tag = ner_set_with_locations[word][0]
                start = ner_set_with_locations[word][1]
                if ner_tag in pos_set:
                    stop = start + len(word)
                    coord_map.add_extend(filename, start, stop)
                    print("FOUND: ",word, "NER: ", ner_tag, start, stop)
            
                    
            #advance our start coordinate
            start_coordinate += len(word)

        self.patterns[pattern_index]["coordinate_map"] = coord_map

    def folder_walk(self, folder):
        """ utility func will make a generator to walk a folder
            returns root_directory,filename

            for example: 
            foo/, bar001.txt
            foo/, bar002.txt

        """
        for root, dirs, files in os.walk(folder):
            for filename in files:
                yield root,filename

    def get_exclude_include_maps(self, filename, pattern, txt):

        coord_map = pattern["coordinate_map"]
        exclude = pattern["exclude"]
        try:
            filter_path = pattern["filepath"]
        except KeyError:
            filter_path = pattern["title"]
        if "phi_type" in pattern:
            phi_type = pattern["phi_type"]

        # self.patterns[pattern_index]["title"]
        else:
            phi_type = "OTHER"

        for start,stop in coord_map.filecoords(filename):

            if pattern['type'] != 'regex_context':
                if exclude:
                    if not self.include_map.does_overlap(filename, start, stop):
                        self.exclude_map.add_extend(filename, start, stop)
                        self.phi_type_dict[phi_type][0].add_extend(filename, start, stop)

                else:
                    if not self.exclude_map.does_overlap(filename, start, stop):
                        self.include_map.add_extend(filename, start, stop)
                        self.data_all_files[filename]["non-phi"].append({"start":start, "stop":stop, "word":txt[start:stop], "filepath":filter_path})

                    else:
                        pass
###########################       

            # Add regex_context to map separately
            else:
                if exclude:
                    self.exclude_map.add_extend(filename, start, stop)
                    self.include_map.remove(filename, start, stop)
                    self.phi_type_dict[phi_type][0].add_extend(filename, start, stop)
                else:
                    self.include_map.add_extend(filename, start, stop)
                    self.exclude_map.remove(filename, start, stop)
                    self.data_all_files[filename]["non-phi"].append({"start":start, "stop":stop, "word":txt[start:stop], "filepath":filter_path})

###########################
            
        # dont' need to loop through all PHi types -- just current one
        # for start,stop in self.phi_type_dict[phi_type][0].filecoords(filename):
        #     self.data_all_files[filename]["phi"].append({"start":start, "stop":stop, "word":txt[start:stop],"phi_type":phi_type, "filepath":""})


    def transform(self, allowed_filetypes=set(["txt", "ano"])):
        """ transform
            turns input files into output PHI files 
            protected health information will be replaced by the replacement character

            transform the data 
            ORDER: Order is preserved prioritiy, 
            patterns at spot 0 will have priority over patterns at index 2 

            **Anything not caught in these passes will be assumed to be PHI
        """
        in_path = self.finpath
        out_path = self.foutpath

        if self.verbose:
            print("RUNNING TRANSFORM")

        if not os.path.exists(in_path):
            raise Exception("File input path does not exist", in_path)
        
        if not os.path.exists(out_path):
            raise Exception("File output path does not exist", out_path)


        #create our final exclude and include maps, priority order
        for root,f in self.folder_walk(in_path):

            #keeps a record of all phi coordinates and text for a given file
            # data = {}
        
            filename = os.path.join( root , f )

            if filename.split(".")[-1] not in allowed_filetypes:
                if self.verbose:
                    print("Skipping: ", filename)
                continue  

            encoding = self.detect_encoding(filename)
            txt = open(filename,"r", encoding=encoding['encoding']).read()



            #now we transform the text
            fbase, fext = os.path.splitext(f)
            outpathfbase = os.path.join( out_path , fbase )
            if self.outformat == "asterisk":
                with open(outpathfbase+".txt", "w", encoding='utf-8', errors='surrogateescape') as f:
                    contents = self.transform_text_asterisk(txt, filename)
                    f.write(contents)
                    
            elif self.outformat == "i2b2":
                with open(outpathfbase+".xml", "w", errors='xmlcharrefreplace') as f: #TODO: should we have an explicit encoding?
                    contents = self.transform_text_i2b2(self.data_all_files[filename])
                    #print("writing contents to: " + outpathfbase+".xml")
                    f.write(contents)
            else:
                raise Exception("Outformat not supported: ",
                                self.outformat)        

        # print(data_all_files)
        if self.run_eval: #output our data for eval
            json.dump(self.data_all_files, open(self.coords, "w"), indent=4)

    # infilename needed for addressing maps
    def transform_text_asterisk(self, txt, infilename):        
        last_marker = 0
        current_chunk = []
        punctuation_matcher = re.compile(r"[^a-zA-Z0-9*]")

        #read the text by character, any non-punc non-overlaps will be replaced
        contents = []
        for i in range(0, len(txt)):

            if i < last_marker:
                continue
            
            if self.include_map.does_exist(infilename, i):
                #add our preserved text
                start,stop = self.include_map.get_coords(infilename, i)
                contents.append(txt[start:stop])
                last_marker = stop
            elif punctuation_matcher.match(txt[i]):
                contents.append(txt[i])
            else:
                contents.append("*")

        return "".join(contents)

    def transform_text_i2b2(self, tagdata):
        """creates a string in i2b2-XML format"""
        root = "Philter"
        contents = []
        
        contents.append("<?xml version=\"1.0\" ?>\n")
        contents.append("<"+root+">\n")
        contents.append("<TEXT><![CDATA[")

        contents.append(tagdata['text'])
        contents.append("]]></TEXT>\n")
        contents.append("<TAGS>\n")
        for i in range(len(tagdata['phi'])):
            phi_type = tagdata['phi'][i]['phi_type']
            tagcategory = phi_type
            contents.append("<")
            contents.append(phi_type)
            contents.append(" id=\"P")
            contents.append(str(i))
            contents.append("\" start=\"")
            contents.append(str(tagdata['phi'][i]['start']))
            contents.append("\" end=\"")
            contents.append(str(tagdata['phi'][i]['stop']))
            contents.append("\" text=\"")
            contents.append(tagdata['phi'][i]['word'])
            contents.append("\" TYPE=\"")
            contents.append(phi_type)
            contents.append("\" comment=\"\" />\n")
        

        # for loop over complement - PHI, create additional tags (UNKNOWN)
        contents.append("</TAGS>\n")
        contents.append("</"+root+">\n")
        
        return "".join(contents)
            
    def detect_encoding(self, fp):
        if not os.path.exists(fp):
            raise Exception("Filepath does not exist", fp)

        detector = UniversalDetector()
        with open(fp, "rb") as f:
            for line in f:
                detector.feed(line)
                if detector.done: 
                    break
            detector.close()
        return detector.result

    def phi_context(self, filename, word, word_index, words, context_window=10):
        """ helper function, creates our phi data type with source file, and context window"""
        if not os.path.exists(filename):
            raise Exception("Filepath does not exist", filename)

        left_index = word_index - context_window
        if left_index < 0:
            left_index = 0

        right_index = word_index + context_window
        if right_index >= len(words):
            right_index = len(words) - 1
        window = words[left_index:right_index]

        #get which patterns matched this word
        num_spaces = len(words[:word_index])
        

        return {"filename":filename, "phi":word, "context":window}


    def seq_eval(self,
            note_lst, 
            anno_lst,
            filename,
            punctuation_matcher=re.compile(r"[^a-zA-Z0-9*]"), 
            text_matcher=re.compile(r"[a-zA-Z0-9]"), 
            phi_matcher=re.compile(r"\*+")):
        """ 
            Compares two sequences item by item, 
            returns generator which yields: 
            classifcation, word

            classifications can be TP, FP, FN, TN 
            corresponding to True Positive, False Positive, False Negative and True Negative
        """
        
        # print(filename)
        start_coordinate = 0
        for note_word, anno_word in list(zip(note_lst, anno_lst)):

            #print(note_word, anno_word)
            ##### Get coordinates ######
            start = start_coordinate
            stop = start_coordinate + len(note_word)
            note_word_stripped = re.sub(r"[^a-zA-Z0-9\*]+", "", note_word.strip())
            anno_word_stripped = re.sub(r"[^a-zA-Z0-9\*]+", "", anno_word.strip())
            if len(note_word_stripped) == 0:
                #got a blank space or something without any characters or digits, move forward
                start_coordinate += len(note_word)
                continue

            
            if phi_matcher.search(anno_word):
                #this contains phi
                
                if note_word == anno_word:
                    
                    # print(note_word, anno_word,'TP')
                    yield "TP", note_word, start_coordinate

                else:
                    if text_matcher.search(anno_word):

                        #print("COMPLEX", note_word, anno_word)

                        #this is a complex edge case, 
                        #the phi annotation has some characters *'ed, and some not, 
                        #find the overlap and report any string of chars in anno as FP
                        #and any string of chars in note as FN
                        fn_words = []
                        fp_words = []

                        fn_chunk = []
                        fp_chunk = []
                        for n,a in list(zip(note_word, anno_word)):
                            if n == a:
                                #these characters match, clear our chunks
                                if len(fp_chunk) > 0:
                                    fp_words.append("".join(fp_chunk))
                                    fp_chunk = []
                                if len(fn_chunk) > 0:
                                    fn_words.append("".join(fn_words))
                                    fn_chunk = []
                                
                                continue 
                            if a == "*" and n != "*":
                                fn_chunk.append(n)
                            elif a != "*" and n == "*":
                                fp_chunk.append(a)

                        #clear any remaining chunks
                        if len(fp_chunk) > 0:
                            fp_words.append("".join(fp_chunk))
                        if len(fn_chunk) > 0:
                            fn_words.append("".join(fn_words))

                        #now drain the difference
                        for w in fn_words:
                            yield "FN", w, start_coordinate
                        for w in fp_words:
                            yield "FP", w, start_coordinate

                    else:
                        #simpler case, anno word is completely blocked out except punctuation
                        yield "FN", note_word, start_coordinate

            else:
                if note_word.isspace() == False:
                    #this isn't phi
                    if note_word == anno_word:
                        #print(note_word, anno_word, "TN")
                        yield "TN", note_word, start_coordinate
                    else:
                        #print(note_word, anno_word, "FP")
                        yield "FP", anno_word, start_coordinate

            #advance our start coordinate
            start_coordinate += len(note_word) 



    def eval(self,
        config,
        note_path="./data/i2b2_notes/",
        anno_path="data/i2b2_anno/",
        anno_suffix="_phi_reduced.ano",
        in_path="data/i2b2_results/",
        summary_output="data/phi/summary.json",
        phi_matcher=re.compile("\*+"),
        only_digits=False,
        fn_output = "data/phi/fn.txt",
        fp_output = "data/phi/fp.txt",
        fn_tags_context = "data/phi/fn_tags_context.txt",
        fp_tags_context = "data/phi/fp_tags_context.txt",
        fn_tags_nocontext = "data/phi/fn_tags.txt",
        fp_tags_nocontext = "data/phi/fp_tags.txt",
        pre_process=r":|\,|\-|\/|_|~", #characters we're going to strip from our notes to analyze against anno        
        pre_process2= r"[^a-zA-Z0-9]",
        punctuation_matcher=re.compile(r"[^a-zA-Z0-9\*]")):
        """ calculates the effectiveness of the philtering / extraction

            only_digits = <boolean> will constrain evaluation on philtering of only digit types
        """

        if not os.path.exists(anno_path):
            raise Exception("Anno Filepath does not exist", anno_path)
        if not os.path.exists(in_path):
            raise Exception("Input Filepath does not exist", in_path)
        # if not os.path.exists(fn_output):
        #     raise Exception("False Negative Filepath does not exist", fn_output)
        # if not os.path.exists(fp_output):
        #     raise Exception("False Positive Filepath does not exist", fp_output)

        if self.verbose:
            print("RUNNING EVAL")
            
        
        summary = {
            "total_false_positives":0,
            "total_false_negatives":0,
            "total_true_positives": 0,
            "total_true_negatives": 0,
            "false_positives":[], #non-phi words we think are phi
            "true_positives": [], #phi words we correctly identify
            "false_negatives":[], #phi words we think are non-phi
            "true_negatives": [], #non-phi words we correctly identify
            "summary_by_file":{}
        }
        summary_coords = {
            "summary_by_file":{}
        }

        all_fn = []
        all_fp = []

        for root, dirs, files in os.walk(in_path):

            for f in files:
                if not f.endswith(".txt"): # TODO: come up with something better
                    continue               #       to ensure one to one txt file
                                           #       comparisons with anno_path
                #local values per file
                false_positives = [] #non-phi we think are phi
                false_positives_coords = []
                true_positives  = [] #phi we correctly identify
                true_positives_coords = []
                false_negatives = [] #phi we think are non-phi
                false_negatives_coords = []
                true_negatives  = [] #non-phi we correctly identify
                true_negatives_coords = []

                original_filename = os.path.join( note_path , f )
                philtered_filename = os.path.join( root , f )
                anno_filename = os.path.join( anno_path , ''.join(f.split(".")[0])+anno_suffix )

                # if len(anno_suffix) > 0:
                #     anno_filename = os.path.join( anno_folder , f.split(".")[0]+anno_suffix )

                if not os.path.exists(philtered_filename):
                    raise Exception("FILE DOESNT EXIST", philtered_filename)
                
                if not os.path.exists(anno_filename):
                    #print("FILE DOESNT EXIST", anno_filename)
                    continue

                encoding1 = self.detect_encoding(philtered_filename)
                philtered = open(philtered_filename,"r").read()
                
                          
                philtered_words = re.split("(\s+)", philtered)
                # if f == '110-01.txt':
                #     print(philtered_words)
                #     print(len("".join(philtered_words)))
                philtered_words_cleaned = []
                for item in philtered_words:
                    if len(item) > 0:
                        if item.isspace() == False:
                            split_item = re.split("(\s+)", re.sub(punctuation_matcher, " ", item))
                            for elem in split_item:
                                if len(elem) > 0:
                                    philtered_words_cleaned.append(elem)
                        else:
                            philtered_words_cleaned.append(item)
                
               # philtered_words_cleaned = self.get_clean(original_filename, philtered)

                encoding2 = self.detect_encoding(anno_filename)
                anno = open(anno_filename,"r").read()              
                
                anno_words = re.split("(\s+)", anno)
                # if f == '110-01.txt':
                #     print(anno_words)
                #     print(len("".join(anno_words)))
                anno_words_cleaned = []
                for item in anno_words:
                    if len(item) > 0:
                        if item.isspace() == False:
                            split_item = re.split("(\s+)", re.sub(punctuation_matcher, " ", item))
                            for elem in split_item:
                                if len(elem) > 0:
                                    anno_words_cleaned.append(elem)
                        else:
                            anno_words_cleaned.append(item)
                #anno_words_cleaned = self.get_clean(original_filename, anno)
                # if f == '110-01.txt':
                #     print(len(philtered_words_cleaned))
                #     print(len(anno_words_cleaned))               
                for c,w,r in self.seq_eval(philtered_words_cleaned, anno_words_cleaned, f):

                    # Double check that we aren't adding blank spaces or single punctionation characters to our lists
                    if w.isspace() == False and (re.sub(r"[^a-zA-Z0-9\*]+", "", w) != ""):

                        if c == "FP":
                            false_positives.append(w)
                            false_positives_coords.append([w,r])
                            # if w == "she" or w == "no" or w == "he" or w == "increased" or w == "wave" or w == "In" or w == "AS":
                            #     print(w)
                            #     print(f)

                        elif c == "FN":
                            false_negatives.append(w)
                            false_negatives_coords.append([w,r])
                        elif c == "TP":
                            true_positives.append(w)
                            true_positives_coords.append([w,r])
                        elif c == "TN":
                            true_negatives.append(w)
                            true_negatives_coords.append([w,r])

                #update summary
                summary["summary_by_file"][philtered_filename] = {"false_positives":false_positives,"false_negatives":false_negatives, "num_false_negatives":len(false_negatives)}
                summary["total_true_positives"] = summary["total_true_positives"] + len(true_positives)
                summary["total_false_positives"] = summary["total_false_positives"] + len(false_positives)
                summary["total_false_negatives"] = summary["total_false_negatives"] + len(false_negatives)
                summary["total_true_negatives"] = summary["total_true_negatives"] + len(true_negatives)
                all_fp = all_fp + false_positives
                all_fn = all_fn + false_negatives


                # Create coordinate summaries
                summary_coords["summary_by_file"][philtered_filename] = {"false_positives":false_positives_coords,"false_negatives":false_negatives_coords,"true_positives":true_positives_coords}


        if summary["total_true_positives"]+summary["total_false_negatives"] > 0:
            recall = summary["total_true_positives"]/(summary["total_true_positives"]+summary["total_false_negatives"])
        elif summary["total_false_negatives"] == 0:
            recall = 1.0

        if summary["total_true_positives"]+summary["total_false_positives"] > 0:
            precision = summary["total_true_positives"]/(summary["total_true_positives"]+summary["total_false_positives"])
        elif summary["total_true_positives"] == 0:
            precision = 0.0

        if summary["total_true_negatives"]+summary["total_false_positives"] > 0:
            retention = summary["total_true_negatives"]/(summary["total_true_negatives"]+summary["total_false_positives"])
        else:
            retention = 0.0
        
        ################# DETAILED EVAL ##################
        #save the phi we missed
        json.dump(summary, open(summary_output, "w"), indent=4)
        json.dump(all_fn, open(fn_output, "w"), indent=4)
        json.dump(all_fp, open(fp_output, "w"), indent=4)
        
        if self.verbose:
            print('\n')
            print("Uncorrected Results:")
            print('\n')
            print("TP:", summary["total_true_positives"],"FN:", summary["total_false_negatives"], "TN:", summary["total_true_negatives"], "FP:", summary["total_false_positives"])
            print("Global Recall: {:.2%}".format(recall))
            print("Global Precision: {:.2%}".format(precision))
            print("Global Retention: {:.2%}".format(retention))


        ###################### Get phi tags #####################
        if self.verbose:
            print('\n')
            print("RUNNING ERRORCHECK")

        # Get xml summary
        phi = self.xml
        # Create dictionary to hold fn tags
        fn_tags = {}
        fp_tags = {}
        
        # Keep track of recall and precision for each category
        phi_categories = ['Age','Contact','Date','ID','Location','Name','Other']
        # i2b2:
        if not self.ucsf_format:                
            # Define tag list
            i2b2_tags = ['DOCTOR','PATIENT','DATE','MEDICALRECORD','IDNUM','DEVICE','USERNAME','PHONE','EMAIL','FAX','CITY','STATE','ZIP','STREET','LOCATION-OTHER','HOSPITAL','AGE']
            
            i2b2_category_dict = {'DOCTOR':'Name',
            'PATIENT':'Name',
            'DATE':'Date',
            'MEDICALRECORD':'ID',
            'IDNUM':'ID',
            'DEVICE':'ID',
            'USERNAME':'Contact',
            'PHONE':'Contact',
            'EMAIL':'Contact',
            'FAX':'Contact',
            'CITY':'Location',
            'STATE':'Location',
            'ZIP':'Location',
            'STREET':'Location',
            'LOCATION-OTHER':'Location',
            'HOSPITAL':'Location',
            'AGE':'Age'
            }
            
            i2b2_include_tags = ['DOCTOR','PATIENT','DATE','MEDICALRECORD','IDNUM','DEVICE','USERNAME','PHONE','EMAIL','FAX','CITY','STATE','ZIP','STREET','LOCATION-OTHER','HOSPITAL','AGE']
            i2b2_patient_tags = ['PATIENT','DATE','MEDICALRECORD','IDNUM','DEVICE','USERNAME','PHONE','EMAIL','FAX','CITY','STATE','ZIP','STREET','LOCATION-OTHER','HOSPITAL','AGE']
            i2b2_provider_tags = ['DOCTOR','DATE','USERNAME','PHONE','EMAIL','FAX','CITY','STATE','ZIP','STREET',"LOCATION-OTHER",'HOSPITAL']

            rp_summaries = {}
            for i in range(0,len(i2b2_tags)):
                tag = i2b2_tags[i]
                fn_key = tag + '_fns'
                tp_key = tag + '_tps'
                rp_summaries[fn_key] = 0
                rp_summaries[tp_key] = 0

        # ucsf:
        if self.ucsf_format:
            # Define tag list
            ucsf_tags = ['Date','Provider_Name','Phone_Fax','Age','Patient_Name_or_Family_Member_Name','Patient_Address','Patient_Initials','Provider_Address_or_Location','Provider_Initials','Provider_Certificate_or_License','Patient_Medical_Record_Id','Patient_Account_Number','Patient_Social_Security_Number','Patient_Vehicle_or_Device_Id','Patient_Unique_Id','Diagnosis_Code_ICD_or_International','Procedure_or_Billing_Code','Medical_Department_Name','Email','URL_IP','Patient_Biometric_Id_or_Face_Photo','Patient_Language_Spoken','Patient_Place_Of_Work_or_Occupation','Patient_Certificate_or_License','Medical_Research_Study_Name_or_Number','Teaching_Institution_Name','Non_UCSF_Medical_Institution_Name','Medical_Institution_Abbreviation','Unclear']
            
            ucsf_category_dict = {'Date':'Date',
            'Provider_Name':'Name',
            'Phone_Fax':'Contact',
            'Age':'Age',
            'Patient_Name_or_Family_Member_Name':'Name',
            'Patient_Address':'Location',
            'Patient_Initials':'Name',
            'Provider_Address_or_Location':'Location',
            'Provider_Initials':'Name',
            'Provider_Certificate_or_License':'ID',
            'Patient_Medical_Record_Id':'ID',
            'Patient_Account_Number':'ID',
            'Patient_Social_Security_Number':'ID',
            'Patient_Vehicle_or_Device_Id':'ID',
            'Patient_Unique_Id':'ID',
            'Diagnosis_Code_ICD_or_International':'ID',
            'Procedure_or_Billing_Code':'ID',
            'Medical_Department_Name':'Location',
            'Email':'Contact',
            'URL_IP':'Contact',
            'Patient_Biometric_Id_or_Face_Photo':'ID',
            'Patient_Language_Spoken':'Other',
            'Patient_Place_Of_Work_or_Occupation':'Location',
            'Patient_Certificate_or_License':'ID',
            'Medical_Research_Study_Name_or_Number':'ID',
            'Teaching_Institution_Name':'Location',
            'Non_UCSF_Medical_Institution_Name':'Location',
            'Medical_Institution_Abbreviation':'Location',
            'Unclear':'Other'
            }
            
            if self.initials:
                ucsf_include_tags = ['Date','Provider_Name','Phone_Fax','Patient_Name_or_Family_Member_Name','Patient_Address','Provider_Address_or_Location','Provider_Certificate_or_License','Patient_Medical_Record_Id','Patient_Account_Number','Patient_Social_Security_Number','Patient_Vehicle_or_Device_Id','Patient_Unique_Id','Procedure_or_Billing_Code','Email','URL_IP','Patient_Biometric_Id_or_Face_Photo','Patient_Certificate_or_License','Age','Patient_Initials','Provider_Initials']
                ucsf_patient_tags = ['Date','Phone_Fax','Age','Patient_Name_or_Family_Member_Name','Patient_Address','Patient_Initials','Patient_Medical_Record_Id','Patient_Account_Number','Patient_Social_Security_Number','Patient_Vehicle_or_Device_Id','Patient_Unique_Id','Email','URL_IP','Patient_Biometric_Id_or_Face_Photo','Patient_Certificate_or_License']
                ucsf_provider_tags = ['Provider_Name','Phone_Fax','Provider_Address_or_Location','Provider_Initials','Provider_Certificate_or_License','Email','URL_IP']

            else:
                ucsf_include_tags = ['Date','Provider_Name','Phone_Fax','Patient_Name_or_Family_Member_Name','Patient_Address','Provider_Address_or_Location','Provider_Certificate_or_License','Patient_Medical_Record_Id','Patient_Account_Number','Patient_Social_Security_Number','Patient_Vehicle_or_Device_Id','Patient_Unique_Id','Procedure_or_Billing_Code','Email','URL_IP','Patient_Biometric_Id_or_Face_Photo','Patient_Certificate_or_License','Age']
                ucsf_patient_tags = ['Date','Phone_Fax','Age','Patient_Name_or_Family_Member_Name','Patient_Address','Patient_Medical_Record_Id','Patient_Account_Number','Patient_Social_Security_Number','Patient_Vehicle_or_Device_Id','Patient_Unique_Id','Email','URL_IP','Patient_Biometric_Id_or_Face_Photo','Patient_Certificate_or_License']
                ucsf_provider_tags = ['Provider_Name','Phone_Fax','Provider_Address_or_Location','Provider_Certificate_or_License','Email','URL_IP']



            rp_summaries = {}
            for i in range(0,len(ucsf_tags)):
                tag = ucsf_tags[i]
                fn_key = tag + '_fns'
                tp_key = tag + '_tps'
                rp_summaries[fn_key] = 0
                rp_summaries[tp_key] = 0


        # Create dictionaries for unigram and bigram PHI/non-PHI frequencies
        # Diciontary values look like: [phi_count, non-phi_count]
        unigram_dict = {}
        bigram_dict = {}
        corrected_age_fns = 0


        # Loop through all filenames in summary
        for fn in summary_coords['summary_by_file']:
            # print(self.patterns)
            # get input notes filename (for filter analysis wit coordinatemap)
            input_filename = os.path.join( self.finpath , os.path.basename(fn) )

            current_summary =  summary_coords['summary_by_file'][fn]

            # Get corresponding info in phi_notes
            note_name = fn.split('/')[-1]
            
            try:
                anno_name = note_name.split('.')[0] + ".xml"
                text = phi[anno_name]['text']
            except KeyError:
                anno_name = note_name.split('.')[0] + ".txt.xml"
                text = phi[anno_name]['text']
                # except KeyError:
                #     anno_name = note_name.split('.')[0] + "_nounicode.txt.xml"
                #     text = phi[anno_name]['text']                       

            lst = re.split("(\s+)", text)
            cleaned = []
            cleaned_coords = []
            for item in lst:
                if len(item) > 0:
                    if item.isspace() == False:
                        split_item = re.split("(\s+)", re.sub(r"[^a-zA-Z0-9]", " ", item))
                        for elem in split_item:
                            if len(elem) > 0:
                                cleaned.append(elem)
                    else:
                        cleaned.append(item)
            #cleaned = self.get_clean(input_filename)
            # if anno_name == '110-01.xml':
            #     print(anno_name)
            #     #print(cleaned)
            #     print('Anno text:')
            #     print(text)
            
            # Get coords for POS tags
            start_coordinate = 0
            pos_coords = []
            for item in cleaned:
                pos_coords.append(start_coordinate)
                start_coordinate += len(item)

            #print(pos_coords)
            
            pos_list = nltk.pos_tag(cleaned)


            cleaned_with_pos = {}
            for i in range(0,len(pos_list)):
                cleaned_with_pos[str(pos_coords[i])] = [pos_list[i][0], pos_list[i][1]]

            ########## Get FN tags ##########
            phi_list = phi[anno_name]['phi']
            # print(cleaned)
            # print(pos_coords)


            ######### Create unigram and bigram frequency tables #######
            if self.freq_table:

                # Create separate cleaned list/coord list without spaces
                cleaned_nospaces = []
                coords_nospaces = []
                for i in range(0,len(cleaned)):
                    if cleaned[i].isspace() == False:
                        cleaned_nospaces.append(cleaned[i])
                        coords_nospaces.append(pos_coords[i])

                # Loop through all single words and word pairs, and compare with PHI list
                for i in range(0,len(cleaned_nospaces)-1):
                    #cleaned_nospaces[i]= word, coords_nospaces[i] = start coordinate
                    unigram_word = cleaned_nospaces[i].replace('\n','').replace('\t','').replace(' ','').lower()
                    bigram_word = " ".join([cleaned_nospaces[i].replace('\n','').replace('\t','').replace(' ','').lower(),cleaned_nospaces[i+1].replace('\n','').replace('\t','').replace(' ','').lower()])
                    unigram_start = coords_nospaces[i]
                    bigram_start1 = coords_nospaces[i]
                    bigram_start2 = coords_nospaces[i+1]

                    # Loop through PHI list and compare ranges
                    for phi_item in phi_list:
                        try:
                            phi_start = phi_item['start']
                            phi_end = phi_item['end']
                        except KeyError:
                            phi_start = phi_item['spans'].split('~')[0]
                            phi_end = phi_item['spans'].split('~')[1]
                        if unigram_start in range(int(phi_start), int(phi_end)):
                            # This word is PHI and hasn't been added to the dictionary yet
                            if unigram_word not in unigram_dict:
                                unigram_dict[unigram_word] = [1, 0]
                           # This word is PHI and has already been added to the dictionary
                            else:
                                unigram_dict[unigram_word][0] += 1
                        else:
                            # This word is not PHI and hasn't been aded to the dictionary yet
                            if unigram_word not in unigram_dict:
                                unigram_dict[unigram_word] = [0, 1]
                           # This word is not PHI and has already been added to the dictionary
                            else:
                                unigram_dict[unigram_word][1] += 1                               
                        if bigram_start1 in range(int(phi_start), int(phi_end)) and bigram_start2 in range(int(phi_start), int(phi_end)):
                            # This word is PHI and hasn't been added to the dictionary yet
                            if bigram_word not in bigram_dict:
                                bigram_dict[bigram_word] = [1, 0]
                           # This word is PHI and has already been added to the dictionary
                            else:
                                bigram_dict[bigram_word][0] += 1                                
                        else:
                            # This word is not PHI and hasn't been aded to the dictionary yet
                            if bigram_word not in bigram_dict:
                                bigram_dict[bigram_word] = [0, 1]
                           # This word is not PHI and has already been added to the dictionary
                            else:
                                bigram_dict[bigram_word][1] += 1


            # Get tp counts per category
            current_tps = current_summary['true_positives']
            # Initialize list to keep track of non-include tag FPs
            additional_fps = []

            for word in current_tps:
                start_coordinate_tp = word[1]
                for phi_item in phi_list:
                    if self.ucsf_format:
                        phi_start = int(phi_item['spans'].split('~')[0])
                        phi_end = int(phi_item['spans'].split('~')[1])                               
                    else:
                        phi_start = phi_item['start']
                        phi_end = phi_item['end']
                    phi_type = phi_item['TYPE']
                    phi_word = phi_item['text']


                    if not self.ucsf_format:
                        for i in range(0,len(i2b2_tags)):
                            tag = i2b2_tags[i]
                            tp_key = tag + '_tps'
                            if (start_coordinate_tp in range(int(phi_start), int(phi_end))) and (tag == phi_type):
                                rp_summaries[tp_key] += 1
                        # Add these TPs to the FPs list of they are not in the include list
                        if phi_type not in i2b2_include_tags:
                            if (start_coordinate_tp in range(int(phi_start), int(phi_end))):
                                additional_fps.append([text[start_coordinate_tp:start_coordinate_tp + len(word[0])], start_coordinate_tp])                                  
                    #### ucsf
                    if self.ucsf_format:
                        if phi_type not in ucsf_include_tags:
                            if (start_coordinate_tp in range(int(phi_start), int(phi_end))):
                                additional_fps.append([text[start_coordinate_tp:start_coordinate_tp + len(word[0])], start_coordinate_tp])

                        for i in range(0,len(ucsf_tags)):
                            tag = ucsf_tags[i]
                            tp_key = tag + '_tps'
                            if (start_coordinate_tp in range(int(phi_start), int(phi_end))) and (tag == phi_type):
                                rp_summaries[tp_key] += 1
                            # Add these TPs to the FPs list of they are not in the include list
                            # elif (start_coordinate_tp in range(int(phi_start), int(phi_end))) and (tag == phi_type) and (tag not in ucsf_include_tags):
                            #     print(phi_type)
                            #     print([cleaned_with_pos[str(phi_start)][0], phi_start])
                            #     additional_fps.append([cleaned_with_pos[str(phi_start)][0], phi_start])
                            #     print('\n')


            # if additional_fps != []:

            # if anno_name == '110-01.xml':
            # print(anno_name)
            # print(cleaned_dict)
            # print('\n')

            #### i2b2
            if not self.ucsf_format:
                fn_counter_dict = {}
                for i in range(0,len(i2b2_tags)):
                    tag = i2b2_tags[i]
                    tag_fn_counter = tag + '_fn_counter'
                    fn_counter_dict[tag_fn_counter] = 0
            #### ucsf
            if self.ucsf_format:
                fn_counter_dict = {}
                for i in range(0,len(ucsf_tags)):
                    tag = ucsf_tags[i]
                    tag_fn_counter = tag + '_fn_counter'
                    fn_counter_dict[tag_fn_counter] = 0
                          

            fn_tag_summary = {}
            include_exclude_fns = ''

            # print(self.patterns)
            if current_summary['false_negatives'] != [] and current_summary['false_negatives'] != [""]:              
                counter = 0
                current_fns = current_summary['false_negatives']
             
                for word in current_fns:
                    counter += 1
                    false_negative = word[0]
                    start_coordinate_fn = word[1]
                    # print(word, start_coordinate)

                    # initialize list that will hold info on what matched what
                    filter_file_list_exclude = []
                    filter_file_list_include = []

                    # if self.dependent:
                    # Loop through coorinate map objects and match patterns with FPs
                    for i,pattern in enumerate(self.patterns):
                        # print('\n',i, ':')

                        coord_map = pattern["coordinate_map"]
                        exclude_include = pattern["exclude"]
                        try:
                            filter_path = pattern["filepath"]
                        except KeyError:
                            filter_path = pattern["title"]
                        # print('\n')
                        # print(filter_path)
                        for start,stop in coord_map.filecoords(input_filename):
                            # print(start,stop,text[start:stop])
                            # Find intersection between ranges
                            word_range = set(range(start_coordinate_fn, start_coordinate_fn + len(false_negative)))
                            filter_range = set(range(start, stop))
                            intersection = word_range & filter_range
                            if intersection != set():
                                # print("********"+str(start_coordinate_fp)+"********")
                                # print(false_positive)
                                # Add this filter path to the list of things that filtered this word
                                if exclude_include == True:
                                    filter_file_list_exclude.append(filter_path)
                                else:
                                    filter_file_list_include.append(filter_path)
                    # if self.dependent == False:
                    #     filter_file_list_exclude.append('')
                    #     filter_file_list_include.append('')

                    for phi_item in phi_list:                           
                        phi_text = phi_item['text']
                        phi_type = phi_item['TYPE']
                        phi_id = phi_item['id']
                        if self.ucsf_format:
                            phi_start = int(phi_item['spans'].split('~')[0])
                            phi_end = int(phi_item['spans'].split('~')[1])                               
                        else:
                            phi_start = phi_item['start']
                            phi_end = phi_item['end']


                        #### i2b2
                        if not self.ucsf_format:
                            for i in range(0,len(i2b2_tags)):
                                tag = i2b2_tags[i]
                                fn_key = tag + '_fns'
                                tag_fn_counter = tag + '_fn_counter'
                                if (start_coordinate_fn in range(int(phi_start), int(phi_end))) and phi_type == tag:
                                    rp_summaries[fn_key] += 1
                                    fn_counter_dict[tag_fn_counter] += 1

                        
                        #### ucsf
                        if self.ucsf_format:
                            for i in range(0,len(ucsf_tags)):
                                tag = ucsf_tags[i]
                                fn_key = tag + '_fns'
                                tag_fn_counter = tag + '_fn_counter'
                                if (start_coordinate_fn in range(int(phi_start), int(phi_end))) and phi_type == tag:
                                    if tag != 'Age':
                                        rp_summaries[fn_key] += 1
                                        fn_counter_dict[tag_fn_counter] += 1


                        # Find PHI match: fn in text, coord in range
                        if start_coordinate_fn in range(int(phi_start), int(phi_end)):
                            # Get PHI tag
                            phi_tag = phi_type
                            # Get POS tag
                            pos_tag = cleaned_with_pos[str(start_coordinate_fn)][1]
                            
                            # Get 25 characters surrounding FN on either side
                            fn_context = ''
                            context_start = start_coordinate_fn - 25
                            context_end = start_coordinate_fn + len(false_negative) + 25
                            if context_start >= 0 and context_end <= len(text)-1:
                                fn_context = text[context_start:context_end]
                            elif context_start >= 0 and context_end > len(text)-1:
                                fn_context = text[context_start:]
                            else:
                                fn_context = text[:context_end]
                            # if fn == './data/i2b2_results/137-03.txt':
                            #     print(fn_context)                  
                            
                            # Get fn id, to distinguish betweem multiple entries
                            fn_id = "N" + str(counter)
                            
                            # Get include or exclude
                            if not self.ucsf_format:
                                if phi_tag in i2b2_include_tags:
                                    include_exclude_fns = 'include'
                                else:
                                    include_exclude_fns = 'exclude'
                            if self.ucsf_format:
                                if phi_tag in ucsf_include_tags:
                                    if phi_tag != 'Age':
                                        include_exclude_fns = 'include'
                                    # If age is over 90, include. Else, exclude
                                    else:
                                        fn_stripped = false_negative.replace('.','')
                                        # Is the age an integer?
                                        if fn_stripped.isdigit():
                                            if int(fn_stripped) >= 90:
                                                include_exclude_fns = 'include'
                                                corrected_age_fns += 1
                                                # print('Include (int): ',fn_stripped)
                                            else:
                                                include_exclude_fns = 'exclude'
                                        # Is the age a string?
                                        # Note that this won't catch all age FNs that are spelled ou
                                        # i.e., only the 'ninety' in 'ninety-five' will be marked as include
                                        # This won't affect our recall at all, but it will affect our precision a little
                                        # We will manually need to subtract theses from our FPs and add to our TPs 
                                        else:
                                            if 'ninety' in fn_stripped:
                                                include_exclude_fns = 'include'
                                                corrected_age_fns += 1
                                                # print('Include (str): ',fn_stripped)
                                            else:
                                                include_exclude_fns = 'exclude'
                                        # print(include_exclude_fns,fn_stripped)

                                else:
                                    include_exclude_fns = 'exclude'
                            ###### Create output dicitonary with id/word/pos/phi
                            #print(include_exclude_fns,false_negative)
                            fn_tag_summary[fn_id] = [false_negative, phi_tag, pos_tag, fn_context, include_exclude_fns, filter_file_list_exclude, filter_file_list_include]
                            # if phi_tag == 'AGE':
                            #     print(word)

            if fn_tag_summary != {}:
                fn_tags[fn] = fn_tag_summary


            ####### Get FP tags #########
            fp_tag_summary = {}
            include_exclude_fps = ''
            #print(cleaned_with_pos)
            current_fps = current_summary['false_positives'] + additional_fps
            if current_fps != [] and current_fps != [""]:              
                counter = 0
                #print(current_fps)
                for word in current_fps:
                    counter += 1
                    false_positive = word[0]
                    start_coordinate_fp = word[1]
                    # print(word)

                    # initialize list that will hold info on what matched what
                    filter_file_list_exclude = []
                    filter_file_list_include = []
                    
                    # if self.dependent:
                    # Loop through coorinate map objects and match patterns with FPs
                    for i,pattern in enumerate(self.patterns):
                        # print('\n',i, ':')

                        coord_map = pattern["coordinate_map"]
                        exclude_include = pattern["exclude"]
                        try:
                            filter_path = pattern["filepath"]
                        except KeyError:
                            filter_path = pattern["title"]
                        # print('\n')
                        # print(filter_path)
                        for start,stop in coord_map.filecoords(input_filename):
                            # print(start,stop,text[start:stop])
                            word_range = set(range(start_coordinate_fp, start_coordinate_fp + len(false_positive)))
                            filter_range = set(range(start, stop))
                            intersection = word_range & filter_range
                            if intersection != set():
                                # print("********"+str(start_coordinate_fp)+"********")
                                # print(false_positive)
                                # Add this filter path to the list of things that filtered this word
                                if exclude_include == True:
                                    filter_file_list_exclude.append(filter_path)
                                else:
                                    filter_file_list_include.append(filter_path)
                    # if self.dependent == False:
                    #     filter_file_list_exclude.append('')
                    #     filter_file_list_include.append('')
            
                    pos_entry = cleaned_with_pos[str(start_coordinate_fp)]

                    pos_tag = pos_entry[1]

                    # Get 25 characters surrounding FP on either side
                    fp_context = ''
                    context_start = start_coordinate_fp - 25
                    context_end = start_coordinate_fp + len(false_positive) + 25
                    if context_start >= 0 and context_end <= len(text)-1:
                        fp_context = text[context_start:context_end]
                    elif context_start >= 0 and context_end > len(text)-1:
                        fp_context = text[context_start:]
                    else:
                        fp_context = text[:context_end]


                    fp_id = "P" + str(counter)

                    
                    fp_tag_summary[fp_id] = [false_positive, pos_tag, fp_context, filter_file_list_exclude, filter_file_list_include]

            if fp_tag_summary != {}:
                fp_tags[fn] = fp_tag_summary

        # Create frequency table outputs
        if self.freq_table:
            # Unigram table
            with open('./data/phi/unigram_freq_table.csv','w') as f:
                f.write('unigram,phi_count,non-phi_count\n')
                for key in unigram_dict:
                    word = key
                    phi_count = unigram_dict[key][0]
                    non_phi_count = unigram_dict[key][1]
                    f.write(word + ',' + str(phi_count) + ',' + str(non_phi_count) + '\n')
            with open('./data/phi/bigram_freq_table.csv','w') as f:
                f.write('bigram,phi_count,non-phi_count\n')
                for key in bigram_dict:
                    term = key
                    phi_count = bigram_dict[key][0]
                    non_phi_count = bigram_dict[key][1]
                    f.write(term + ',' + str(phi_count) + ',' + str(non_phi_count) + '\n')

        # get specific recalls
        # i2b2
        overall_data = []
        if not self.ucsf_format:
            include_dict = {'fns':0,'tps':0,'fps':summary["total_false_positives"],'tns':summary["total_true_negatives"]}
            patient_phi_dict = {'fns':0,'tps':0,'fps':summary["total_false_positives"],'tns':summary["total_true_negatives"]}
            provider_phi_dict = {'fns':0,'tps':0,'fps':summary["total_false_positives"],'tns':summary["total_true_negatives"]}

            category_dict = {}
            for i in range(0,len(phi_categories)):
                category_tag = phi_categories[i]
                category_fns = category_tag + '_fns'
                category_tps = category_tag + '_tps'

                category_dict[category_fns] = 0
                category_dict[category_tps] = 0


            overall_recall_dict = {}

            for i in range(0,len(i2b2_tags)):
                tag = i2b2_tags[i]
                fn_key = tag + '_fns'
                tp_key = tag + '_tps'
                tag_fn_counter = tag + '_fn_counter'
                tag_cleaned_list = tag + '_cleaned'
                recall_key = tag + '_recall'


                # Get info for overall include dict and category dict
                if tag in i2b2_include_tags:
                    include_dict['fns'] += rp_summaries[fn_key]
                    include_dict['tps'] += rp_summaries[tp_key]

                    if tag in i2b2_patient_tags:
                        patient_phi_dict['fns'] += rp_summaries[fn_key]
                        patient_phi_dict['tps'] += rp_summaries[tp_key]
                    if tag in i2b2_provider_tags:
                        provider_phi_dict['fns'] += rp_summaries[fn_key]
                        provider_phi_dict['tps'] += rp_summaries[tp_key]

                    tag_category = i2b2_category_dict[tag]
                    category_fns = tag_category + '_fns'
                    category_tps = tag_category + '_tps'

                    category_dict[category_fns] += rp_summaries[fn_key]
                    category_dict[category_tps] += rp_summaries[tp_key]
                
                # Get additional TNs and FPs
                if tag not in i2b2_include_tags:
                    include_dict['tns'] += rp_summaries[fn_key]
                    include_dict['fps'] += rp_summaries[tp_key]

                    if tag in i2b2_patient_tags:
                        patient_phi_dict['tns'] += rp_summaries[fn_key]
                        patient_phi_dict['fps'] += rp_summaries[tp_key]   
                    if tag in i2b2_provider_tags:
                        provider_phi_dict['tns'] += rp_summaries[fn_key]
                        provider_phi_dict['fps'] += rp_summaries[tp_key]          


                if rp_summaries[fn_key] != 0:
                    # if rp_summaries[tp_key] != 0 and (rp_summaries[tp_key]-rp_summaries[fn_key]) > 0:
                    overall_recall_dict[recall_key] = rp_summaries[tp_key]/(rp_summaries[fn_key] + rp_summaries[tp_key])
                    # else:
                    #     overall_recall_dict[recall_key] = 0
                else:
                    overall_recall_dict[recall_key] = 1

                overall_data.append([tag,"{:.2%}".format(overall_recall_dict[recall_key]),str(rp_summaries[tp_key]),str(rp_summaries[fn_key])])
                # print(tag + " Recall: " + "{:.2%}".format(overall_recall_dict[recall_key]) + " TP: " + str(rp_summaries[tp_key]) + " FN: " + str(rp_summaries[fn_key]))

        # ucsf
        if self.ucsf_format:
            include_dict = {'fns':0,'tps':0,'fps':summary["total_false_positives"],'tns':summary["total_true_negatives"]}
            patient_phi_dict = {'fns':0,'tps':0,'fps':summary["total_false_positives"],'tns':summary["total_true_negatives"]}
            provider_phi_dict = {'fns':0,'tps':0,'fps':summary["total_false_positives"],'tns':summary["total_true_negatives"]}


            category_dict = {}
            for i in range(0,len(phi_categories)):
                category_tag = phi_categories[i]
                category_fns = category_tag + '_fns'
                category_tps = category_tag + '_tps'

                category_dict[category_fns] = 0
                category_dict[category_tps] = 0


            overall_recall_dict = {}

            for i in range(0,len(ucsf_tags)):
                tag = ucsf_tags[i]
                fn_key = tag + '_fns'
                tp_key = tag + '_tps'
                tag_fn_counter = tag + '_fn_counter'
                tag_cleaned_list = tag + '_cleaned'
                recall_key = tag + '_recall'


                # Get info for overall include dict and category dict
                if tag in ucsf_include_tags:
                    if tag != 'Age':
                        include_dict['fns'] += rp_summaries[fn_key]
                        include_dict['tps'] += rp_summaries[tp_key]

                        if tag in ucsf_patient_tags:
                            patient_phi_dict['fns'] += rp_summaries[fn_key]
                            patient_phi_dict['tps'] += rp_summaries[tp_key]
                        if tag in ucsf_provider_tags:
                            provider_phi_dict['fns'] += rp_summaries[fn_key]
                            provider_phi_dict['tps'] += rp_summaries[tp_key]

                        tag_category = ucsf_category_dict[tag]
                        category_fns = tag_category + '_fns'
                        category_tps = tag_category + '_tps'

                        category_dict[category_fns] += rp_summaries[fn_key]
                        category_dict[category_tps] += rp_summaries[tp_key]
                    else:
                        include_dict['fns'] += corrected_age_fns
                        include_dict['tps'] += rp_summaries[tp_key]
                        include_dict['tns'] += (rp_summaries[fn_key] - corrected_age_fns)

                        if tag in ucsf_patient_tags:
                            patient_phi_dict['fns'] += corrected_age_fns
                            patient_phi_dict['tps'] += rp_summaries[tp_key]
                            patient_phi_dict['tns'] += (rp_summaries[fn_key] - corrected_age_fns)
                        if tag in ucsf_provider_tags:
                            provider_phi_dict['fns'] += corrected_age_fns
                            provider_phi_dict['tps'] += rp_summaries[tp_key]
                            provider_phi_dict['tns'] += (rp_summaries[fn_key] - corrected_age_fns)

                        tag_category = ucsf_category_dict[tag]
                        category_fns = tag_category + '_fns'
                        category_tps = tag_category + '_tps'

                        category_dict[category_fns] += corrected_age_fns
                        category_dict[category_tps] += rp_summaries[tp_key]

                
                # Get additional TNs and FPs
                if tag not in ucsf_include_tags:
                    include_dict['tns'] += rp_summaries[fn_key]
                    include_dict['fps'] += rp_summaries[tp_key]
                
                    if tag in ucsf_patient_tags:
                        patient_phi_dict['tns'] += rp_summaries[fn_key]
                        patient_phi_dict['fps'] += rp_summaries[tp_key]   
                    if tag in ucsf_provider_tags:
                        provider_phi_dict['tns'] += rp_summaries[fn_key]
                        provider_phi_dict['fps'] += rp_summaries[tp_key]  


                if rp_summaries[fn_key] != 0:
                    # if rp_summaries[tp_key] != 0 and (rp_summaries[tp_key]-rp_summaries[fn_key]) > 0:
                    overall_recall_dict[recall_key] = rp_summaries[tp_key]/(rp_summaries[fn_key] + rp_summaries[tp_key])
                    # else:
                    #     overall_recall_dict[recall_key] = 0
                else:
                    overall_recall_dict[recall_key] = 1
                if tag == 'Age':
                    overall_data.append([tag,"{:.2%}".format(overall_recall_dict[recall_key]),str(rp_summaries[tp_key]),str(corrected_age_fns)])
                # print(tag + " Recall: " + "{:.2%}".format(overall_recall_dict[recall_key]) + " TP: " + str(rp_summaries[tp_key]) + " FN: " + str(rp_summaries[fn_key]))
                else:
                    overall_data.append([tag,"{:.2%}".format(overall_recall_dict[recall_key]),str(rp_summaries[tp_key]),str(rp_summaries[fn_key])])
                # print(tag + " Recall: " + "{:.2%}".format(overall_recall_dict[recall_key]) + " TP: " + str(rp_summaries[tp_key]) + " FN: " + str(rp_summaries[fn_key]))
        
        # pretty print tag recalls
        overall_data.sort(key=lambda x: float(x[1][:-1]),reverse=True)
        sorted_overall_data = [["Tag","Recall","TPs","FNs"]]
        for item in overall_data:
            sorted_overall_data.append(item)

        if self.verbose:
            print('\n')
            print("Recall by Tag:")
            col_width = max(len(word) for row in sorted_overall_data for word in row) + 2  # padding
            for row in sorted_overall_data:
                print("".join(word.ljust(col_width) for word in row))



        # Get category recall
        category_data = []
        for i in range(0,len(phi_categories)):
            category_tag = phi_categories[i]
            category_fns = category_tag + '_fns'
            category_tps = category_tag + '_tps'

            category_recall = 0
            if category_dict[category_fns] != 0:
                # if category_dict[category_tps]!= 0 and (category_dict[category_tps]-category_dict[category_fns]) > 0:
                category_recall = category_dict[category_tps]/(category_dict[category_fns] + category_dict[category_tps])
                # else:
                #     category_recall = 0
            else:
                category_recall = 1
            category_data.append([category_tag,"{:.2%}".format(category_recall),str(category_dict[category_tps]),str(category_dict[category_fns])])
            # print(category_tag + " Recall: " + "{:.2%}".format(category_recall) + " TP: " + str(category_dict[category_tps]) + " FN: " + str(category_dict[category_fns]))                 

        # pretty print category recalls
        category_data.sort(key=lambda x: float(x[1][:-1]),reverse=True)
        sorted_category_data = [["Category","Recall","TPs","FNs"]]
        for item in category_data:
            sorted_category_data.append(item)
        if self.verbose:
            print('\n')
            print('Recall by PHI Category:')
            col_width = max(len(word) for row in category_data for word in row) + 2  # padding
            for row in sorted_category_data:
                print("".join(word.ljust(col_width) for word in row))
        




        ######### Get corrected recall, precision ##########


        corrected_recall = 0
        if include_dict['fns'] != 0:
            # if include_dict['tps'] != 0 and (include_dict['tps']-include_dict['fns']) > 0:
            corrected_recall = include_dict['tps']/(include_dict['fns'] + include_dict['tps'])
            # else:
            #     corrected_recall = 0
        else:
            corrected_recall = 1

        corrected_precision = 0
        if include_dict['fps'] != 0:
            # if include_dict['tps'] != 0 and (include_dict['tps']-include_dict['fns']) > 0:
            corrected_precision = include_dict['tps']/(include_dict['fps'] + include_dict['tps'])
            # else:
            #     corrected_recall = 0
        else:
            corrected_precision = 1

        specificity = 0
        if include_dict['fps'] != 0:
            # if include_dict['tps'] != 0 and (include_dict['tps']-include_dict['fns']) > 0:
            specificity = include_dict['tns']/(include_dict['fps'] + include_dict['tns'])
            # else:
            #     corrected_recall = 0
        else:
            specificity = 1

        print('\n')
        print("Corrected Results:")
        print('\n')
        print("cTP:",include_dict['tps'], "cFN:", include_dict['fns'], "cTN:", include_dict['tns'], "cFP:", include_dict['fps'])
        print("Corrected Recall: " + "{:.2%}".format(corrected_recall))
        print("Corrected Precision: " + "{:.2%}".format(corrected_precision))
        print("Corrected Retention: " + "{:.2%}".format(specificity))
        print('\n')


        ######### Patient-only recall, precision ##########


        patient_recall = 0
        if patient_phi_dict['fns'] != 0:
            # if include_dict['tps'] != 0 and (include_dict['tps']-include_dict['fns']) > 0:
            patient_recall = patient_phi_dict['tps']/(patient_phi_dict['fns'] + patient_phi_dict['tps'])
            # else:
            #     corrected_recall = 0
        else:
            patient_recall = 1

        patient_precision = 0
        if patient_phi_dict['fps'] != 0:
            # if include_dict['tps'] != 0 and (include_dict['tps']-include_dict['fns']) > 0:
            patient_precision = patient_phi_dict['tps']/(patient_phi_dict['fps'] + patient_phi_dict['tps'])
            # else:
            #     corrected_recall = 0
        else:
            patient_precision = 1

        patient_specificity = 0
        if patient_phi_dict['fps'] != 0:
            # if include_dict['tps'] != 0 and (include_dict['tps']-include_dict['fns']) > 0:
            patient_specificity = patient_phi_dict['tns']/(patient_phi_dict['fps'] + patient_phi_dict['tns'])
            # else:
            #     corrected_recall = 0
        else:
            patient_specificity = 1

        print('\n')
        print("Patient-Only Results:")
        print('\n')
        print("cTP:",patient_phi_dict['tps'], "cFN:", patient_phi_dict['fns'], "cTN:", patient_phi_dict['tns'], "cFP:", patient_phi_dict['fps'])
        print("Patient PHI Recall: " + "{:.2%}".format(patient_recall))
        print("Precision: " + "{:.2%}".format(patient_precision))
        print("Retention: " + "{:.2%}".format(patient_specificity))
        print('\n')



       ######### Provider-only recall, precision ##########


        provider_recall = 0
        if provider_phi_dict['fns'] != 0:
            # if include_dict['tps'] != 0 and (include_dict['tps']-include_dict['fns']) > 0:
            provider_recall = provider_phi_dict['tps']/(provider_phi_dict['fns'] + provider_phi_dict['tps'])
            # else:
            #     corrected_recall = 0
        else:
            patient_recall = 1

        provider_precision = 0
        if provider_phi_dict['fps'] != 0:
            # if include_dict['tps'] != 0 and (include_dict['tps']-include_dict['fns']) > 0:
            provider_precision = provider_phi_dict['tps']/(provider_phi_dict['fps'] + provider_phi_dict['tps'])
            # else:
            #     corrected_recall = 0
        else:
            patient_precision = 1

        provider_specificity = 0
        if provider_phi_dict['fps'] != 0:
            # if include_dict['tps'] != 0 and (include_dict['tps']-include_dict['fns']) > 0:
            provider_specificity = provider_phi_dict['tns']/(provider_phi_dict['fps'] + provider_phi_dict['tns'])
            # else:
            #     corrected_recall = 0
        else:
            provider_specificity = 1

        print('\n')
        print("Provider-Only Results:")
        print('\n')
        print("cTP:",provider_phi_dict['tps'], "cFN:", provider_phi_dict['fns'], "cTN:", provider_phi_dict['tns'], "cFP:", provider_phi_dict['fps'])
        print("Provider PHI Recall: " + "{:.2%}".format(provider_recall))
        print("Precision: " + "{:.2%}".format(provider_precision))
        print("Retention: " + "{:.2%}".format(provider_specificity))
        print('\n')



        ######## Summarize FN results #########
        
        ##### With and without context #####
        
        # With context:
        # Condensed tags will contain id, word, PHI tag, POS tag, occurrences
        fn_tags_condensed_context = {}
        # Stores lists that represent distinct groups of words, PHI and POS tags
        fn_tags_condensed_list_context = []
        
        # No context:
        # Condensed tags will contain id, word, PHI tag, POS tag, occurrences
        fn_tags_condensed = {}
        # Stores lists that represent distinct groups of words, PHI and POS tags
        fn_tags_condensed_list = []

        # Keep track of how many distinct combinations we've added to each list
        context_counter = 0
        nocontext_counter = 0
        for fn in fn_tags:
            file_dict = fn_tags[fn] 
            for subfile in file_dict:
                current_list_context = file_dict[subfile]
            ##############################
                # print(current_list_context)
                current_list_nocontext = current_list_context[:3] + [current_list_context[-3]] + [current_list_context[-2]] + [current_list_context[-1]]
            ############################
                
                word = current_list_context[0]
                phi_tag = current_list_context[1]
                pos_tag = current_list_context[2]
                fn_context = current_list_context[3].replace("\n"," ")
                filter_matches_exclude = current_list_context[5]
                filter_matches_include = current_list_context[6]
                
                # Context: add each occurrence with corresponding filename                    
                fn_tags_condensed_list_context.append(current_list_context)
                key_name = "uniq" + str(context_counter)
                filename = fn.split('/')[-1]
                include_exclude = current_list_context[4]
                fn_tags_condensed_context[key_name] = [word, phi_tag, pos_tag, fn_context, filename, include_exclude, filter_matches_exclude, filter_matches_include]
                context_counter += 1

                # No context
                if current_list_nocontext not in fn_tags_condensed_list:   
                    fn_tags_condensed_list.append(current_list_nocontext)
                    key_name = "uniq" + str(nocontext_counter)
                    fn_tags_condensed[key_name] = [word, phi_tag, pos_tag, 1, include_exclude, filter_matches_exclude, filter_matches_include]
                    nocontext_counter += 1
                else: 
                    uniq_id_index = fn_tags_condensed_list.index(current_list_nocontext)
                    uniq_id = "uniq" + str(uniq_id_index)
                    fn_tags_condensed[uniq_id][3] += 1

        ####### Summariz FP results #######

        # With context
        # Condensed tags will contain id, word, POS tag, occurrences
        fp_tags_condensed_context = {}
        # Stores lists that represent distinct groups of wordss and POS tags
        fp_tags_condensed_list_context = []

        # No context
        # Condensed tags will contain id, word, POS tag, occurrences
        fp_tags_condensed = {}
        # Stores lists that represent distinct groups of wordss and POS tags
        fp_tags_condensed_list = []

        # Keep track of how many distinct combinations we've added to each list
        nocontext_counter = 0
        context_counter = 0
        for fp in fp_tags:
            file_dict = fp_tags[fp]
            for subfile in file_dict:
                current_list_context = file_dict[subfile]
                current_list_nocontext = current_list_context[:2] + [current_list_context[3]] + [current_list_context[4]]

                word = current_list_context[0]
                pos_tag = current_list_context[1]
                fp_context = current_list_context[2].replace("\n"," ")
                filter_matches_exclude = current_list_context[3]
                filter_matches_include = current_list_context[4]

                # Context: add each occurrence with corresponding filename
                fp_tags_condensed_list_context.append(current_list_context)
                key_name = "uniq" + str(context_counter)
                filename = fp.split('/')[-1]
                fp_tags_condensed_context[key_name] = [word, pos_tag, fp_context, filename, filter_matches_exclude, filter_matches_include]
                context_counter += 1

                # No Context
                if current_list_nocontext not in fp_tags_condensed_list:
                    fp_tags_condensed_list.append(current_list_nocontext)
                    key_name = "uniq" + str(nocontext_counter)
                    fp_tags_condensed[key_name] = [word, pos_tag, 1, filter_matches_exclude, filter_matches_include]
                    nocontext_counter += 1
                else:
                    uniq_id_index = fp_tags_condensed_list.index(current_list_nocontext)
                    uniq_id = "uniq" + str(uniq_id_index)
                    fp_tags_condensed[uniq_id][2] += 1


        # Write FN and FP results to outfolder
        # Conext
        with open( os.path.join( self.eval_outpath , "fn_tags_context.txt" ) , "w") as fn_file:
            fn_file.write("key" + "|" + "note_word" + "|" + "phi_tag" + "|" + "pos_tag" + "|" + "context" + "|" + "filename"+ "|" +"include_exclude" + "|" +"exclude_filters" + "|" +"include_filters" +"\n")
            # print(fn_tags_condensed_context)
            for key in fn_tags_condensed_context:
                current_list = fn_tags_condensed_context[key]
                fn_file.write(key + "|" + current_list[0] + "|" + current_list[1] + "|" + current_list[2] + "|" + current_list[3] + "|" + current_list[4]+ "|" +current_list[5]+ "|" +str(current_list[6]) + "|" +str(current_list[7]) + "\n")
        
        with open( os.path.join( self.eval_outpath , "fp_tags_context.txt" ) , "w") as fp_file:
            fp_file.write("key" + "|" + "note_word" + "|" + "pos_tag" + "|" + "context" + "|" + "filename"+ "|" +"exclude_filters" + "|" +"include_filters" +"\n")
            for key in fp_tags_condensed_context:
                current_list = fp_tags_condensed_context[key]
                fp_file.write(key + "|" + current_list[0] + "|" + current_list[1]  + "|" +  current_list[2] + "|" + current_list[3]+ "|" + str(current_list[4]) + "|" + str(current_list[5]) +"\n")

        # No context
        with open( os.path.join( self.eval_outpath , "fn_tags.txt" ) , "w") as fn_file:
            fn_file.write("key" + "|" + "note_word" + "|" + "phi_tag" + "|" + "pos_tag" + "|" + "occurrences"+"|" +"include_exclude" + "|" +"exclude_filters" + "|" +"include_filters" + "\n")
            for key in fn_tags_condensed:
                current_list = fn_tags_condensed[key]
                fn_file.write(key + "|" + current_list[0] + "|" + current_list[1] + "|" + current_list[2] + "|" + str(current_list[3])+"|" + current_list[4]+ "|" + str(current_list[5])+ "|" + str(current_list[6])+"\n")
        
        with open( os.path.join( self.eval_outpath , "fp_tags.txt" ) , "w") as fp_file:
            fp_file.write("key" + "|" + "note_word" + "|" + "pos_tag" + "|" + "occurrences"+ "|" +"exclude_filters" + "|" +"include_filters" + "\n")
            for key in fp_tags_condensed:
                current_list = fp_tags_condensed[key]
                fp_file.write(key + "|" + current_list[0] + "|" + current_list[1]  + "|" +  str(current_list[2])+ "|" + str(current_list[3]) + "|" + str(current_list[4]) +"\n")            
            
    
    def getphi(self, 
            anno_folder="data/i2b2_anno/", 
            anno_suffix="_phi_reduced.ano", 
            data_folder="data/i2b2_notes/", 
            output_folder="i2b2_phi", 
            filter_regex=None):
        """ get's phi from existing data to build up a data model
        data structure to hold our phi and classify phi we find
            {
                "foo.txt":[
                    {
                        "phi":"1/1/2019",
                        "context":"The data was 1/1/2019 and the patient was happy",
                        "class":"numer" //number, string ... 
                    },...
                ],...
            }
        """
        if self.run_eval:
            print("getphi")


        #use config if exists
        if self.anno_folder != None:
            anno_folder = self.anno_folder

        if self.anno_suffix != "":
            anno_suffix = self.anno_suffix

        phi = {}
        word_counts = {}
        not_phi = {}
        window_size = 10 #amount of words surrounding word to grab

        for root, dirs, files in os.walk(data_folder):
           
            for f in files:
               
                if not os.path.exists( os.path.join( root , f ) ):
                    raise Exception("FILE DOESNT EXIST", os.path.join( root , f ) )

                if len(anno_suffix) > 0:
                    if not os.path.exists( os.path.join( anno_folder , f.split(".")[0]+anno_suffix ) ):
                        print("FILE DOESNT EXIST", os.path.join( anno_folder , f.split(".")[0]+anno_suffix ) )
                        continue
                else:
                    if not os.path.exists( os.path.join( anno_folder , f ) ):
                        print("FILE DOESNT EXIST", os.path.join( anno_folder , f ) )
                        continue

                orig_filename = os.path.join( root , f )
                encoding1 = self.detect_encoding(orig_filename)
                orig = open(orig_filename,"r", encoding=encoding1['encoding']).read()

                orig_words = re.split("\s+", orig)

                anno_filename = os.path.join( anno_folder , f.split(".")[0]+anno_suffix )
                encoding2 = self.detect_encoding(anno_filename)
                anno = open(anno_filename,"r", encoding=encoding2['encoding']).read()
                anno_words = re.split("\s+", anno)

                anno_dict = {}
                orig_dict = {}

                for w in anno_words:
                    anno_dict[w] = 1

                for i,w in enumerate(orig_words):

                    #check for edge cases that should not be "words"
                    x = w.replace("_","").strip()
                    if len(x) == 0:
                        continue

                    #add all words to our counts
                    if w not in word_counts:
                        word_counts[w] = 0
                    word_counts[w] += 1

                    #check if this word is phi
                    if w not in anno_dict:

                        left_index = i - 10
                        if left_index < 0:
                            left_index = 0

                        right_index = i + 10
                        if right_index >= len(orig_words):
                            right_index = len(orig_words) - 1
                        window = orig_words[left_index:right_index]
                        if f not in phi:
                            phi[f] = []

                        c = "string"
                        if re.search("\d+", w):
                            c = "number"

                        phi[f].append({"phi":w,"context":window,"class":c})
                    else:
                        #add all words to our counts
                        if w not in not_phi:
                            not_phi[w] = 0
                        not_phi[w] += 1

        #save our phi with context
        json.dump(phi, open("data/phi/phi_context.json", "w"), indent=4)

        #save all phi word counts
        counts = {}
        num_phi = {}
        string_phi = {}
        
        for f in phi:
            for d in phi[f]:
                if d["phi"] not in counts:
                    counts[d["phi"]] = 0
                counts[d["phi"]] += 1
                if d["class"] == "number":
                    if d["phi"] not in num_phi:
                        num_phi[d["phi"]] = 0
                    num_phi[d["phi"]] += 1
                else:
                    if d["phi"] not in string_phi:
                        string_phi[d["phi"]] = 0
                    string_phi[d["phi"]] += 1

        #save all phi counts
        json.dump(counts, open("data/phi/phi_counts.json", "w"), indent=4)
        #save phi number counts
        json.dump(num_phi, open("data/phi/phi_number_counts.json", "w"), indent=4)
        #save phi string counts
        json.dump(string_phi, open("data/phi/phi_string_counts.json", "w"), indent=4)
        #save our total word counts
        json.dump(word_counts, open("data/phi/word_counts.json", "w"), indent=4)
        #save our total non_phi counts
        json.dump(not_phi, open("data/phi/non_phi_counts.json", "w"), indent=4)
        
        #get all non_phi counts by number or string
        non_phi_number = {}
        non_phi_string = {}
        for w in word_counts:
            if re.search("\d+", w):
                if w not in non_phi_number:
                    non_phi_number[w] = 0
                non_phi_number[w] += 1
            else:
                if w not in non_phi_string:
                    non_phi_string[w] = 0
                non_phi_string[w] += 1

        #save all phi string counts
        json.dump(non_phi_number, open("data/phi/non_phi_number_counts.json", "w"), indent=4)

        #save all phi number counts
        json.dump(non_phi_string, open("data/phi/non_phi_string_counts.json", "w"), indent=4)


    def mapphi(self, 
            phi_path="data/phi/phi_counts.json", 
            out_path="data/phi/phi_map.json",
            sorted_path="data/phi/phi_sorted.json",  
            digit_char="`", 
            string_char="?"):
        """ given all examples of the phi, creates a general representation 
            
            digit_char = this is what digits are replaced by
            string_char = this is what strings are replaced by
            any_char = this is what any random characters are replaced with
        """
        if self.run_eval:
            print("mapphi")

        d = json.load(open(phi_path, "r"))

        phi_map = {}

        for phi in d:
            wordlst = []
            phi_word = phi["phi"]
            for c in phi_word:
                if re.match("\d+", c):
                    wordlst.append(digit_char)
                elif re.match("[a-zA-Z]+", c):
                    wordlst.append(string_char)
                else:
                    wordlst.append(c)
            word = "".join(wordlst)
            if word not in phi_map:
                phi_map[word] = {'examples':{}}
            if phi_word not in phi_map[word]['examples']:
                phi_map[word]['examples'][phi_word] = []
            phi_map[word]['examples'][phi_word].append(phi) 

        #save the count of all representations
        for k in phi_map:
            phi_map[k]["count"] = len(phi_map[k]["examples"].keys())

        #save all representations
        json.dump(phi_map, open(out_path, "w"), indent=4)

        #save an ordered list of representations so we can prioritize regex building
        items = []
        for k in phi_map:
            items.append({"pattern":k, "examples":phi_map[k]["examples"], "count":len(phi_map[k]["examples"].keys())})

        items.sort(key=lambda x: x["count"], reverse=True)
        json.dump(items, open(sorted_path, "w"), indent=4)


