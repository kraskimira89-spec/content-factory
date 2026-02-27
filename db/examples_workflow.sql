-- =============================================================================
-- Примеры SQL для цепочки агентов (Planner → Writer → Editor → Publisher → Analyst)
-- Справочный файл: подставляйте свои id, даты и текст.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. PLANNER: кампания и контент-единицы на 2 недели (сухая углекислая ванна)
-- -----------------------------------------------------------------------------

-- 1.1. Найти ID услуги
SELECT id FROM services WHERE key = 'dry_co2_bath';

-- 1.2. Создать кампанию (подставьте target_service_id из 1.1)
INSERT INTO content_campaigns (
    name, description, start_date, end_date,
    target_service_id, created_by_agent
)
VALUES (
    'CO2-спринт 2 недели',
    'Двухнедельная кампания по продвижению сухих углекислых ванн',
    '2026-03-01',
    '2026-03-14',
    1,
    'planner'
)
RETURNING id;

-- 1.3. Лонгрид в блог (channel_id=1, rubric_id по справочнику, campaign_id из 1.2)
INSERT INTO content_items (
    title, description, status,
    channel_id, rubric_id, service_id, content_type,
    funnel_stage, priority, planned_date, internal_deadline,
    campaign_id, created_by_agent
)
VALUES (
    'Сухая углекислая ванна в Ноябрьске: мягкая сосудистая терапия',
    'Опорный лонгрид о курсе сухих CO2-ванн: показания, ход процедуры, курс 10 сеансов, FAQ.',
    'planned',
    1, 1, 1, 'longread',
    'awareness', 10, '2026-03-02', '2026-02-28',
    1, 'planner'
)
RETURNING id;

-- 1.4. Ключевые слова к контент-единице (content_item_id из 1.3)
INSERT INTO content_keywords (content_item_id, keyword, cluster, intent)
VALUES
    (101, 'сухая углекислая ванна Ноябрьск', 'dry_co2_bath', 'local'),
    (101, 'сухие углекислые ванны для сосудов', 'dry_co2_bath', 'informational'),
    (101, 'курсовое лечение сухими углекислыми ваннами', 'dry_co2_bath', 'transactional');

-- 1.5. Лог задачи планировщика
INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, input_ref, output_ref)
VALUES (
    'planner', 101, 'plan_item', 'done',
    '{"campaign_id": 1, "service_key": "dry_co2_bath"}',
    '{"note": "Создан опорный лонгрид"}'
);

-- -----------------------------------------------------------------------------
-- 2. WRITER: выбор задач и сохранение черновика
-- -----------------------------------------------------------------------------

-- 2.1. Задачи на ближайшие 2 дня по услуге
SELECT
    ci.id, ci.title, ci.description, ci.content_type,
    ci.planned_date, ci.internal_deadline,
    s.name AS service_name, r.title AS rubric_title, ch.name AS channel_name
FROM content_items ci
LEFT JOIN services s ON ci.service_id = s.id
LEFT JOIN rubrics r ON ci.rubric_id = r.id
LEFT JOIN channels ch ON ci.channel_id = ch.id
WHERE ci.status = 'planned'
  AND ci.internal_deadline <= (CURRENT_DATE + INTERVAL '2 day')
  AND ci.service_id = 1
ORDER BY ci.internal_deadline, ci.priority DESC;

-- 2.2. Ключевые слова по задаче
SELECT keyword, cluster, intent FROM content_keywords WHERE content_item_id = 101;

-- 2.3. Старт работы Writer
UPDATE content_items SET status = 'in_progress', updated_at = now() WHERE id = 101;
INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, input_ref)
VALUES ('writer', 101, 'write_draft', 'running', '{"note": "Старт написания черновика лонгрида"}')
RETURNING id;

-- 2.4. Сохранение черновика (версия 1)
INSERT INTO content_versions (content_item_id, version, source_agent, text, meta)
VALUES (
    101, 1, 'writer',
    '<ТЕКСТ ЛОНГРИДА>',
    '{"word_count": 2100, "language": "ru", "tone": "дружелюбный экспертный"}'
)
RETURNING id;

-- 2.5. Закрытие задачи Writer, статус draft_ready
UPDATE agent_tasks SET status = 'done', output_ref = '{"version": 1}', finished_at = now()
WHERE content_item_id = 101 AND agent_name = 'writer' AND task_type = 'write_draft' AND status = 'running';
UPDATE content_items SET status = 'draft_ready', updated_at = now() WHERE id = 101;

-- -----------------------------------------------------------------------------
-- 3. EDITOR: черновик → правки → утверждение
-- -----------------------------------------------------------------------------

-- 3.1. Материалы, готовые к редактированию
SELECT ci.id, ci.title, ci.content_type, ci.planned_date, cv.version, cv.source_agent, cv.created_at
FROM content_items ci
JOIN LATERAL (
    SELECT * FROM content_versions v
    WHERE v.content_item_id = ci.id
    ORDER BY v.version DESC LIMIT 1
) AS cv ON true
WHERE ci.status = 'draft_ready'
ORDER BY ci.planned_date, ci.priority DESC;

-- 3.2. Текст последней версии
SELECT cv.id, cv.version, cv.text, cv.meta, ci.title, ci.description
FROM content_versions cv
JOIN content_items ci ON ci.id = cv.content_item_id
WHERE cv.content_item_id = 101
ORDER BY cv.version DESC LIMIT 1;

-- 3.3. Новая версия от Editor (version 2)
INSERT INTO content_versions (content_item_id, version, source_agent, text, meta)
VALUES (
    101, 2, 'editor',
    '<ОТРЕДАКТИРОВАННЫЙ ТЕКСТ>',
    '{"word_count": 1950, "medical_compliance_checked": true}'
)
RETURNING id;

