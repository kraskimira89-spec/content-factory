# Агент Analyst: пересчёт приоритетов content_items по метрикам (views, conversions)
import os
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from logger import get_logger  # type: ignore

logger = get_logger("seo_agents.agent_analyst")

PERIOD_DAYS = 14  # за сколько дней агрегируем метрики


def recalculate_priorities() -> int | None:
    """
    Обновляет priority у content_items по content_metrics за последние PERIOD_DAYS дней.
    Правило: 3 = 5+ конверсий, 2 = 1–4 конверсии, 1 = есть трафик, 0 = нет.
    Возвращает число обновлённых строк или None при ошибке/недоступности БД.
    """
    try:
        from db import get_connection, is_available
    except ImportError:
        return None
    if not is_available():
        return None
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            WITH agg AS (
                SELECT
                    cm.content_item_id,
                    SUM(COALESCE(cm.views, 0)) FILTER (WHERE cm.source IN ('ga4', 'metrika')) AS total_views,
                    SUM(COALESCE(cm.conversions, 0)) FILTER (WHERE cm.source = 'crm') AS total_conversions
                FROM content_metrics cm
                WHERE cm.date >= CURRENT_DATE - %s * INTERVAL '1 day'
                GROUP BY cm.content_item_id
            ),
            scores AS (
                SELECT
                    content_item_id,
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
            FROM scores
            WHERE ci.id = scores.content_item_id
            """,
            (PERIOD_DAYS,),
        )
        updated = cur.rowcount
        cur.execute(
            """INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, input_ref, output_ref, finished_at)
               VALUES ('analyst', NULL, 'recalculate_priorities', 'done', %s, %s, now())""",
            (
                '{"period_days": ' + str(PERIOD_DAYS) + '}',
                '{"rule": "priority_by_conversions_and_views"}',
            ),
        )
        conn.commit()
        return updated
    finally:
        conn.close()


def main():
    print("=== Агент Analyst: пересчёт приоритетов по метрикам ===\n")

    updated = recalculate_priorities()
    if updated is None:
        print("БД недоступна. Пропуск.")
        logger.info("Analyst: БД недоступна")
        return
    print(f"Обновлено приоритетов: {updated}. Период: последние {PERIOD_DAYS} дней.")
    logger.info("Analyst: recalculate_priorities updated=%s", updated)


if __name__ == "__main__":
    main()
