-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- Create the clinical_knowledge table
create table if not exists clinical_knowledge (
  id uuid default gen_random_uuid() primary key,
  patient_id text not null,
  content text not null,
  embedding vector(384),
  metadata jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create a function to search for clinical knowledge using pgvector
create or replace function match_clinical_knowledge (
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  p_patient_id text
)
returns table (
  id uuid,
  patient_id text,
  content text,
  metadata jsonb,
  similarity float
)
language sql stable
as $$
  select
    clinical_knowledge.id,
    clinical_knowledge.patient_id,
    clinical_knowledge.content,
    clinical_knowledge.metadata,
    1 - (clinical_knowledge.embedding <=> query_embedding) as similarity
  from clinical_knowledge
  where 
    clinical_knowledge.patient_id = p_patient_id 
    and 1 - (clinical_knowledge.embedding <=> query_embedding) > match_threshold
  order by clinical_knowledge.embedding <=> query_embedding
  limit match_count;
$$;

-- Create the uploads table
create table if not exists uploads (
  id uuid default gen_random_uuid() primary key,
  patient_id text not null,
  filename text not null,
  status text not null check (status in ('processing', 'indexed', 'failed')),
  error_message text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create missing patient management tables

create table if not exists vitals_history (
  id bigint generated always as identity primary key,
  patient_id text not null,
  timestamp timestamp with time zone default timezone('utc'::text, now()) not null,
  spo2 double precision,
  heart_rate double precision,
  temperature double precision,
  respiratory_rate double precision,
  systolic_bp double precision,
  diastolic_bp double precision
);

create table if not exists alerts (
  id bigint generated always as identity primary key,
  patient_id text not null,
  timestamp timestamp with time zone default timezone('utc'::text, now()) not null,
  severity text not null,
  score integer not null,
  alerts jsonb default '[]'::jsonb not null
);

create table if not exists patient_history (
  id bigint generated always as identity primary key,
  patient_id text not null,
  timestamp timestamp with time zone default timezone('utc'::text, now()) not null,
  interaction_text text not null,
  extracted_symptoms jsonb default '[]'::jsonb not null,
  risk_score integer not null,
  severity text not null
);

create table if not exists medications (
  id bigint generated always as identity primary key,
  patient_id text not null,
  timestamp timestamp with time zone default timezone('utc'::text, now()) not null,
  medicine text not null,
  dosage text not null,
  frequency text not null,
  source_file text
);

create table if not exists lab_results (
  id bigint generated always as identity primary key,
  patient_id text not null,
  timestamp timestamp with time zone default timezone('utc'::text, now()) not null,
  test text not null,
  value double precision not null,
  unit text not null,
  reference_range text,
  source_file text
);

create table if not exists medical_images (
  id bigint generated always as identity primary key,
  patient_id text not null,
  timestamp timestamp with time zone default timezone('utc'::text, now()) not null,
  image_type text not null,
  observation text not null,
  image_path text not null
);

create table if not exists videos (
  id bigint generated always as identity primary key,
  patient_id text not null,
  timestamp timestamp with time zone default timezone('utc'::text, now()) not null,
  video_path text not null,
  summary text not null,
  observations text not null
);

create table if not exists risk_history (
  id bigint generated always as identity primary key,
  patient_id text not null,
  timestamp timestamp with time zone default timezone('utc'::text, now()) not null,
  risk_score integer not null,
  reasons jsonb default '[]'::jsonb not null,
  severity text not null
);

-- Force PostgREST to reload the schema cache so the new tables and functions are available via the API
NOTIFY pgrst, 'reload schema';
