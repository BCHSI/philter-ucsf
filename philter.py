class Philter:
    """ 
        General text filtering class,
        can filter using whitelists, blacklists, regex's and POS
    """

    def __init__(self) : 

        self.root = "/Users/MarkKrass/Dropbox (Stanford Law School)/pile/philter/"
        self.patterns = json.loads(open(root + "configs/philter_delta_phi_tags.json", "r").read())
        self.coordinate_maps = []
        self.pos_tags = {}
        self.cleaned = {}

        #create a memory for FULL exclude coordinate map (including non-whitelisted words)
        self.full_exclude_map = {}
        self.phi_type_list = ['DATE','Patient_Social_Security_Number','Email','Provider_Address_or_Location','Age','Name','OTHER','ID','NAME','LOCATION','CONTACT','AGE']
        self.data_all_files = {}
        self.pattern_indexes = {}
        self.patterns_out = {}
        self.doc_result_dict = {}
        # init patterns
        self.init_patterns(self.patterns)

    def init_patterns(self, patterns, root = "/Users/MarkKrass/Dropbox (Stanford Law School)/pile/philter/"):
        """ given our input pattern config will load our sets and pre-compile our regex"""

        known_pattern_types = set(["regex", "set", "regex_context","stanford_ner", "pos_matcher", "match_all"])
        require_files = set(["regex", "set"])
        require_pos = set(["pos_matcher"])
        set_filetypes = set(["pkl", "json"])
        regex_filetypes = set(["txt"])
        reserved_list = set(["data", "coordinate_map"])

        # add root to all filepaths
        for i,p in enumerate(patterns):
            if "filepath" in p:
                patterns[i]['filepath'] = root + patterns[i]['filepath']

        #first check that data is formatted, can be loaded etc. 
        for i,pattern in enumerate(patterns):
            self.patterns_out[i] = {'title':pattern['title']}
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
                self.patterns_out[i]["data"] = init_set(pattern["filepath"])  
            if pattern["type"] == "regex":
                if pattern["filepath"].split(".")[-1] not in regex_filetypes:
                    raise Exception("Invalid filteype", pattern["filepath"], "must be of", regex_filetypes)
                self.patterns_out[i]["data"] = precompile(pattern["filepath"])
            elif pattern["type"] == "regex_context":
                if pattern["filepath"].split(".")[-1] not in regex_filetypes:
                    raise Exception("Invalid filteype", pattern["filepath"], "must be of", regex_filetypes)
                self.patterns_out[i]["data"] = precompile(pattern["filepath"])
                #print(self.precompile(pattern["filepath"]))
        return self.patterns_out

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
    
    def get_pos(self, filename, cleaned):
        self.pos_tags = {}
        self.pos_tags[filename] = nltk.pos_tag(cleaned)
        return self.pos_tags[filename]


    def get_clean(self, st, pre_process= r"[^a-zA-Z0-9]"):
        # Use pre-process to split sentence by spaces AND symbols, while preserving spaces in the split list
        lst = re.split("(\s+)", st)
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
        return cleaned
  
    
    def count_hits_by_string(self, string_inputs):
        """ Runs the set, or regex on an iterable containing strings.
            This is an alternative to the map_coordinates 
        """

        docid=0
        for s in string_inputs:
            s = self.get_clean(s)
            s = "".join(s)
            # Get full self.include/exclude map before transform
            self.data_all_files[docid] = {"phi_types":{}}

            #### Create inital self.exclude/include for file

            for i,pat in enumerate(self.patterns):
                if pat["type"] == "regex":
                    self.data_all_files[docid]['phi_types'][pat['title']] = self.count_regex_hits(filename=str(docid), 
                                                                                                      text=s, 
                                                                                                      pattern_index=i)
                elif pat["type"] == "set":
                     self.data_all_files[docid]['phi_types'][pat['title']] = self.map_set(filename=str(docid), 
                                                                                          text=s, 
                                                                                          pattern_index=i)
            docid += 1
            
        return self.data_all_files

    def count_regex_hits(self, filename="", text="", pattern_index=-1, pre_process= r"[^a-zA-Z0-9]"):
        """ count regex hits for a given regex type
        """
        
        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(patterns))
        regex = self.patterns_out[pattern_index]["data"]

        # All regexes except matchall
        matches = regex.finditer(text)
        return len([i for i in matches])
    
    def map_set(self, filename="", text="", pattern_index=-1,  pre_process= r"[^a-zA-Z0-9]"):
        """ Creates a coordinate mapping of words any words in this set"""

        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(patterns))

        map_set = self.patterns_out[pattern_index]["data"]

        #get part of speech we will be sending through this set
        #note, if this is empty we will put all parts of speech through the set
        check_pos = False
        pos_set = set([])
        if "pos" in self.patterns[pattern_index]:
            pos_set = set(self.patterns[pattern_index]["pos"])
        if len(pos_set) > 0:
            check_pos = True

        cleaned = self.get_clean(text)
        if check_pos:
            pos_list = nltk.pos_tag(cleaned)
        else:
            pos_list = zip(cleaned,range(len(cleaned)))

        pos_list = nltk.pos_tag(cleaned)
        out = []
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
                    out.extend((start, stop))
                    #print("FOUND: ",word, "COORD: ",  text[start:stop])
                else:
                    #print("not in set: ",word, "COORD: ",  text[start:stop])
                    #print(word_clean)
                    pass
                    
            #advance our start coordinate
            start_coordinate += len(word)
        return len([i for i in out])


