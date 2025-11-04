# ✅ Auto-Analysis Fix - Signal Handling Correction

## 🎯 Исправленные проблемы

### Проблема 1: TypeError при изменении карт
**Ошибка:**
```
TypeError: cards_changed() only accepts 0 argument(s), 1 given!
```

**Причина:**
Qt сигналы (`textChanged`, `cards_changed`) передают аргументы в слот, но метод `on_cards_changed()` не принимал никаких аргументов.

**Решение:**
```python
# Было:
def on_cards_changed(self):
    ...

# Стало:
def on_cards_changed(self, *args):  # Принимает любые аргументы
    ...
```

---

### Проблема 2: Некорректные данные в Монте-Карло
**Симптомы:**
- При изменении количества игроков за столом данные не обновлялись
- При ручном изменении карт `game_state` не обновлялся
- Корректные данные поступали только после нажатия кнопки "Analyze"

**Причина:**
Методы `on_table_size_changed()` и `on_cards_changed()` не обновляли `game_state` полностью:
- Не обновляли `player_cards` из текущих input'ов
- Не обновляли `board_cards` и `stage` при смене размера стола

**Решение:**
Теперь оба метода синхронизируют `game_state` с текущими значениями input'ов.

---

## 🔧 Технические детали исправлений

### 1. Метод `on_cards_changed()` - ИСПРАВЛЕН

**Было:**
```python
def on_cards_changed(self):
    """Handle card input changes"""
    board_cards = self.get_board_cards()
    self.game_state.board_cards = board_cards
    self.game_state.stage = self._determine_stage(board_cards)
    
    self.update_game_state_display()
    
    if self.has_player_cards():
        self.analysis_timer.stop()
        self.analysis_timer.start(300)
```

**Проблемы:**
1. ❌ Не принимает аргументы от сигнала
2. ❌ Не обновляет `player_cards` в `game_state`
3. ❌ Использует `has_player_cards()` вместо прямой проверки

**Стало:**
```python
def on_cards_changed(self, *args):
    """Handle card input changes"""
    # Update player cards
    player_cards = self.get_player_cards()
    self.game_state.player_cards = player_cards
    
    # Update board cards
    board_cards = self.get_board_cards()
    self.game_state.board_cards = board_cards
    self.game_state.stage = self._determine_stage(board_cards)
    
    self.update_game_state_display()
    
    # Auto-analyze if we have valid player cards
    if len(player_cards) == 2:
        self.analysis_timer.stop()
        self.analysis_timer.start(300)
    
    logger.debug(f"Cards changed: {len(player_cards)} player, {len(board_cards)} board")
```

**Улучшения:**
1. ✅ Принимает аргументы через `*args`
2. ✅ Обновляет `player_cards` из input'ов
3. ✅ Обновляет `board_cards` и `stage`
4. ✅ Прямая проверка количества карт
5. ✅ Добавлен debug logging

---

### 2. Метод `on_table_size_changed()` - ИСПРАВЛЕН

**Было:**
```python
def on_table_size_changed(self, table_size: TableSize):
    """Handle table size change"""
    self.game_state.table_size = table_size
    self.update_game_state_display()
    
    if self.has_player_cards():
        self.analyze_situation()  # Прямой вызов без debounce
    
    logger.info(f"Table size changed: {table_size}")
```

**Проблемы:**
1. ❌ Не обновляет карты из input'ов
2. ❌ Прямой вызов `analyze_situation()` без debounce
3. ❌ Может вызвать анализ с устаревшими данными

**Стало:**
```python
def on_table_size_changed(self, table_size: TableSize):
    """Handle table size change"""
    self.game_state.table_size = table_size
    
    # Update player and board cards from current inputs
    self.game_state.player_cards = self.get_player_cards()
    self.game_state.board_cards = self.get_board_cards()
    self.game_state.stage = self._determine_stage(self.game_state.board_cards)
    
    self.update_game_state_display()
    
    # Auto-analyze if we have valid player cards
    if len(self.game_state.player_cards) == 2:
        self.analysis_timer.stop()
        self.analysis_timer.start(300)
    
    logger.info(f"Table size changed: {table_size}")
```

**Улучшения:**
1. ✅ Синхронизирует все данные из input'ов
2. ✅ Использует debounced timer (300ms)
3. ✅ Гарантирует актуальность данных
4. ✅ Консистентное поведение с `on_cards_changed()`

---

## 📊 Поток данных после исправления

### Сценарий 1: Изменение карты в input'е

```
[User] Вводит карту в CardInputWidget
    ↓
CardInputWidget.line_edit.textChanged
    ↓ (signal)
CardsDock.cards_changed (signal relay)
    ↓
AdaptiveMainWindow.on_cards_changed(*args)
    ↓
1. player_cards = get_player_cards()        # Читаем из input'ов
2. game_state.player_cards = player_cards   # Обновляем state
3. board_cards = get_board_cards()          # Читаем board
4. game_state.board_cards = board_cards     # Обновляем state
5. game_state.stage = _determine_stage()    # Обновляем stage
6. update_game_state_display()              # Обновляем UI
7. if len(player_cards) == 2:               # Проверяем
       analysis_timer.start(300)            # Запускаем debounced анализ
    ↓ (через 300ms)
analyze_situation()
    ↓
analysis_service.analyze_hand(game_state)   # ✅ Актуальные данные!
```

