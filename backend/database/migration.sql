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

-- Force PostgREST to reload the schema cache so the new tables and functions are available via the API
NOTIFY pgrst, 'reload schema';
