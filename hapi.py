import urllib
import requests
import glob
import json
from datetime import timedelta
from datetime import datetime

# api config constants
baseurl = 'https://apps.hdap.gatech.edu/hapiR4/baseR4/'
headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

# stages
STAGE_1 = 'Ready for Stage 1 Evaluation'
STAGE_WAIT = 'Waiting to be Ready for Stage 2 Evaluation'
STAGE_2 = 'Ready for Stage 2 Evaluation'
STAGE_REC = 'Extubate'
STAGE_NR = 'Not Recommended'

def post_resource(data_json):#, reference=None):
	url = baseurl + data_json['resourceType'] + '?_format=json&_pretty=true'
	# print(url)
	r = None #request object
	# if data_json['resourceType'] == 'Patient':
	# 	r = requests.post(url, json=data_json, headers=headers, allow_redirects=False, verify=False)
	# else:
		# r = requests.post(url, json=data_json, headers=headers, allow_redirects=False, verify=False)
	r = requests.post(url, json=data_json, headers=headers, allow_redirects=False, verify=False)

	return r

def get_resource_reference(response):
	rJson = response.json()
	referenceString = rJson['issue'][0]['diagnostics'].split('"')[1]
	reference = referenceString.split('/_history')[0]
	return reference

def get_JSON_from_file(jsonFilePath):
	with open(jsonFilePath, 'r') as jsonFile:
		data = ''.join([x.strip() for x in jsonFile.readlines()])
		data_json = json.loads(data)
		return data_json

def processPatient(patientDir):
	# process the patient to get the patient reference
	patientPath = glob.glob(patientDir+'patient*')[0]
	# print(patientPath)
	patientJSON = get_JSON_from_file(patientPath)
	patientResponse = post_resource(patientJSON)
	patient_reference = get_resource_reference(patientResponse)#.split('/')[1]
	print('created patient: {}'.format(patient_reference))
	patientJSON['identifier'] = patient_reference.split('/')[1]
	print(type(patientJSON))
	with open(patientPath, 'w', encoding="utf8") as patFile:
		json.dump(patientJSON, patFile, indent=4)

	# process all observations
	allPaths = glob.glob(patientDir+'*')
	for path in allPaths:
		data_json = get_JSON_from_file(path)
		if data_json['resourceType'] != 'Patient':

			#modify the patient reference
			data_json['subject']['reference'] = patient_reference

			resource_response = post_resource(data_json)#, patient_reference)
			if resource_response != None:
				resource_reference = get_resource_reference(resource_response)
				print('created resource: {}'.format(resource_reference))
				data_json['id'] = resource_reference.split('/')[1]
				with open(path, 'w', encoding="utf8") as obsFile:
					json.dump(data_json, obsFile, indent=4)

	return patient_reference.split('/')[1]
	
codes = {
	'o2': set(["2708-6", "59408-5", "150456"]),
	'rr': set(["9279-1"])
}

def get_recent_observations_for_patient(patientID):
	url = baseurl + 'Observation/_search?subject=Patient%2F'+patientID
	print(url)
	data_json = {
		'subject': 'Patient/' + patientID
	}
	r = requests.get(url, json=data_json, headers=headers, allow_redirects=False, verify=False)
	observations = r.json()['entry']
	mostRecentO2 = None
	mostRecentRR = None
	if observations != None:
		for obs in observations:
			obs = obs['resource']
			code = obs['code']['coding'][0]['code']
			getDate = lambda x: x['meta']['lastUpdated']
			if code in codes['o2']:
				if mostRecentO2 is None or getDate(obs) > getDate(mostRecentO2):
					mostRecentO2 = obs
			if code in codes['rr']:
				if mostRecentRR is None or getDate(obs) > getDate(mostRecentRR):
					mostRecentRR = obs
		getVal = lambda x: x['valueQuantity']['value']
		out = {'patient': patientID,
				'sp_o2': getVal(mostRecentO2),
				'respiratory_rate': getVal(mostRecentRR)
				}
		return out
	return None


'''
create table if not exists Patients (
    id serial primary key,
    fhir_id integer not null,
    first_name varchar(50) not null,
    last_name varchar(50) not null,
    age integer not null,
    gender varchar(50) not null,
    stage varchar(50) not null,
    respiratory_rate integer not null,
    sp_o2 integer not null,
    last_decision_ts timestamp,
    time_till_next_stage timestamp
);
'''

def addAllPatientsFromFiles():
	patientDirs = glob.glob('json/*/')
	patients = []
	for patient_dir in patientDirs:
		patients.append(processPatient(patient_dir))
	print('patientlist')
	print(patients)
	return patients

def calculate_age(born):
    today = datetime.now()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def get_new_patient_info(patientID):
	url = baseurl + '/Patient/'+patientID
	r = requests.get(url, headers=headers, allow_redirects=False, verify=False)
	p_json = r.json()
	dict_patient = {}
	dict_patient['fhir_id'] = patientID
	dict_patient['first_name'] = p_json['name'][0]['given'][0] or 'NONE'
	dict_patient['last_name'] = p_json['name'][0]['family'] or 'NONE'
	birthday = datetime.strptime(p_json['birthDate'], '%Y-%m-%d')
	dict_patient['age'] = calculate_age(birthday)
	dict_patient['gender'] = p_json['gender']
	recent_obs = get_recent_observations_for_patient(patientID)
	dict_patient['sp_o2'] = recent_obs['sp_o2']
	dict_patient['respiratory_rate'] = recent_obs['respiratory_rate']
	f = '%Y-%m-%d %H:%M:%S'
	dict_patient['last_decision_ts'] = datetime.strftime(datetime.now(), f)
	dict_patient['time_till_next_stage'] = None
	#calculate Stage
	dict_patient['stage'] = STAGE_1
	if dict_patient['sp_o2'] < 95 or dict_patient['respiratory_rate'] > 20:
		dict_patient['stage'] = STAGE_NR

	return dict_patient



if __name__ == '__main__':
	# allPaths = glob.glob('json/*')
	# patients = addAllPatientsFromFiles()
	patients = ['49168', '49171', '49174', '49177', '49180']
	for patientID in patients:
		print(getNewPatientInfo(patientID))

	# patients = ['Patient/48931', 'Patient/48934', 'asdfa']
	# patients = ['48931', '48934']

	# for patient in patients:
	# 	observations = get_recent_observations_for_patient(patient)
	# 	print(observations)
	# print('')
		# for entry in observations['entry']:
			# print(jsondumps(entry, indent=4))
			# print(entry['resource']['resourceType'])
			# print(entry['resource']['id'])
			# print(entry['resource'].keys())
			# print('')