-- 3.4. Статус approved, задача Editor
UPDATE content_items SET status = 'approved', updated_at = now() WHERE id = 101;
INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, input_ref, output_ref, finished_at)
VALUES ('editor', 101, 'edit', 'done', '{"last_writer_version": 1}', '{"approved_version": 2}', now());

-- -----------------------------------------------------------------------------
-- 4. PUBLISHER: WordPress и ВК
-- -----------------------------------------------------------------------------

-- 4.1. Лог публикации в WordPress (после успешного POST в WP API)
INSERT INTO publishing_log (
    content_item_id, channel_id, platform, external_id, url, published_at, status, response_raw
)
VALUES (
    101, 1, 'wordpress', '1234',
    'https://entuziastov75.ru/blog/suhaya-uglekislaya-vanna/',
    now(), 'success',
    '{"wp_post_id": 1234}'
)
RETURNING id;

-- 4.2. Обновить content_item (external_id, status = published)
UPDATE content_items
SET external_id = '1234', status = 'published', updated_at = now()
WHERE id = 101;

-- 4.3. Задача Publisher (WordPress)
INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, input_ref, output_ref, finished_at)
VALUES (
    'publisher', 101, 'publish_wordpress', 'done',
    '{"target_platform": "wordpress"}',
    '{"wp_post_id": 1234, "url": "https://entuziastov75.ru/blog/..."}',
    now()
);

-- 4.4. Публикация в ВК (второй канал по тому же content_item)
INSERT INTO publishing_log (
    content_item_id, channel_id, platform, external_id, url, published_at, status, response_raw
)
VALUES (
    101, 2, 'vk', '-123456789_5678',
    'https://vk.com/wall-123456789_5678',
    now(), 'success',
    '{"owner_id": -123456789, "post_id": 5678}'
);
INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, input_ref, output_ref, finished_at)
VALUES ('publisher', 101, 'publish_vk', 'done', '{"target_platform": "vk"}', '{"url": "https://vk.com/..."}', now());

-- -----------------------------------------------------------------------------
-- 5. ANALYST: метрики и пересчёт приоритетов
-- -----------------------------------------------------------------------------

-- 5.1. Публикации по услуге (для сбора метрик по URL)
SELECT ci.id, ci.title, pl.url
FROM content_items ci
JOIN publishing_log pl ON pl.content_item_id = ci.id
JOIN services s ON ci.service_id = s.id
WHERE s.key = 'dry_co2_bath' AND pl.platform = 'wordpress' AND pl.status = 'success';

-- 5.2. Записать метрики GA/Метрики
INSERT INTO content_metrics (content_item_id, date, views, reads, clicks, conversions, source, raw_data)
VALUES (
    101, '2026-03-03', 320, 210, 35, 0, 'ga4',
    '{"url": "...", "sessions": 280, "avg_engaged_time": 95}'
)
ON CONFLICT (content_item_id, date, source)
DO UPDATE SET views = EXCLUDED.views, reads = EXCLUDED.reads, clicks = EXCLUDED.clicks, raw_data = EXCLUDED.raw_data, created_at = now();

-- 5.3. Конверсии из CRM
INSERT INTO content_metrics (content_item_id, date, views, reads, clicks, conversions, source, raw_data)
VALUES (101, '2026-03-03', NULL, NULL, NULL, 4, 'crm', '{"leads": 4, "utm_campaign": "co2_sprint_march"}')
ON CONFLICT (content_item_id, date, source)
DO UPDATE SET conversions = EXCLUDED.conversions, raw_data = EXCLUDED.raw_data, created_at = now();

-- 5.4. Агрегат эффективности за 14 дней
WITH agg AS (
    SELECT
        cm.content_item_id,
        SUM(COALESCE(cm.views, 0)) FILTER (WHERE cm.source IN ('ga4','metrika')) AS total_views,
        SUM(COALESCE(cm.conversions, 0)) FILTER (WHERE cm.source = 'crm') AS total_conversions
    FROM content_metrics cm
    JOIN content_items ci ON ci.id = cm.content_item_id
    JOIN services s ON ci.service_id = s.id
    WHERE s.key = 'dry_co2_bath' AND cm.date >= (CURRENT_DATE - INTERVAL '14 day')
    GROUP BY cm.content_item_id
)
SELECT content_item_id, total_views, total_conversions,
       CASE WHEN total_views = 0 THEN 0 ELSE ROUND(total_conversions::numeric / total_views * 100, 2) END AS conv_rate_pct
FROM agg
ORDER BY conv_rate_pct DESC, total_conversions DESC;

-- 5.5. Обновить priority по результатам (топ-конвертеры = 3, есть заявки = 2, трафик = 1, нет = 0)
WITH agg AS (
    SELECT cm.content_item_id,
           SUM(COALESCE(cm.views, 0)) FILTER (WHERE cm.source IN ('ga4','metrika')) AS total_views,
           SUM(COALESCE(cm.conversions, 0)) FILTER (WHERE cm.source = 'crm') AS total_conversions
    FROM content_metrics cm
    GROUP BY cm.content_item_id
),
scores AS (
    SELECT content_item_id, total_views, total_conversions,
           CASE
               WHEN total_conversions >= 5 THEN 3
               WHEN total_conversions BETWEEN 1 AND 4 THEN 2
               WHEN total_views > 0 THEN 1
               ELSE 0
           END AS score
    FROM agg
)
UPDATE content_items ci
SET priority = scores.score, updated_at = now()
FROM scores WHERE ci.id = scores.content_item_id;

-- 5.6. Лог задачи Analyst
INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, input_ref, output_ref, finished_at)
VALUES ('analyst', NULL, 'recalculate_priorities', 'done', '{"period_days": 14}', '{"rule": "priority_by_conversions_and_views"}', now());
