import xml.etree.ElementTree as ET
import argparse
import xmltodict
import os
import re
import sys

# This script removes PHI tags that are not PHI (according to HIPAA) from i2b2 annotations

def extractXML(directory,filename):
	tree = ET.parse(directory + '/'+ filename)
	root = tree.getroot()
	xmlstr = ET.tostring(root, encoding='utf8', method='xml')

	xml_dict = xmltodict.parse(xmlstr,dict_constructor=dict)["deIdi2b2"]
	text = xml_dict["TEXT"]
	tags_dict = xml_dict["TAGS"]

	return text,tags_dict,xmlstr

def delete_annotation(xml_file, phi_type, tag_to_delete):
	
	if sys.version_info < (3, 0):
		remove_line_if = bytes('text="' + tag_to_delete + '"')
	else:
		remove_line_if = bytes('text="' + tag_to_delete + '"', 'utf-8')
	
	for line in xml_file.split(b"\n"):
		if remove_line_if in line:
			remove_line = line + b"\n"
			xml_file = xml_file.replace(remove_line,b"")
	
	return xml_file

def fix_dates(xml_file,text):

	# Remove years in isolation
	PHI_type="DATE"
	date = text
	if date.isdigit():
		if len(date) == 4 and (1000 <= int(date) <= 3000):
			xml_file = delete_annotation(xml_file, PHI_type, text)
		elif len(date) == 2:
			xml_file = delete_annotation(xml_file, PHI_type, text)

	if re.findall(r'(^\d{2,4}(\')?s$|^\'\d{2}$)',date) != []:
		xml_file = delete_annotation(xml_file, PHI_type, text)
	
	# Remove season
	seasons = ["spring","winter","fall","summer","autumn"]
	if date.lower() in seasons:
		xml_file = delete_annotation(xml_file, PHI_type, text)
	
	# Remove day of week
	days=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday","Mon","Tues","Wed","Thurs","Fri","Sat","Sun"]
	if date in days:
		xml_file = delete_annotation(xml_file, PHI_type, text)
	
	return xml_file

def remove_abbrevs(xml_file,text,phi_type):
	
	if len(text)<4 and str(text).isupper():
		xml_file = delete_annotation(xml_file, phi_type, text)
	return xml_file

def remove_ids(xml_file,text,phi_type):
	
	# Three sub-categories:
	## IDNUM
	## MEDICALRECORD
	## DEVICE

	if len(text)<5:
		xml_file = delete_annotation(xml_file, phi_type, text)

	return xml_file

def remove_countries(xml_file,text,phi_type):
	
	if phi_type == "COUNTRY":
		xml_file = delete_annotation(xml_file, phi_type, text)
	return xml_file

def remove_states(xml_file,text,phi_type):
	
	if phi_type == "STATE":
		xml_file = delete_annotation(xml_file, phi_type, text)
	return xml_file

def remove_profession(xml_file,text,phi_type):
	
	if phi_type == "PROFESSION":
		xml_file = delete_annotation(xml_file, phi_type, text)
	return xml_file

def remove_age_under_90(xml_file,text,phi_type,filename):
	
	standardized_age = text.split("y")[0]
	non_numeric_ages =	["18 month", "20's", "32y5.7m", "56y0.5m","50's","50s", "60's", "60's", "60's", "60's", "60s", "60s", "60s", "70's", "70's", "70s", "80's", "80's", "80's", "80's", "80's", "80's", "80's", "80's", "80's", "80's", "80s", "80s", "80s", "80s", "80s", "82nd", "Sevent", "sevent"]
	
	if standardized_age in non_numeric_ages:
		xml_file = delete_annotation(xml_file, phi_type, text)
	elif isinstance(standardized_age, int) and int(standardized_age) < 90:
		xml_file = delete_annotation(xml_file, phi_type, text)
	elif standardized_age not in non_numeric_ages and int(standardized_age) < 90:
		xml_file = delete_annotation(xml_file, phi_type, text)

	return xml_file

def remove_hospitals(xml_file,text,phi_type):
	
	# Remove hospital abbreviations
	if re.findall(r'(^[A-Z]{2,4}$)',text) != []:
		xml_file = delete_annotation(xml_file, phi_type, text)
	
	return xml_file

def main():
    
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--input", required=True,
	                help="Path to the folder with the original i2b2 xml files (testing-PHI-Gold-fixed)")
	ap.add_argument("-o", "--output", required=True,
	                help="Path to save the curated xml files to")
	args = ap.parse_args()
	
	# Loop through xml_files
	input_dir = args.input
	output_dir = args.output

	# Make the output directroy if it doesn't exist already
	try:
		os.makedirs(output_dir)
	except OSError:
		print("Output directory already exists.")

	new_dict = dict()

	for filename in os.listdir(input_dir):

		text,tags_dict,xmlstr = extractXML(input_dir,filename)
		if sys.version_info < (3, 0):
			all_tags = tags_dict.iteritems()
		else:
			all_tags = tags_dict.items()
		
		for key, value in all_tags:

			if isinstance(value, list):
				for final_value in value:

					text = final_value["@text"]
					phi_type = final_value["@TYPE"]

					# Any of these fields can be commented out if you would like to
					# retain a particular PHI category in the XML tags
					if phi_type == "DATE": 
						xmlstr = fix_dates(xmlstr,text)
					elif phi_type == "NAME" or phi_type == "DOCTOR":
						xmlstr = remove_abbrevs(xmlstr,text,phi_type)	
					# elif phi_type == "IDNUM" or phi_type == "MEDICALRECORD" or phi_type == "DEVICE":
					# 	xmlstr = remove_ids(xmlstr,text,phi_type)	
					elif phi_type == "COUNTRY":
						xmlstr = remove_countries(xmlstr,text,phi_type)
					#elif phi_type == "STATE":
					#	xmlstr = remove_states(xmlstr,text,phi_type)
					elif phi_type == "PROFESSION":
						xmlstr = remove_profession(xmlstr,text,phi_type)
					elif phi_type == "AGE":
						xmlstr = remove_age_under_90(xmlstr,text,phi_type,filename)
					elif phi_type == "HOSPITAL":
						xmlstr = remove_hospitals(xmlstr,text,phi_type)								
			else:
				final_value = value
				text = final_value["@text"]
				phi_type = final_value["@TYPE"]

				if phi_type == "DATE":
					xmlstr = fix_dates(xmlstr,text)
				elif phi_type == "NAME" or phi_type == "DOCTOR":
					xmlstr = remove_abbrevs(xmlstr,text,phi_type)
				# elif phi_type == "IDNUM" or phi_type == "MEDICALRECORD" or phi_type == "DEVICE":
				# 	xmlstr = remove_ids(xmlstr,text,phi_type)
				elif phi_type == "COUNTRY":
					xmlstr = remove_countries(xmlstr,text,phi_type)
				#elif phi_type == "STATE":
				#	xmlstr = remove_states(xmlstr,text,phi_type)
				elif phi_type == "PROFESSION":
					xmlstr = remove_profession(xmlstr,text,phi_type)		
				elif phi_type == "AGE":
					xmlstr = remove_age_under_90(xmlstr,text,phi_type,filename)
				elif phi_type == "HOSPITAL":
					xmlstr = remove_hospitals(xmlstr,text,phi_type)	
		
		output_file = output_dir+filename
		with open(output_file, "w") as text_file:
			text_file.write(xmlstr.decode("utf-8"))


if __name__ == "__main__":
	main()






