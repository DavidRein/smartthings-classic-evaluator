import os
import glob
import re
import csv
import json
import yaml


#ensures that a file is deleted from directory
def clean(filename):
    if os.path.exists(filename):
        os.remove(filename)


#writes iterable output to .csv with specified filename
def write_to_csv(output, filename):
    clean(filename + ".csv")
    with open(filename + '.csv', 'w', newline='') as csvfile:
        for entry in output:
            csvwriter = csv.writer(csvfile, delimiter=',')
            csvwriter.writerow(entry)


#writes dictionary output to .json wit specified filename
def write_to_json(output_data, filename):
    clean(filename + ".json")
    with open(filename + '.json', 'w') as jsonfile:
        json.dump(output_data, jsonfile, indent=2)


#gets list of all files with a desired extension
def get_files(path, filetype):
    return glob.glob(path + "/**/*." + filetype, recursive=True)


#returns a file name from a filepath
def strip_to_filename(filepath, filetype):
    _ , filename = os.path.split(filepath)
    trim_length = len(filetype) + 1
    filename = filename[:-trim_length]
    return filename


#function grabbed from https://www.geeksforgeeks.org/camel-case-given-sentence/
# needed to standardize capability names from different sources for ease in searching dictionaries
def convert_to_camelcase(s):
    if(len(s) == 0):
        return
    s1 = ''
    s1 += s[0].upper()
    for i in range(1, len(s)):
        if (s[i] == ' '):
            s1 += s[i + 1].upper()
            i += 1
        elif(s[i - 1] != ' '):
            s1 += s[i]
    return s1


#creates a dictionary of devicehandlers and their capabilities, commands, and attributes,
# extracted from downloaded smartthings github repository
def extract_devicehandler_info(writeToCSV=False, writeToJSON=False):
    output_capabilities = []
    output_commands = []
    output_attributes = []
    data = {"devicehandlers": []}

    files = get_files("./SmartThingsPublic-master/devicetypes", "groovy")

    #for all devicehandler src files
    for f in files:
        filename = strip_to_filename(f, "groovy")

        capabilities = [filename]
        commands = [filename]
        attributes = [filename]

        #search file for keywords. On hits, add results to entry lists
        with open(f, "rt", encoding='utf-8') as myfile:
            for myline in myfile:
                if "capability \"" in myline:
                    capability = re.search("\"(.*?)\"", myline).group(1)
                    if not capability in capabilities:
                        capabilities.append(convert_to_camelcase(capability))
                elif "command \"" in myline:
                    command = re.search("\"(.*?)\"", myline).group(1)
                    if not command in commands:
                        commands.append(command)
                elif "attribute \"" in myline:
                    attribute = re.search("\"(.*?)\"", myline).group(1)
                    if not attribute in attributes:
                        attributes.append(command)
        
        #update output lists
        output_capabilities.append(capabilities)
        output_commands.append(commands)
        output_attributes.append(attributes)

        #update output dictionary
        data["devicehandlers"].append(  { filename: {"capabilities" : capabilities[1:],
                "loose_commands" : commands[1:], 
                "loose_attributes" : attributes[1:]} }  )

    #optional write results to files
    if writeToCSV == True:
        write_to_csv(output_capabilities, "devicehandler_capabilities")
        write_to_csv(output_commands, "devicehandler_loose_commands")
        write_to_csv(output_attributes, "devicehandler_loose_attributes")
    if writeToJSON == True:
        write_to_json(data, "devicehandlers")

    #return dictionary
    return data


#creates a dictionary of smartapps and their capabilities, 
# extracted from downloaded smartthings github repo
def extract_smartapp_info(capabilitiies_dict, writeToCSV=False, writeToJSON=False):
    output = []
    data = {"smartapps": []}
    files = get_files("./SmartThingsPublic-master/smartapps", "groovy")

    #for all smartapp src (.groovy) files
    for f in files:
        filename = strip_to_filename(f, "groovy")
        entry = [filename]

        #scan file line-by-line for 'capability' keyword, pull capability names
        with open(f, "rt", encoding='utf-8') as myfile:
            for myline in myfile:
                if "\"capability." in myline:
                    capability = re.search("\"capability.(.*?)\"", myline).group(1).lower()
                    if not capability in entry:
                        entry.append(capability)

        #add results to output list
        output.append(entry)

        #create entry dict
        sad = {"capabilities" : entry[1:], "available_commands": [], "available_attributes": []}
        #get commands and attributes of requested capabilities and add them to the entry dict
        for c in entry[1:]:
            temp = get_capability_info(c, capabilities_dict)
            for key in temp:
                sad[key] += temp[key]
        #add smartapp entry to data store in JSON format
        data["smartapps"].append(  { filename: sad }  )

    #optional write results to files
    if writeToCSV == True:
        write_to_csv(output, "smartapp_capabilities")
    if writeToJSON == True:
        write_to_json(data, "smartapps")
    
    #return dictionary
    return data


