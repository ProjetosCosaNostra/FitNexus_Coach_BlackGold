-- FitNexus Coach BlackGold — schema inicial de referência

create table if not exists profiles (
  id uuid primary key,
  role text not null default 'coach',
  full_name text,
  business_name text,
  instagram text,
  whatsapp text,
  created_at timestamp with time zone default now()
);

create table if not exists students (
  id uuid primary key default gen_random_uuid(),
  coach_id uuid not null,
  full_name text not null,
  goal text,
  active boolean default true,
  created_at timestamp with time zone default now()
);

create table if not exists workouts (
  id uuid primary key default gen_random_uuid(),
  coach_id uuid not null,
  student_id uuid not null,
  title text not null,
  description text,
  created_at timestamp with time zone default now()
);

create table if not exists exercises (
  id uuid primary key default gen_random_uuid(),
  workout_id uuid not null,
  name text not null,
  sets text,
  reps text,
  load text,
  rest_seconds int,
  notes text,
  position int default 0
);

create table if not exists workout_logs (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null,
  workout_id uuid not null,
  exercise_id uuid,
  completed boolean default false,
  load_used text,
  notes text,
  created_at timestamp with time zone default now()
);
