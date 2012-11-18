create table if not exists devices (
    id varchar(100),
    owner_email varchar(255),
    task_id int,
    last_checkin datetime null default null,
    primary key (id)
);

create table if not exists owners (
    id int auto_increment primary key,
    first_name varchar(255),
    last_name varchar(255),
    username varchar(255),
    password varchar(255),
    assoc varchar(255),
    email varchar(255)
);

create table if not exists tasks (
    id int auto_increment primary key,
    owner_email varchar(255),
    wanted_devices int,
    code_path varchar(255),
    data_file_path varchar(255),
    name varchar(255)
);

create table if not exists results (
    id int auto_increment primary key,
    value_type varchar(255),
    value varchar(255),
    task_id int,
    device_id varchar(100)
);
