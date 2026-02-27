-- Content Factory: общая схема БД для цепочки агентов
-- PostgreSQL

-- 1. Справочники каналов, рубрик, услуг/комплексов
------------------------------------------------------------

CREATE TABLE IF NOT EXISTS channels (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS rubrics (
    id      SERIAL PRIMARY KEY,
    key     TEXT NOT NULL UNIQUE,
    title   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS services (
    id          SERIAL PRIMARY KEY,
    key         TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS complexes (
    id          SERIAL PRIMARY KEY,
    key         TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS complex_services (
    id          SERIAL PRIMARY KEY,
    complex_id  INTEGER NOT NULL REFERENCES complexes(id) ON DELETE CASCADE,
    service_id  INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    UNIQUE (complex_id, service_id)
);

-- 2. Кампании / контент-спринты
------------------------------------------------------------

CREATE TABLE IF NOT EXISTS content_campaigns (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    start_date      DATE,
    end_date        DATE,
    target_service_id INTEGER REFERENCES services(id),
    created_by_agent TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- 3. Контент-единицы и календарь
------------------------------------------------------------

CREATE TABLE IF NOT EXISTS content_items (
    id              SERIAL PRIMARY KEY,
    external_id     TEXT,
    title           TEXT NOT NULL,
    description     TEXT,
    status          TEXT NOT NULL DEFAULT 'planned',
    channel_id      INTEGER REFERENCES channels(id),
    rubric_id       INTEGER REFERENCES rubrics(id),
    service_id      INTEGER REFERENCES services(id),
    complex_id      INTEGER REFERENCES complexes(id),
    content_type    TEXT NOT NULL,
    funnel_stage    TEXT,
    priority        INTEGER DEFAULT 0,
    planned_date    DATE,
    internal_deadline DATE,
    campaign_id     INTEGER REFERENCES content_campaigns(id),
    created_by_agent TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_content_items_planned_date ON content_items(planned_date);
CREATE INDEX IF NOT EXISTS idx_content_items_status ON content_items(status);
CREATE INDEX IF NOT EXISTS idx_content_items_channel ON content_items(channel_id);

CREATE TABLE IF NOT EXISTS content_keywords (
    id              SERIAL PRIMARY KEY,
    content_item_id INTEGER NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    keyword         TEXT NOT NULL,
    cluster         TEXT,
    intent          TEXT,
    UNIQUE (content_item_id, keyword)
);

-- 4. Задания агентов
------------------------------------------------------------

CREATE TABLE IF NOT EXISTS agent_tasks (
    id              SERIAL PRIMARY KEY,
    agent_name      TEXT NOT NULL,
    content_item_id INTEGER REFERENCES content_items(id),
    task_type       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'queued',
    input_ref       JSONB,
    output_ref      JSONB,
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent_name ON agent_tasks(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_content_item ON agent_tasks(content_item_id);

-- 5. Исследование ключевых слов (Research)
------------------------------------------------------------

CREATE TABLE IF NOT EXISTS keyword_research (
    id          SERIAL PRIMARY KEY,
    service_id  INTEGER REFERENCES services(id),
    geo         TEXT,
    tool        TEXT,
    params      JSONB,
    raw_data    JSONB,
    created_by_agent TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS keyword_research_items (
    id              SERIAL PRIMARY KEY,
    research_id     INTEGER NOT NULL REFERENCES keyword_research(id) ON DELETE CASCADE,
    keyword         TEXT NOT NULL,
    search_volume   INTEGER,
    difficulty      NUMERIC,
    serp_notes      TEXT,
    UNIQUE (research_id, keyword)
);

-- 6. Версии контента (Writer / Editor)
------------------------------------------------------------

CREATE TABLE IF NOT EXISTS content_versions (
    id              SERIAL PRIMARY KEY,
    content_item_id INTEGER NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    version         INTEGER NOT NULL,
    source_agent    TEXT NOT NULL,
    text            TEXT NOT NULL,
    meta            JSONB,
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (content_item_id, version)
);

-- 7. Публикация (Publish)
------------------------------------------------------------

CREATE TABLE IF NOT EXISTS publishing_log (
    id              SERIAL PRIMARY KEY,
    content_item_id INTEGER NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    channel_id      INTEGER REFERENCES channels(id),
    platform        TEXT NOT NULL,
    external_id     TEXT,
    url             TEXT,
    published_at    TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'success',
    response_raw    JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_publishing_log_content_item ON publishing_log(content_item_id);

-- 8. Метрики (Analyst)
------------------------------------------------------------

CREATE TABLE IF NOT EXISTS content_metrics (
    id              SERIAL PRIMARY KEY,
    content_item_id INTEGER NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    date            DATE NOT NULL,
    views           INTEGER,
    reads           INTEGER,
    clicks          INTEGER,
    conversions     INTEGER,
    source          TEXT,
    raw_data        JSONB,
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (content_item_id, date, source)
);

CREATE INDEX IF NOT EXISTS idx_content_metrics_content_item ON content_metrics(content_item_id);
