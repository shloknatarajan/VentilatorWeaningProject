# Ventilator Weaning Recommendation System
Ventilator Weaning Recommendation System project for Team 41

Team:
- Zhiyu Liu, zliu721@gatech.edu, zl93@cornell.edu
- (Michael) Josh Bauzon, mbauzon3@gatech.edu
- Shlok Natarajan, shlok.natarajan@gatech.edu
- Brendon Machado, brendon.machado@gatech.edu
- Shiyan Jiang

TA: Raj Vansia

Running inside docker is the best way to run this app locally

## Running inside Docker (RECOMMENDED)
1. Install Docker
2. Install docker-compose (`pip install docker-compose`)
3. Set up virtual environment
    1. `pip install virtualenv` if you don't already have virtualenv installed
    2. `virtualenv venv`
    3. `source venv/bin/activate`
    4. `pip install -r requirements.txt`
4. Create docker images and run
    1. `docker-compose down`
    2. `docker-compose build`
    3. `docker-compose up --force-recreate`
5. Server will run on 0.0.0.0:5000


## Running without Docker
### Dependencies
#### Required
- postgres
    - use Homebrew: `brew install postgres`; or
    - download dmg from https://postgresapp.com

### To Run:
1. `psql -f sql/schema.sql`
2. Set up virtual environment
    1. `pip install virtualenv` if you don't already have virtualenv installed
    2. `virtualenv venv`
    3. `source venv/bin/activate`
    4. `pip install -r requirements.txt`
3. Only run below if migrations folder is not present
    a. `python manage.py db init`
    b. `python manage.py db migrate`
    c. `python manage.py db upgrade`
4. `python app.py`
5. Server will run on 0.0.0.0:5000