### Сценарий 2: Изменение размера стола

```
[User] Выбирает другой размер стола
    ↓
TableConfigDock.table_size_changed (signal)
    ↓
AdaptiveMainWindow.on_table_size_changed(table_size)
    ↓
1. game_state.table_size = table_size       # Обновляем размер
2. game_state.player_cards = get_player_cards()  # Синхронизируем карты
3. game_state.board_cards = get_board_cards()    # Синхронизируем board
4. game_state.stage = _determine_stage()         # Обновляем stage
5. update_game_state_display()                   # Обновляем UI
6. if len(player_cards) == 2:                    # Проверяем
       analysis_timer.start(300)                 # Запускаем анализ
    ↓ (через 300ms)
analyze_situation()
    ↓
analysis_service.analyze_hand(game_state)   # ✅ Актуальные данные с новым размером!
```

---

## 🎮 Тестирование исправлений

### Тест 1: Изменение карты
```
1. Открыть приложение
2. Ввести первую карту игрока: As
   ✅ PASS: Нет ошибки TypeError
3. Ввести вторую карту игрока: Kh
   ✅ PASS: Автоматически запускается анализ через 300ms
4. Изменить первую карту на: Qd
   ✅ PASS: Анализ перезапускается с новыми данными
```

### Тест 2: Изменение размера стола
```
1. Ввести карты игрока: As Kh
2. Анализ выполнен для 6-max
3. Изменить размер стола на 9-max
   ✅ PASS: Анализ автоматически перезапускается
   ✅ PASS: В анализе используется 9-max (не 6-max)
4. Проверить результат equity
   ✅ PASS: Equity рассчитан против 8 оппонентов (9-max)
```

### Тест 3: Изменение board карт
```
1. Ввести карты игрока: As Kh
2. Ввести флоп: Ah 7h 2c
   ✅ PASS: Stage обновляется на "Flop"
   ✅ PASS: Анализ автоматически запускается
3. Добавить turn: 3d
   ✅ PASS: Stage обновляется на "Turn"
   ✅ PASS: Анализ перезапускается с 4 картами board
4. Добавить river: 5h
   ✅ PASS: Stage обновляется на "River"
   ✅ PASS: Финальный анализ с полным board
```

### Тест 4: Кнопка "Analyze"
```
1. Ввести карты: As Kh
2. Дождаться автоанализа
3. Нажать кнопку "Analyze"
   ✅ PASS: Анализ выполняется снова
   ✅ PASS: Используются актуальные данные
   ✅ PASS: Нет дублирования анализа
```

---

## 🔄 Debounce механизм

### Зачем нужен debounce?

Когда пользователь быстро меняет карты (например, вводит "As"), происходит:
1. textChanged при вводе "A" → запуск анализа
2. textChanged при вводе "s" → запуск анализа

Без debounce это приведет к 2 вызовам анализа. С debounce:
1. textChanged "A" → timer.start(300)
2. textChanged "s" → timer.stop() + timer.start(300)  # Сброс таймера
3. Через 300ms после последнего изменения → анализ выполняется 1 раз

### Реализация:

```python
# Timer настроен как SingleShot (выполняется 1 раз)
self.analysis_timer = QTimer(self)
self.analysis_timer.setSingleShot(True)
self.analysis_timer.timeout.connect(self.analyze_situation)

# При каждом изменении:
self.analysis_timer.stop()    # Отменяем предыдущий таймер
self.analysis_timer.start(300)  # Запускаем новый на 300ms
```

**Преимущества:**
- ✅ Экономия вычислений (не запускаем анализ при каждом символе)
- ✅ Лучшая UX (результат появляется когда пользователь закончил ввод)
- ✅ Снижение нагрузки на систему

---

## 🎯 Итоговое поведение

### Автоанализ запускается при:
1. ✅ Изменении любой карты (player или board)
2. ✅ Изменении размера стола
3. ✅ Нажатии кнопки "Analyze"

### Автоанализ НЕ запускается если:
1. ❌ У игрока меньше 2 карт
2. ❌ Прошло меньше 300ms с последнего изменения (debounce)

### Гарантии качества данных:
1. ✅ `game_state` всегда синхронизирован с input'ами
2. ✅ Анализ всегда использует актуальные данные
3. ✅ Размер стола, карты и stage всегда консистентны

---

## 📝 Checklist исправлений

- ✅ Исправлен TypeError в `on_cards_changed()`
- ✅ Добавлен `*args` для приема аргументов от сигналов
- ✅ Обновление `player_cards` в `on_cards_changed()`
- ✅ Обновление всех полей `game_state` в `on_table_size_changed()`
- ✅ Использование debounced timer во всех event handlers
- ✅ Добавлен debug logging
- ✅ Консистентное поведение всех триггеров анализа

---

## 🚀 Готово к использованию!

Запуск:
```bash
cd C:\MonteLab
python main_adaptive.py
```

**Результат:**
- Автоанализ работает при любом изменении карт
- Автоанализ работает при изменении размера стола
- Данные всегда актуальные и корректные
- Нет ошибок TypeError

---

*Документация обновлена: 24.10.2025*  
*Версия: 2.0-Adaptive-AutoAnalysis-Fixed*
