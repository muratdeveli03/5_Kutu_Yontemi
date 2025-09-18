-- Öğrenci tablosu
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT,
    class INTEGER
);

-- Kelime tablosu
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class INTEGER,
    english TEXT,
    turkish TEXT
);

-- Öğrenci ilerleme tablosu
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    word_id INTEGER,
    box INTEGER DEFAULT 1,
    last_review DATE DEFAULT CURRENT_DATE,
    UNIQUE(student_id, word_id)
);
