create table training_exercises (
    id uuid primary key,
    user_id varchar(200) not null default '',
    name varchar(200) not null,
    prescription_type varchar(32) not null default 'STRENGTH',
    default_sets bigint not null default 0 check (default_sets >= 0),
    default_reps bigint not null default 0 check (default_reps >= 0),
    muscle_group varchar(200) not null default '',
    default_time bigint not null default 0 check (default_time >= 0),
    notes text not null default '',
    created_at timestamp not null,
    updated_at timestamp not null
);

create index idx_training_exercises_user_id_name on training_exercises (user_id, name);
