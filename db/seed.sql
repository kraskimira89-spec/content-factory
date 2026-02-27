-- Начальные данные: каналы, рубрики (совпадают с agent_4_publish.RUBRICS), услуги
-- Выполнять после schema.sql

INSERT INTO channels (name, description) VALUES
    ('blog', 'Блог сайта (WordPress)'),
    ('vk', 'ВКонтакте'),
    ('instagram', 'Instagram'),
    ('email', 'Рассылка')
ON CONFLICT (name) DO NOTHING;

INSERT INTO rubrics (key, title) VALUES
    ('health_fitness', 'Здоровье и фитнес'),
    ('relax_massage', 'Релаксация и массаж'),
    ('nutrition_lifestyle', 'Питание и образ жизни'),
    ('client_stories', 'Истории клиентов'),
    ('ai_health', 'ИИ и здоровье')
ON CONFLICT (key) DO NOTHING;

INSERT INTO services (key, name, description) VALUES
    ('dry_co2_bath', 'Сухая углекислая ванна', NULL),
    ('cedar_barrel', 'Кедровая фитобочка', NULL),
    ('salt_room', 'Соляная комната', NULL),
    ('massage', 'Массаж', NULL),
    ('pressotherapy', 'Прессотерапия', NULL)
ON CONFLICT (key) DO NOTHING;
