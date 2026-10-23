# Profile Updates (existing profile)

```markdown
# 👋 С возвращением, {name}!

У тебя уже есть профиль обучения.

Что хочешь сделать?

1. **Обновить профиль** — изменить цели, сроки или предпочтения
2. **Посмотреть текущий план** — расписание занятий
3. **Сбросить прогресс** — начать с нуля (⚠️ весь прогресс будет стёрт!)
4. **Отмена** — оставить всё как есть

**Напиши 1, 2, 3 или 4:**
```

- **1** — ask which field, update only that field, preserve the rest.
- **2** — render the plan section from current data. Read-only.
- **3** — confirm twice, naming the stakes («Будет стёрт весь прогресс: дней — X, сессий — Y, освоенных слов — Z. Продолжить? (yes/no)»). This deletes every file in the resolved data directory. Hooks do not fire here, so back up first:

  ```bash
  DATA_DIR="$(python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/ensure_data_dir.py")"
  TS="$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$DATA_DIR/.backups/pre-reset-$TS"
  cp "$DATA_DIR"/*.json "$DATA_DIR/.backups/pre-reset-$TS/"
  ```

  Then restart setup from §"Welcome".
- **4** — exit cleanly.
