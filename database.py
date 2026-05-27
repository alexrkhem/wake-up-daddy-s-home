import sqlite3
from pathlib import Path
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── TODOS ──────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        target_date DATE,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'todo',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── SLEEP ──────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS sleep_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL UNIQUE,
        bedtime TEXT,
        wake_time TEXT,
        duration_hours REAL,
        quality INTEGER,
        notes TEXT,
        routine_followed INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS sleep_routine (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        step_order INTEGER,
        activity TEXT NOT NULL,
        time_before_sleep TEXT,
        active INTEGER DEFAULT 1
    )""")

    # ── FITNESS ────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        location TEXT,
        name TEXT,
        duration_mins INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS workout_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_id INTEGER REFERENCES workouts(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        sets INTEGER,
        reps TEXT,
        weight_lbs REAL,
        notes TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS steps_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL UNIQUE,
        steps INTEGER,
        goal INTEGER DEFAULT 10000
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS physique_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        filepath TEXT,
        weight_lbs REAL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS supplements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dosage TEXT,
        timing TEXT,
        notes TEXT,
        active INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS supplement_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        supplement_id INTEGER REFERENCES supplements(id),
        taken INTEGER DEFAULT 0
    )""")

    # ── NUTRITION ──────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS nutrition_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL UNIQUE,
        calories REAL,
        protein_g REAL,
        carbs_g REAL,
        fat_g REAL,
        fiber_g REAL,
        source TEXT DEFAULT 'cronometer_csv',
        notes TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS eating_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meal_name TEXT NOT NULL,
        scheduled_time TEXT,
        description TEXT,
        approx_calories INTEGER,
        active INTEGER DEFAULT 1
    )""")

    # ── MUSIC ──────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS music_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        instrument TEXT NOT NULL,
        category TEXT NOT NULL,
        duration_mins INTEGER,
        notes TEXT,
        quality INTEGER,
        bpm_practiced INTEGER,
        piece_worked_on TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS music_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instrument TEXT,
        goal_text TEXT,
        target_date DATE,
        achieved INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── ACADEMICS ──────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT,
        semester TEXT,
        color TEXT DEFAULT '#d4681e',
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        course_id INTEGER REFERENCES courses(id),
        duration_mins INTEGER,
        topic TEXT,
        notes TEXT,
        productivity INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER REFERENCES courses(id),
        title TEXT NOT NULL,
        due_date DATE,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'todo',
        grade REAL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS textbooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER REFERENCES courses(id),
        title TEXT NOT NULL,
        filepath TEXT,
        vectorized INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── INVESTMENTS ────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS portfolio_holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account TEXT NOT NULL,
        symbol TEXT NOT NULL,
        shares REAL,
        avg_cost REAL,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS portfolio_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        account TEXT,
        symbol TEXT,
        transaction_type TEXT,
        shares REAL,
        price REAL,
        fees REAL DEFAULT 0,
        notes TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS cash_deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        account TEXT,
        amount REAL,
        notes TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE,
        target_price REAL,
        alert_price REAL,
        thesis TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS research_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        title TEXT,
        content TEXT,
        tags TEXT,
        thesis_tag TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── DESIGN PROJECTS ────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS design_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'active',
        start_date DATE,
        deadline DATE,
        tags TEXT,
        website_ready INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS project_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER REFERENCES design_projects(id) ON DELETE CASCADE,
        filename TEXT,
        filepath TEXT,
        file_type TEXT,
        notes TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS project_milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER REFERENCES design_projects(id) ON DELETE CASCADE,
        title TEXT,
        due_date DATE,
        status TEXT DEFAULT 'pending',
        notes TEXT
    )""")

    # ── JOURNAL & WINS ─────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        content TEXT,
        mood INTEGER,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS wins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        impact INTEGER DEFAULT 3,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS lessons_learned (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        lesson TEXT,
        context TEXT,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()
    _seed_defaults()

def _seed_defaults():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM sleep_routine")
    if c.fetchone()[0] == 0:
        routines = [
            (1, "No screens / blue-light glasses on", "60 mins before"),
            (2, "Dim all lights", "60 mins before"),
            (3, "Herbal tea (chamomile or valerian)", "45 mins before"),
            (4, "Read a physical book or journal", "30 mins before"),
            (5, "Light full-body stretch", "20 mins before"),
            (6, "Set out tomorrow's clothes & bag", "15 mins before"),
            (7, "Gratitude — write 3 things", "10 mins before"),
            (8, "Room temp 65-68°F, blackout curtains", "Bedtime setup"),
        ]
        c.executemany("INSERT INTO sleep_routine (step_order,activity,time_before_sleep) VALUES (?,?,?)", routines)

    c.execute("SELECT COUNT(*) FROM eating_schedule")
    if c.fetchone()[0] == 0:
        meals = [
            ("Breakfast", "7:30 AM", "High-protein start — eggs, Greek yogurt, oats", 550),
            ("Mid-Morning Snack", "10:30 AM", "Fruit + nuts or cottage cheese", 200),
            ("Lunch", "1:00 PM", "Balanced meal — lean protein, complex carbs, veggies", 700),
            ("Pre-Workout", "4:00 PM", "Fast carbs + protein — banana, protein shake", 350),
            ("Dinner", "7:00 PM", "Whole-food dinner — meat/fish, rice/potato, greens", 750),
            ("Evening Snack", "9:00 PM", "Optional — casein protein or Greek yogurt", 200),
        ]
        c.executemany("INSERT INTO eating_schedule (meal_name,scheduled_time,description,approx_calories) VALUES (?,?,?,?)", meals)

    c.execute("SELECT COUNT(*) FROM supplements")
    if c.fetchone()[0] == 0:
        supps = [
            ("Creatine Monohydrate", "5g", "post-workout", "Mix with water or shake"),
            ("Whey Protein", "1 scoop (~25g protein)", "post-workout", "Within 30 min post-session"),
            ("Vitamin D3 + K2", "5000 IU D3 / 100mcg K2", "morning", "Take with fat-containing meal"),
            ("Omega-3 Fish Oil", "2g EPA/DHA", "morning", "With breakfast"),
            ("Magnesium Glycinate", "400mg", "evening", "Improves sleep quality"),
            ("Zinc", "30mg", "evening", "Don't stack with calcium"),
            ("Caffeine + L-Theanine", "200mg / 400mg", "pre-workout", "Optional; skip after 2pm"),
        ]
        c.executemany("INSERT INTO supplements (name,dosage,timing,notes) VALUES (?,?,?,?)", supps)

    c.execute("SELECT COUNT(*) FROM watchlist")
    if c.fetchone()[0] == 0:
        watchlist = [
            ("HUBB", 400.0, 330.0, "fortress-america", "Hubbell — electrical grid infrastructure"),
            ("GEV", 550.0, 420.0, "fortress-america", "GE Vernova — domestic energy buildout"),
            ("VLO", 160.0, 120.0, "petrodollar", "Valero — domestic refining margin play"),
            ("CF", 90.0, 72.0, "fortress-america", "CF Industries — domestic nitrogen fertilizer"),
            ("PHYS", None, None, "petrodollar", "Physical gold trust — sovereign lifeboat"),
            ("PSLV", None, None, "petrodollar", "Physical silver trust"),
        ]
        c.executemany("INSERT INTO watchlist (symbol,target_price,alert_price,thesis,notes) VALUES (?,?,?,?,?)", watchlist)

    conn.commit()
    conn.close()
