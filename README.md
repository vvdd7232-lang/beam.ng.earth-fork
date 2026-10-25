# BeamNG.Earth — standalone fork

Форк [tecnagamer/beamng.earth](https://github.com/tecnagamer/beamng.earth), исходный снимок
`f8e7a774042ea53832e570d6474da2af890d91cf` (MIT; авторство сохранено в LICENSE/CREDITS.md).

Лаунчер не использует Steam: нет запуска через URI, поиска библиотек/Proton-префиксов,
оверлея, Steam Runtime или проверки клиента. Игра запускается напрямую.
Это изменение мода, **не обход защиты игры**: файлы BeamNG.drive не изменяются и не входят в сборку.
Если конкретная сборка игры сама требует клиент, этот форк этого не меняет.

## Сборка на Windows 10/11 x64

1. Установите **Python 3.12 x64** с Python Launcher (`py`).
2. Скачайте исходники и запустите `build_windows.bat` из cmd или двойным щелчком.
3. Готовый файл: `dist\BeamNG.Earth-<VERSION>.exe`.

Скрипт создаёт отдельное окружение `.venv-build`, устанавливает зависимости,
упаковывает мод, сервер и Python через PyInstaller и проверяет запуск сервера с `--help`.
Нужен интернет для установки пакетов. Компилятор для обычной сборки не нужен.
Дополнительно: `build_windows.bat --native` собирает ускоряющий Rust-модуль
(нужны Rust stable x64 и Visual Studio Build Tools с C++ и Windows SDK).
Без него используется Python-реализация. Используется стандартный загрузчик PyInstaller;
возможны ложные срабатывания антивируса, подписи издателя нет.

## Запуск

```bat
"dist\BeamNG.Earth-<VERSION>.exe" --game-dir "D:\Games\BeamNG.drive"
```

Укажите корень установки с `BeamNG.drive.exe`. Без `--game-dir` Windows проверяет
`installPath` в `%LOCALAPPDATA%\BeamNG\BeamNG.drive.ini` и ключ реестра самой BeamNG.
Альтернатива — переменная окружения `BNGE_GAME_DIR`.

Нестандартная папка пользовательских данных:

```bat
"dist\BeamNG.Earth-<VERSION>.exe" --game-dir "D:\Games\BeamNG.drive" --user-dir "D:\BeamNGUser\current"
```

Первый раз запустите игру, чтобы она создала пользовательскую папку.
Затем выберите **Freeroam → BeamNG.Earth**. Карта требует интернета для загрузки данных.
`--no-game` запускает только сервер; игру можно открыть самостоятельно.
`--gfx dx11`, `--gfx dx12`, `--gfx vk` выбирают рендерер.
Закрытие игры останавливает сервер; также можно нажать Ctrl+C.
Steam Input/оверлей, автоматический Proton и sandbox-запуск больше не поддерживаются.
Linux: `python launcher.py --game-dir /path/to/BeamNG.drive` (нативная версия).

Исходная документация: [docs/UPSTREAM_README.md](docs/UPSTREAM_README.md).
Она и CHANGELOG/research описывают upstream и могут упоминать удалённые возможности.
