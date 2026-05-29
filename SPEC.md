# Piano Performance Analyzer — SPEC

Приложение для сравнения записанной игры пользователя с эталонным MIDI.
Сравнение по pitch и timing с использованием tolerance threshold.

## Features
- Загрузка audio recording и reference MIDI
- Автоматический анализ и сравнение нот
- Визуальная подсветка клавиш: missed / wrong / late notes
- Real-time подсветка нот с микрофона (бонус)

## Flow
1. Пользователь загружает audio recording (.wav/.mp3)
2. Пользователь загружает reference MIDI (.mid)
3. Бэкенд обрабатывает оба файла и приводит к общему формату:
   - MIDI: PrettyMIDI извлекает ноты, переводит тики в секунды (тики / PPQ / BPM * 60)
   - Audio: Basic Pitch извлекает ноты с таймингами в секундах
4. Сравнение нот по pitch и timing через tolerance threshold
5. Результат: missed / wrong / late notes → JSON → фронтенд
6. Фронтенд подсвечивает клавиши согласно результату

## Tech Stack
**Backend (Python)**
- FastAPI — HTTP сервер
- PrettyMIDI — парсинг MIDI
- Basic Pitch (Spotify) — audio → ноты

**Frontend**
- React — UI + piano keyboard
- Web Audio API + Pitchfinder — real-time подсветка с микрофона

## Tolerance Threshold
- Pitch: ±0.5 полутона (четверть тона)
- Timing: ±100ms

## Playback Mode
- Кнопка Play запускает воспроизведение audio файла
- requestAnimationFrame двигает current_time синхронно с аудио
- На каждом кадре: найти ноты где start <= current_time <= end
- Подсветить клавиши: зелёный = correct, красный = wrong
- По завершении — показать итоговую статистику