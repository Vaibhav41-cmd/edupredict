-- ═══════════════════════════════════════════════════════════════════════════
-- Student Pass/Fail Prediction System — MySQL Database Schema
-- Compatible with MySQL 8.0+ / MariaDB 10.6+
-- Run via XAMPP phpMyAdmin or: mysql -u root -p < database/schema.sql
-- ═══════════════════════════════════════════════════════════════════════════

-- Create & select database
CREATE DATABASE IF NOT EXISTS student_prediction_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE student_prediction_db;

-- ── 1. Admins ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admins (
  id            INT             AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(80)     NOT NULL,
  email         VARCHAR(120)    NOT NULL,
  password_hash VARCHAR(256)    NOT NULL,
  is_active     TINYINT(1)      NOT NULL DEFAULT 1,
  created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login    DATETIME        DEFAULT NULL,

  UNIQUE KEY uq_admins_username (username),
  UNIQUE KEY uq_admins_email    (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ── 2. Students ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
  id                    INT             AUTO_INCREMENT PRIMARY KEY,
  student_id            VARCHAR(20)     NOT NULL  COMMENT 'e.g. MCA2024001',
  name                  VARCHAR(100)    NOT NULL,
  email                 VARCHAR(120)    NOT NULL,
  department            VARCHAR(100)    NOT NULL,
  semester              TINYINT         NOT NULL,

  -- Subject marks (0–100)
  subject1_marks        DECIMAL(5,2)    NOT NULL,
  subject2_marks        DECIMAL(5,2)    NOT NULL,
  subject3_marks        DECIMAL(5,2)    NOT NULL,
  subject4_marks        DECIMAL(5,2)    NOT NULL,
  subject5_marks        DECIMAL(5,2)    NOT NULL,

  -- Other academic factors
  internal_marks        DECIMAL(5,2)    NOT NULL,
  attendance_pct        DECIMAL(5,2)    NOT NULL,
  study_hours_per_day   DECIMAL(4,2)    NOT NULL,
  assignments_submitted TINYINT         NOT NULL,
  previous_backlogs     TINYINT         NOT NULL DEFAULT 0,

  -- Timestamps
  created_at            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  UNIQUE KEY uq_students_student_id (student_id),
  UNIQUE KEY uq_students_email      (email),
  INDEX idx_students_department     (department),
  INDEX idx_students_semester       (semester)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ── 3. Prediction Logs ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prediction_logs (
  id               INT             AUTO_INCREMENT PRIMARY KEY,
  student_id       INT             NOT NULL,

  result           ENUM('PASS','FAIL') NOT NULL,
  pass_probability DECIMAL(6,5)    NOT NULL,
  fail_probability DECIMAL(6,5)    NOT NULL,

  model_name       VARCHAR(100)    NOT NULL,
  model_version    VARCHAR(50)     DEFAULT NULL,
  feature_snapshot JSON            DEFAULT NULL COMMENT 'Snapshot of inputs at prediction time',

  predicted_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_predlogs_student
    FOREIGN KEY (student_id) REFERENCES students(id)
    ON DELETE CASCADE ON UPDATE CASCADE,

  INDEX idx_predlogs_student_id   (student_id),
  INDEX idx_predlogs_result       (result),
  INDEX idx_predlogs_predicted_at (predicted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ── 4. Student Auth (for student self-service portal) ─────────────────────
CREATE TABLE IF NOT EXISTS student_auth (
  id               INT             AUTO_INCREMENT PRIMARY KEY,
  student_id       INT             NOT NULL,
  username         VARCHAR(50)     NOT NULL,
  password_hash    VARCHAR(256)    NOT NULL,
  is_active        TINYINT(1)      NOT NULL DEFAULT 1,
  last_login       DATETIME        DEFAULT NULL,
  created_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

  UNIQUE KEY uq_student_auth_username (username),
  UNIQUE KEY uq_student_auth_student (student_id),

  CONSTRAINT fk_student_auth_student
    FOREIGN KEY (student_id) REFERENCES students(id)
    ON DELETE CASCADE ON UPDATE CASCADE,

  INDEX idx_student_auth_student_id (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ═══════════════════════════════════════════════════════════════════════════
-- SAMPLE DATA (for development / demo)
-- ═══════════════════════════════════════════════════════════════════════════

-- Sample students
INSERT INTO students
  (student_id, name, email, department, semester,
   subject1_marks, subject2_marks, subject3_marks, subject4_marks, subject5_marks,
   internal_marks, attendance_pct, study_hours_per_day, assignments_submitted, previous_backlogs)
VALUES
  ('MCA2024001','Rahul Sharma',   'rahul@demo.com',   'MCA', 2, 78,82,75,88,71, 42, 88.5, 5.0, 9, 0),
  ('MCA2024002','Priya Patel',    'priya@demo.com',   'MCA', 2, 55,48,62,50,57, 28, 62.0, 2.5, 6, 2),
  ('MCA2024003','Arjun Mehta',    'arjun@demo.com',   'MCA', 4, 90,87,93,88,85, 48, 95.0, 7.0, 10, 0),
  ('MCA2024004','Sneha Joshi',    'sneha@demo.com',   'MCA', 2, 35,40,28,45,32, 18, 48.0, 1.5, 3, 4),
  ('MCA2024005','Vikram Nair',    'vikram@demo.com',  'MCA', 3, 68,72,65,70,74, 36, 78.0, 4.0, 7, 1),
  ('BCA2024001','Ananya Gupta',   'ananya@demo.com',  'BCA', 1, 82,79,85,80,88, 44, 91.0, 6.0, 10, 0),
  ('BCA2024002','Ravi Kumar',     'ravi@demo.com',    'BCA', 1, 42,38,44,40,36, 20, 55.0, 2.0, 4, 3),
  ('MCA2024006','Divya Singh',    'divya@demo.com',   'MCA', 2, 76,80,73,78,82, 40, 82.0, 5.5, 8, 0),
  ('MCA2024007','Karan Malhotra', 'karan@demo.com',   'MCA', 3, 28,32,35,30,25, 14, 42.0, 1.0, 2, 5),
  ('MCA2024008','Neha Verma',     'neha@demo.com',    'MCA', 2, 65,70,68,72,60, 34, 74.0, 3.5, 7, 1);


-- ═══════════════════════════════════════════════════════════════════════════
-- USEFUL QUERIES FOR REPORTING
-- ═══════════════════════════════════════════════════════════════════════════

-- Pass/Fail ratio
-- SELECT result, COUNT(*) AS count FROM prediction_logs GROUP BY result;

-- Average marks by department
-- SELECT s.department,
--        AVG((s.subject1_marks+s.subject2_marks+s.subject3_marks+s.subject4_marks+s.subject5_marks)/5) AS avg_marks,
--        COUNT(*) AS students
-- FROM students s GROUP BY s.department ORDER BY avg_marks DESC;

-- Students at risk (attendance < 75% OR avg marks < 50)
-- SELECT student_id, name, attendance_pct,
--   (subject1_marks+subject2_marks+subject3_marks+subject4_marks+subject5_marks)/5 AS avg_marks
-- FROM students
-- WHERE attendance_pct < 75
--    OR (subject1_marks+subject2_marks+subject3_marks+subject4_marks+subject5_marks)/5 < 50
-- ORDER BY avg_marks ASC;
