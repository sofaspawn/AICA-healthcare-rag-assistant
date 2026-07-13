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

-- Disable Row-Level Security (RLS) for all tables to allow backend direct API access

alter table vitals_history disable row level security;
alter table alerts disable row level security;
alter table patient_history disable row level security;
alter table medications disable row level security;
alter table lab_results disable row level security;
alter table medical_images disable row level security;
alter table videos disable row level security;
alter table risk_history disable row level security;
alter table uploads disable row level security;
alter table clinical_knowledge disable row level security;

-- Create a function to search using hybrid search (vector similarity + full text search via RRF)
create or replace function match_clinical_knowledge_hybrid (
  query_embedding vector(384),
  query_text text,
  match_threshold float,
  match_count int,
  p_patient_id text,
  full_text_weight float default 1.0,
  semantic_weight float default 1.0,
  rrf_k int default 50
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
  with full_text as (
    select
      id,
      row_number() over (order by ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) desc) as rank_ix
    from
      clinical_knowledge
    where
      patient_id = p_patient_id and
      to_tsvector('english', content) @@ plainto_tsquery('english', query_text)
    limit least(match_count * 2, 100)
  ),
  semantic as (
    select
      id,
      1 - (embedding <=> query_embedding) as similarity,
      row_number() over (order by embedding <=> query_embedding) as rank_ix
    from
      clinical_knowledge
    where
      patient_id = p_patient_id and
      1 - (embedding <=> query_embedding) > match_threshold
    limit least(match_count * 2, 100)
  )
  select
    ck.id,
    ck.patient_id,
    ck.content,
    ck.metadata,
    -- RRF calculation
    coalesce(1.0 / (rrf_k + full_text.rank_ix), 0.0) * full_text_weight +
    coalesce(1.0 / (rrf_k + semantic.rank_ix), 0.0) * semantic_weight as similarity
  from
    full_text
    full outer join semantic on full_text.id = semantic.id
    join clinical_knowledge ck on coalesce(full_text.id, semantic.id) = ck.id
  order by
    similarity desc
  limit match_count;
$$;

-- Force PostgREST to reload the schema cache so the new tables and functions are available via the API
NOTIFY pgrst, 'reload schema';
