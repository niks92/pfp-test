-- Initialisation script run once when the Postgres container starts.
CREATE TABLE IF NOT EXISTS university_chapters (
    chapter_id   VARCHAR(20) PRIMARY KEY,
    chapter_name VARCHAR(255) NOT NULL,
    city         VARCHAR(100) NOT NULL,
    state        VARCHAR(2)   NOT NULL,
    longitude    DOUBLE PRECISION NOT NULL,
    latitude     DOUBLE PRECISION NOT NULL,
    updated_at   TIMESTAMP DEFAULT NOW()
);
