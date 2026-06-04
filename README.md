[security-architecture.md](https://github.com/user-attachments/files/28576294/security-architecture.md)
# Блок-схема SecurityMonitor

Десктопное приложение мониторинга безопасности: сканирование файлов, процессы, сеть. Управление через главный цикл и действия пользователя.

## Общий поток

```mermaid
flowchart TB
    START(["Запуск программы"])
    INIT["ИНИЦИАЛИЗАЦИЯ"]
    LOOP["Главный цикл программы"]
    ACTION{"Действие пользователя"}

    START --> INIT
    INIT --> LOOP
    LOOP --> ACTION
    ACTION --> LOOP
```

## Инициализация

```mermaid
flowchart TB
    subgraph INIT["ИНИЦИАЛИЗАЦИЯ"]
        I1["Инициализация SecurityMonitor"]
        I2["Создание интерфейса init_ui"]
        I3["Создание заголовка"]
        I4["Создание вкладок"]
        I5["Вкладка Дашборд"]
        I6["Вкладка Сканер файлов"]
        I7["Вкладка Процессы"]
        I8["Вкладка Сеть"]
    end

    I1 --> I2 --> I3 --> I4
    I4 --> I5
    I4 --> I6
    I4 --> I7
    I4 --> I8
```

## Действия пользователя

Из главного цикла доступны следующие ветки:

```mermaid
flowchart LR
    ACTION{"Действие<br/>пользователя"}

    ACTION -->|"Быстрое сканирование"| QS["quick_scan_action"]
    ACTION -->|"Полное сканирование"| FS["full_scan_action"]
    ACTION -->|"Обновить всё"| UA["update_all_data"]
    ACTION -->|"Обновить процессы"| UP["update_processes"]
    ACTION -->|"Обновить сеть"| UN["update_network"]
    ACTION -->|"Очистить результаты"| CR["clear_scan_results"]
    ACTION -->|"Экспорт CSV"| EX["export_scan_results"]
    ACTION -->|"Выбор пути"| BP["browse_path"]
    ACTION -->|"Закрытие"| CL["on_closing"]
```

## Сканер файлов — быстрое сканирование

```mermaid
flowchart TB
    subgraph SCAN["СКАНЕР ФАЙЛОВ"]
        QS["quick_scan_action"]
        PATH["Получить путь"]
        SCAN_CALL["file_scanner.quick_scan"]
        WALK["os.walk по директории"]
        EXT{"Расширение в<br/>suspicious_extensions?"}
        ADD["Добавить угрозу"]
        SKIP["Пропустить"]
        SEEN{"Файл уже<br/>сканировался?"}
        SAVE["Сохранить угрозу"]
        STAT["Обновить статистику"]
        UPD["update_scan_results"]
        TABLE["Показать угрозы в таблице"]
        MSG["Показать сообщение с результатами"]
        UA["update_all_data"]
    end

    QS --> PATH
    QS --> SCAN_CALL
    SCAN_CALL --> WALK --> EXT
    EXT -->|Да| ADD --> SEEN
    EXT -->|Нет| SKIP
    SEEN -->|Нет| SAVE --> STAT
    SEEN -->|Да| SKIP
    STAT --> UPD --> TABLE --> MSG
    QS --> UA
```

## Сканер файлов — полное сканирование

```mermaid
flowchart TB
    FS["full_scan_action"]
    DIRS["Список директорий"]
    LOOP["Цикл по директориям"]
    CALL["Вызов quick_scan"]
    COLLECT["Сбор всех угроз"]
    UPDATE["Обновить результаты"]
    UA["update_all_data"]

    FS --> DIRS --> LOOP --> CALL --> COLLECT --> UPDATE
    FS --> UA
```

## update_all_data

```mermaid
flowchart TB
    UA["update_all_data"]
    UP["update_processes"]
    UN["update_network"]
    US["update_stats_display"]
    ACT["update_activity"]
    LOOP["Главный цикл программы"]

    UA --> UP
    UA --> UN
    UA --> US
    UA --> ACT
    US --> LABELS["Обновить метки stats_labels"]
    UA --> LOOP
```

## Монитор процессов

```mermaid
flowchart TB
    subgraph PROC["МОНИТОР ПРОЦЕССОВ"]
        UP["update_processes"]
        GET["process_monitor.get_processes"]
        PS["psutil.process_iter"]
        PARSE["Парсинг информации"]
        CLEAR["Очистить таблицу"]
        INSERT["Вставить процессы в таблицу"]
        STAT["Обновить статистику"]
    end

    UP --> GET --> PS --> PARSE --> CLEAR --> INSERT --> STAT
```

## Сетевой монитор

```mermaid
flowchart TB
    subgraph NET["СЕТЕВОЙ МОНИТОР"]
        UN["update_network"]
        GET["network_monitor.get_connections"]
        PS["psutil.net_connections"]
        PARSE["Парсинг соединений"]
        CLEAR["Очистить таблицу"]
        INSERT["Вставить соединения в таблицу"]
        STAT["Обновить статистику"]
    end

    UN --> GET --> PS --> PARSE --> CLEAR --> INSERT --> STAT
```

## Экспорт результатов (CSV)

```mermaid
flowchart TB
    EX["export_scan_results"]
    CHECK{"Есть данные<br/>для экспорта?"}
    ERR["Показать сообщение об ошибке"]
    PICK["Выбрать файл CSV"]
    WRITE["Записать данные в CSV"]
    OK["Сообщение об успехе"]

    EX --> CHECK
    CHECK -->|Нет| ERR
    CHECK -->|Да| PICK --> WRITE --> OK
```

## Очистка результатов

```mermaid
flowchart TB
    CR["clear_scan_results"]
    CONF{"Пользователь<br/>подтвердил?"}
    CANCEL["Отмена"]
    T1["Очистить таблицу"]
    T2["Очистить scan_results"]
    T3["Очистить unique_files_scanned"]
    T4["Сбросить статистику в 0"]
    MSG["Сообщение об очистке"]

    CR --> CONF
    CONF -->|Нет| CANCEL
    CONF -->|Да| T1 --> T2 --> T3 --> T4 --> MSG
```

## Прочие действия

```mermaid
flowchart LR
    BP["browse_path"] --> SET["Установить путь в scan_path_var"]
    CL["on_closing"] --> DEST["root.destroy"]
```

## Модули и функции

| Модуль | Ключевые функции | Зависимости |
|--------|------------------|-------------|
| **Инициализация** | `SecurityMonitor`, `init_ui` | Tkinter |
| **Сканер файлов** | `quick_scan_action`, `full_scan_action`, `file_scanner.quick_scan` | `os.walk`, `suspicious_extensions` |
| **Монитор процессов** | `update_processes`, `process_monitor.get_processes` | `psutil.process_iter` |
| **Сетевой монитор** | `update_network`, `network_monitor.get_connections` | `psutil.net_connections` |
| **Дашборд** | `update_all_data`, `update_stats_display`, `update_activity` | — |
| **Экспорт** | `export_scan_results` | CSV |
| **Очистка** | `clear_scan_results` | — |

## Вкладки интерфейса

| Вкладка | Назначение |
|---------|------------|
| **Дашборд** | Сводная статистика и активность |
| **Сканер файлов** | Быстрое и полное сканирование, выбор пути |
| **Процессы** | Список запущенных процессов |
| **Сеть** | Активные сетевые соединения |
