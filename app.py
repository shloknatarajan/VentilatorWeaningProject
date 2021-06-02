# Utils
from os import environ
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import logging
import sys

# Flask
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
import flask_login

# FHIR
from fhirclient import client
from fhirclient.models.patient import Patient as FHIRPatient
from fhirclient.models.observation import Observation as FHIRObservation
import hapi

# Create the application object
app = Flask(__name__, template_folder="templates")
app.secret_key = "random_key"

# Set up db SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ns = str(environ.get('NAMESPACE'))
app.logger.info('start: namespace ns is %s' % ns)

# Set up FHIR
smart_defaults = {
    'app_id': 'my_web_app',
    'api_base': 'https://apps.hdap.gatech.edu/hapiR4/baseR4/',
    'redirect_uri': 'http://localhost:8000/fhir-app/',
}
myfhirclient = client.FHIRClient(settings=smart_defaults)

# Set up utils
logging.basicConfig(level=logging.INFO)
utc=pytz.UTC
login_manager = LoginManager()
login_manager.init_app(app)

# All Stages
STAGE_1 = 'Ready for Stage 1 Evaluation'
STAGE_WAIT = 'Waiting to be Ready for Stage 2 Evaluation'
STAGE_2 = 'Ready for Stage 2 Evaluation'
STAGE_REC = 'Extubate'
STAGE_NR = 'Not Recommended'

#list of patients:
PATIENT_LIST = ['49168', '49171', '49174', '49177', '49180']


#--------------------------------------------------------------------------------------------------------------
#  CLASSES
#--------------------------------------------------------------------------------------------------------------

# User mapped to Users table
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    authenticated = True

    def __init__(self, email, password, firstname, lastname):
        self.email = email
        self.password = password
        self.firstname = firstname
        self.lastname = lastname

    def __rep__(self):
        return '<User %r>' % self.email

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.id

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

# Patient mapped to Patients table
class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fhir_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String, nullable=False)
    stage = db.Column(db.String, nullable=False)
    respiratory_rate = db.Column(db.Integer, nullable=False)
    sp_o2 = db.Column(db.Integer, nullable=False)
    last_decision_ts = db.Column(db.TIMESTAMP)
    time_till_next_stage = db.Column(db.TIMESTAMP)

    def __init__(self, first_name, last_name, age, gender, stage, respiratory_rate, sp_o2, last_decision_ts, time_till_next_stage, fhir_id):
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self.gender = gender
        self.stage = stage
        self.respiratory_rate = respiratory_rate
        self.sp_o2 = sp_o2
        self.last_decision_ts = last_decision_ts
        self.time_till_next_stage = time_till_next_stage
        self.fhir_id = fhir_id

    def __rep__(self):
        return '<Patient %r>' % self.last_name

# Questionnaire Answers
class QuestionnaireAnswer():
    def __init__(self, recovered, breathing, awake, respiratory_rate, sp_o2, cpap=None):
        self.recovered = recovered
        self.breathing = breathing
        self.awake = awake
        self.respiratory_rate = respiratory_rate
        self.sp_o2 = sp_o2
        self.cpap = cpap


#--------------------------------------------------------------------------------------------------------------
#  AUTHORIZATION MANAGER
#--------------------------------------------------------------------------------------------------------------

