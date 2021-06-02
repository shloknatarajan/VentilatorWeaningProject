\c weaningrecsystem team41;

create table if not exists Users (
    id serial primary key,
    email varchar(50) not null unique,
    firstName varchar(50) not null,
    lastName varchar(50) not null,
    password varchar(50) not null -- can be hashed
);

insert into Users(email, firstName, lastName, password) values ('mbauzon3@gatech.edu', 'Josh', 'Bauzon', 'mypass');
insert into Users(email, firstName, lastName, password) values ('shlok.natarajan@gatech.edu', 'Shlok', 'Natarajan', 'mypass');
insert into Users(email, firstName, lastName, password) values ('bmachado3@gatech.edu', 'Brendon', 'Machado', 'mypass');
insert into Users(email, firstName, lastName, password) values ('sjiang98@gatech.edu', 'Shiyan', 'Jiang', 'mypass');
insert into Users(email, firstName, lastName, password) values ('zliu721@gatech.edu', 'Zhiyu', 'Liu', 'mypass');
insert into Users(email, firstName, lastName, password) values ('sample@gmail.com', 'John', 'Doe', 'mypass');
insert into Users(email, firstName, lastName, password) values ('another@gmail.com', 'Tom', 'Smith', 'mypass');

SET TIMEZONE='America/New_york';

create table if not exists Patients (
    id serial primary key,
    fhir_id varchar(50) not null,
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

-- insert into Patients(fhir_id, first_name, last_name, age, gender, stage, respiratory_rate, sp_o2) values (111, 'LeBron', 'James', 53, 'Male', 'Ready for Stage 1 Evaluation', 20, 97);
-- insert into Patients(fhir_id, first_name, last_name, age, gender, stage, respiratory_rate, sp_o2) values (222, 'Kobe', 'Bryant', 64, 'Male', 'Ready for Stage 1 Evaluation', 30, 97);
-- insert into Patients(fhir_id, first_name, last_name, age, gender, stage, respiratory_rate, sp_o2, last_decision_ts) values (333, 'Dwyane', 'Wade', 34, 'Male', 'Ready for Stage 2 Evaluation', 20, 97, now());
-- insert into Patients(fhir_id, first_name, last_name, age, gender, stage, respiratory_rate, sp_o2) values (444, 'James', 'Harden', 40, 'Male', 'Extubate', 17, 96);
-- insert into Patients(fhir_id, first_name, last_name, age, gender, stage, respiratory_rate, sp_o2) values (555, 'Michael', 'Jordan', 60, 'Male', 'Extubate', 2, 2);