#creates a dictionary of capabilities and their associated commands and attributes, 
# extracted from smartthings classic capability reference
def extract_capabilities_info(writeToCSV=False, writeToJSON=False):
    output_commands = []
    output_attributes = []
    data = {"capabilities": []}

    files = get_files("./SmartThingsClassic-capabilities", "yaml")

    #for all capability yaml files
    for f in files:
        commands = []
        attributes = []
        #open the file and extract the capability name and associated commands and attributes
        with open(f, "rt", encoding='utf-8') as myfile:
            capdict = yaml.full_load(myfile)
            if 'name' in capdict:
                commands.append(convert_to_camelcase(capdict['name']).lower())
                attributes.append(convert_to_camelcase(capdict['name']).lower())
            commands += list(capdict['commands'].keys())
            attributes += list(capdict['attributes'].keys())

        #store the results to output lists and dictionary
        output_commands.append(commands)
        output_attributes.append(attributes)
        data["capabilities"].append(  { commands[0]: {"commands" : commands[1:], 
                "attributes" : attributes[1:]} }  )

    #optional write results to files
    if writeToCSV == True:
        write_to_csv(output_commands, "capability_commands")
        write_to_csv(output_attributes, "capability_attributes")
    if writeToJSON == True:
        write_to_json(data, "capabilities.csv")

    #return dictionary
    return data    


#returns a dictionary containing 'available_commands' and 'avaialble_attributes' 
# of the specified capability
def get_capability_info(capability, capabilities_dict):
    #for each capability entry
    for capdict in capabilities_dict["capabilities"]:
        #find entry to target capability
        if(capability in capdict.keys()):
            #create and return the dictionary entry for the target entry
            cd = {}
            cd["available_commands"] = capdict[capability]["commands"]
            cd["available_attributes"] = capdict[capability]["attributes"]
            return cd

    #if target capability not found, return empty dictionary
    return {}


#gets count of smartapp requests for each capability, returns the list of counts
def get_capabilities_requested_count(capabilities_dict, smartapp_dict, writeToCSV=False, writeToJSON=False):
    output = [['Capability','SmartApp Request Count']]

    #for each capability entry
    for cap_dict in capabilities_dict["capabilities"]:
        for capability in cap_dict:
            request_count = 0
            #for each smartapp entry
            for sad in smartapp_dict["smartapps"]:
                for smartapp in sad:
                    #if smartapp requests the current capability, increment count
                    if capability in sad[smartapp]["capabilities"]:
                        request_count += 1
            #add capability and count to output list and dictionary
            output.append([capability, request_count])
            cap_dict[capability]["smartapp_request_count"] = request_count

    #optional write results to files
    if writeToCSV == True:
        write_to_csv(output, "capabilities_request_count")
    if writeToJSON == True:
        write_to_json(capabilities_dict, "capabilities")
    
    return output


#gets count of capabilities, commands, and attributes for each smartapp, returns the list of counts
def get_smartapp_access_count(smartapp_dict, writeToCSV=False, writeToJSON=False):
    output = [['SmartApp', 'Capability Count', 'Available Commands Count', 'Available Attributes Count']]

    #for each smartapp entry
    for sad in smartapp_dict["smartapps"]:
        for smartapp in sad:
            #create list entry with counts for each element in the dictionary
            output.append([smartapp, len(sad[smartapp]["capabilities"]), 
                    len(sad[smartapp]["available_commands"]), len(sad[smartapp]["available_attributes"])])
            #add counts to dictionary
            sad_keys = list(sad[smartapp])
            for key in sad_keys:
                sad[smartapp][key + "_count"] = len(sad[smartapp][key])

    #optional write results to files
    if writeToCSV == True:
        write_to_csv(output, "smartapp_access_count")
    if writeToJSON == True:
        write_to_json(smartapp_dict, "smartapps")
    
    #return list of smartapp access counts
    return output


if __name__ == "__main__":
    #initial pulls of information from 'external' sources (i.e. downloaded repo, source files, etc.)
    capabilities_dict = extract_capabilities_info()
    smartapp_dict = extract_smartapp_info(capabilities_dict)
    extract_devicehandler_info()

    #calculate metrics from existing information
    get_capabilities_requested_count(capabilities_dict, smartapp_dict, writeToCSV=True)
    get_smartapp_access_count(smartapp_dict, writeToCSV=True, writeToJSON=True)