@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.
    :param unicode user_id: user_id (email) user to retrieve
    """
    return User.query.get(user_id)

@login_manager.unauthorized_handler
def unauthorized(): # for /evaluate and /patientProfile
    return render_template('401-2.html', ns=ns)

#--------------------------------------------------------------------------------------------------------------
#  ROUTE HANDLING
#--------------------------------------------------------------------------------------------------------------

# Homepage redirect to login
@app.route('/')
def home():
    add_all_patients()
    return redirect(ns + "login")

# TODO: remove
@app.route('/welcome')
def welcome():
    return render_template('welcome.html', doctor_last_name=session['doctor_last_name'], ns=ns)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(ns + "allPatients")
    error = None
    if request.method == 'POST':
        email = request.form['email']
        pw = request.form['password']
        users=User.query.all()

        error = 'User not found. Please try again.'
        user_not_found = True
        # TODO: simplify
        for user in users:
            if (user.email == email):
                user_not_found = False
                if (user.password == pw):
                    session['logged_in'] = True
                    session['doctor_last_name'] = user.lastname
                    app.logger.info('User successfully logged in as %s' % user.lastname)
                    app.logger.info('basePath is %s' % ns)
                    login_user(user)
                    return redirect(ns + "allPatients")
                else:
                    app.logger.error('User exists but invalid password')
                    error = 'Invalid Credentials. Please try again.'
        if (user_not_found):
            app.logger.error('Email does not exist in database')
    return render_template('login.html', error=error)

# Logout
@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('doctor_last_name', None)
    app.logger.info('User log out')
    logout_user()
    return redirect(ns)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        password = request.form['password']
        
        users=User.query.all()

        error = 'Email already exists. Please Login.'
        emailAlreadyExists = False
        # TODO: simplify
        for user in users:
            if (user.email == email):
                error = 'Email already exists. Please Login.'
                emailAlreadyExists = True
                break
        if (emailAlreadyExists == False):
            try:
                user=User(
                    email = email,
                    password = password,
                    firstname = firstname,
                    lastname = lastname
                )
                db.session.add(user)
                db.session.commit()
                return "User added. user id={}".format(user.id)
            except Exception as e:
                return(str(e))
    return render_template('register.html', error=error)

# More Information page
@app.route('/moreInformation')
def moreInformation():
    if current_user.is_authenticated ==  False:
        return render_template('moreInformation.html', ns=ns)
    return render_template('moreInformation.html', ns=ns, doctor_last_name=session['doctor_last_name'])

# All Patients page
@app.route('/allPatients')
def allPatients():
    if current_user.is_authenticated ==  False:
        return render_template('401-1.html', ns=ns)
    add_all_patients()
    updatePatientsInWaiting()
    patients=Patient.query.order_by(Patient.id).all()
    app.logger.info('patients type %s' % type(patients))
    app.logger.info('patients  %s' % patients)
    return render_template('allPatients.html', ns=ns, doctor_last_name=session['doctor_last_name'], patients=patients)

# Patient Profile page
@app.route('/patientProfile/<patient_id>')
@login_required
def patientProfile(patient_id):
    updatePatientsInWaiting()
    pid = request.args.get('pid', '')
    app.logger.info('profile patient id: %s' % pid)
    patient = Patient.query.filter_by(id=patient_id).first()
    if patient == None:
        return render_template('404-patient.html', ns=ns)
    app.logger.info('patient name: %s' % patient.first_name)
    app.logger.info('patient stage: %s' % patient.stage)
    app.logger.info('patient type: %s' % type(patient))
    app.logger.info('patient last_decision_ts: %s' % patient.last_decision_ts)
    app.logger.info('patient: %s' % patient)
    return render_template('patientProfile.html', ns=ns, doctor_last_name=session['doctor_last_name'], patient=patient)

# Evaluate page
@app.route('/evaluate/<patient_id>', methods=['GET', 'POST'])
@login_required
def evaluate(patient_id):
    app.logger.info('evaluate patient id: %s' % patient_id)
    patient = Patient.query.filter_by(id=patient_id).first()
    if patient == None:
        return render_template('404-patient.html')
    app.logger.info('patient name: %s' % patient.first_name)
    app.logger.info('patient stage: %s' % patient.stage)
    app.logger.info('patient type: %s' % type(patient))
    app.logger.info('patient: %s' % patient)

    if request.method == 'POST':
        recovered = convertYesNoToTrueFalse(request.form['recovered'])
        breathing = convertYesNoToTrueFalse(request.form['breathing'])
        awake = convertYesNoToTrueFalse(request.form['awake'])
        app.logger.info('Input recovered %s' % recovered)
        app.logger.info('Input breathing %s' % breathing)
        app.logger.info('Input awake %s' % awake)
        respiratory_rate = int(request.form['respiratory_rate'])
        sp_o2 = int(request.form['sp_o2'])
        app.logger.info('Input respiratory_rate %s' % respiratory_rate)
        app.logger.info('Input sp_o2 %s' % sp_o2)
        cpap = None
        if 'cpap' in request.form:
            cpap = convertYesNoToTrueFalse(request.form['cpap'])
            app.logger.info('Input cpap %s' % cpap)
        qa = QuestionnaireAnswer(recovered, breathing, awake, respiratory_rate, sp_o2, cpap)
        decision = makeDecision(qa)
        app.logger.info('final decision is %s' % decision)
        app.logger.info('namespace ns is %s' % ns)
        updatePatientStage(patient_id, decision)
        if (ns=='/'): # running local
            return redirect(ns + "patientProfile/" + patient_id)
        return redirect("../" + ns + "patientProfile/" + patient_id)

    # method is GET at this point
    if (patient.stage == STAGE_2):
        return render_template('stage2evaluation.html', ns=ns, doctor_last_name=session['doctor_last_name'], patient=patient)
    return render_template('stage1evaluation.html', ns=ns, doctor_last_name=session['doctor_last_name'], patient=patient)

# TODO: remove. Only use for FHIR reference
@app.route('/fhirclient')
def fhirclient():
    patient = FHIRPatient.read(33598, myfhirclient.server)
    app.logger.info('birth date: %s' % patient.birthDate.isostring)
    # '1963-06-12'
    myname = myfhirclient.human_name(patient.name[0])
    app.logger.info('myname is %s' % myname)
    #return render_template('index.html', ns=ns)
    return 'This is retrieved from fhir server. <br><br>  Name = ' + myname + '<br>  Birth date = ' + patient.birthDate.isostring

#Show 404 Page
def page_not_found(e):
  return render_template('error404.html'), 404

app.register_error_handler(404, page_not_found)



#--------------------------------------------------------------------------------------------------------------
#  HELPER FUNCTIONS
#--------------------------------------------------------------------------------------------------------------

def convertYesNoToTrueFalse(yesOrNo):
    return yesOrNo == 'yes' or yesOrNo == 'Yes' or yesOrNo == 'YES'

def makeDecision(questionnaireAnswer):
    if questionnaireAnswer.recovered and questionnaireAnswer.breathing and questionnaireAnswer.awake:
        app.logger.info('passed first 3 conditions')
        app.logger.info('questionnaireAnswer.respiratory_rate is %s' % questionnaireAnswer.respiratory_rate)
        app.logger.info('questionnaireAnswer.sp_o2 is %s' % questionnaireAnswer.sp_o2)
        if questionnaireAnswer.respiratory_rate < 25 and questionnaireAnswer.sp_o2 > 94:
            app.logger.info('passed next 2 conditions')
            if questionnaireAnswer.cpap is not None:
                app.logger.info('passed last condition')
                return questionnaireAnswer.cpap
            else:
                return True
    return False

def updatePatientStage(patient_id, decision):
    patient = Patient.query.filter_by(id=patient_id).first_or_404(description='There is no patient with ID {} found!'.format(patient_id))
    currentStage = patient.stage
    nextStage = currentStage
    if decision == True:
        if currentStage == STAGE_1:
            nextStage = STAGE_WAIT
            patient.time_till_next_stage = datetime.now() + timedelta(minutes=2)
        elif currentStage == STAGE_2:
            nextStage = STAGE_REC
    else:
        if currentStage == STAGE_2:
            nextStage = STAGE_1
    patient.stage = nextStage
    patient.last_decision_ts = datetime.now()
    app.logger.info('new patient.stage: %s' % patient.stage)
    app.logger.info('new patient.last_decision_ts: %s' % patient.last_decision_ts)
    db.session.commit()

def updatePatientObservations(patient_id):
    results = hapi.get_recent_observations_for_patient(patient_id)
    #TODO
    #call SQL and stuff

def updatePatientsInWaiting():
    patients = Patient.query.order_by(Patient.id).all()
    for patient in patients:
        if patient.stage == STAGE_WAIT:
            app.logger.info('patient %s in WAITING' % patient.id)
            time_now = utc.localize(datetime.now())
            time_till_next_stage = utc.localize(patient.time_till_next_stage)
            app.logger.info('time_now %s' % time_now)
            app.logger.info('time_till_next_stage %s' % time_till_next_stage)
            if time_now > time_till_next_stage:
                app.logger.info('updateing patient %s to Ready for Stage 2' % patient.id)
                patient.stage = STAGE_2
                patient.time_till_next_stage = None
                db.session.commit()

def add_all_patients():
    patients=Patient.query.all()
    app.logger.info(patients)
    if len(patients) == 0:
        app.logger.info('adding patients')
        for patient_id in PATIENT_LIST:
            patient_dict = hapi.get_new_patient_info(patient_id)
            app.logger.info(patient_dict['first_name'])
            patient = Patient(**patient_dict)
            patients.append(patient)
            try:
                db.session.add(patient)
                db.session.commit()
                app.logger.info("Added Patient {}".format(patient.id))
            except Exception as e:
                app.logger.info('EPIC FAIL')
                app.logger.info(str(e))
#--------------------------------------------------------------------------------------------------------------
#  DB INIT
#--------------------------------------------------------------------------------------------------------------
# for each patient, add patient to DB



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
