SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE DATABASE IF NOT EXISTS chatbot_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE chatbot_db;

CREATE TABLE IF NOT EXISTS users (
  user_id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  mail VARCHAR(255) NOT NULL,
  user_type ENUM('admin','employee') NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY mail (mail)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS admins (
  admin_id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  PRIMARY KEY (admin_id),
  UNIQUE KEY user_id (user_id),
  CONSTRAINT admins_ibfk_1
    FOREIGN KEY (user_id)
    REFERENCES users (user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS admin_accounts (
  admin_acc_id INT NOT NULL AUTO_INCREMENT,
  admin_id INT NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (admin_acc_id),
  UNIQUE KEY admin_id (admin_id),
  CONSTRAINT admin_accounts_ibfk_1
    FOREIGN KEY (admin_id)
    REFERENCES admins (admin_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS employees (
  emp_id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  role VARCHAR(100) DEFAULT NULL,
  start_date DATE DEFAULT NULL,
  salary DECIMAL(10,2) DEFAULT NULL,
  leave_work_days INT DEFAULT 0,
  department VARCHAR(100) DEFAULT NULL,
  gender VARCHAR(20) DEFAULT NULL,
  PRIMARY KEY (emp_id),
  UNIQUE KEY user_id (user_id),
  CONSTRAINT employees_ibfk_1
    FOREIGN KEY (user_id)
    REFERENCES users (user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS employee_accounts (
  acc_id INT NOT NULL AUTO_INCREMENT,
  emp_id INT NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (acc_id),
  UNIQUE KEY emp_id (emp_id),
  CONSTRAINT employee_accounts_ibfk_1
    FOREIGN KEY (emp_id)
    REFERENCES employees (emp_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS chats (
  chat_id INT NOT NULL AUTO_INCREMENT,
  acc_id INT NOT NULL,
  title VARCHAR(255) DEFAULT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (chat_id),
  KEY acc_id (acc_id),
  CONSTRAINT chats_ibfk_1
    FOREIGN KEY (acc_id)
    REFERENCES employee_accounts (acc_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS chat_messages (
  message_id INT NOT NULL AUTO_INCREMENT,
  chat_id INT NOT NULL,
  sender_role ENUM('user','assistant','system') NOT NULL,
  message_text TEXT NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (message_id),
  KEY chat_id (chat_id),
  CONSTRAINT chat_messages_ibfk_1
    FOREIGN KEY (chat_id)
    REFERENCES chats (chat_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS chatbot_categories (
  category_key VARCHAR(50) NOT NULL,
  category_name VARCHAR(100) NOT NULL,
  description TEXT,
  is_enabled TINYINT(1) NOT NULL DEFAULT 1,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (category_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS documents (
  doc_id INT NOT NULL AUTO_INCREMENT,
  doc_name VARCHAR(255) NOT NULL,
  doc_category VARCHAR(100) DEFAULT NULL,
  file_path VARCHAR(500) DEFAULT NULL,
  uploaded_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (doc_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS uploads (
  upload_id INT NOT NULL AUTO_INCREMENT,
  admin_acc_id INT NOT NULL,
  doc_id INT NOT NULL,
  timestamp TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (upload_id),
  KEY admin_acc_id (admin_acc_id),
  KEY doc_id (doc_id),
  CONSTRAINT uploads_ibfk_1
    FOREIGN KEY (admin_acc_id)
    REFERENCES admin_accounts (admin_acc_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT uploads_ibfk_2
    FOREIGN KEY (doc_id)
    REFERENCES documents (doc_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


INSERT INTO users (user_id, name, mail, user_type, created_at)
VALUES
  (1, 'Tarik', 'tarik@siro.com', 'employee', '2026-04-30 00:18:04'),
  (2, 'Ahmet Yilmaz', 'ahmet.yilmaz@siro.com', 'employee', '2026-05-01 09:00:00'),
  (3, 'Ayse Demir', 'ayse.demir@siro.com', 'employee', '2026-05-01 09:05:00'),

  (4, 'Tarik Admin', 'tarik@admin.com', 'admin', '2026-04-30 00:42:01'),
  (5, 'HR Admin', 'hr.admin@siro.com', 'admin', '2026-05-01 09:15:00')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  mail = VALUES(mail),
  user_type = VALUES(user_type);


INSERT INTO admins (admin_id, user_id)
VALUES
  (1, 4),
  (2, 5)
ON DUPLICATE KEY UPDATE
  user_id = VALUES(user_id);


INSERT INTO admin_accounts (admin_acc_id, admin_id, password_hash, created_at)
VALUES
  -- tarik@admin.com password: 123456
  (1, 1, '$2b$12$W7jdJ9w2utqKFyxmqC5/g.1TQwxo69OtsuKzVSOGijjZEKpnQudMa', '2026-04-30 00:43:06'),

  -- hr.admin@siro.com password: 1234567
  (2, 2, '$2b$12$LWflkXtYGEveANCbrEFDbO9lCX6eLQl5u8FxZze4onThfszLlAAZ.', '2026-05-01 09:25:00')
ON DUPLICATE KEY UPDATE
  admin_id = VALUES(admin_id),
  password_hash = VALUES(password_hash);


INSERT INTO employees
  (emp_id, user_id, role, start_date, salary, leave_work_days, department, gender)
VALUES
  (1, 1, 'Engineer', NULL, NULL, 0, 'IT', NULL),
  (2, 2, 'Software Engineer', '2025-01-15', NULL, 0, 'IT', 'Male'),
  (3, 3, 'HR Specialist', '2024-09-01', NULL, 0, 'Human Resources', 'Female')
ON DUPLICATE KEY UPDATE
  user_id = VALUES(user_id),
  role = VALUES(role),
  start_date = VALUES(start_date),
  salary = VALUES(salary),
  leave_work_days = VALUES(leave_work_days),
  department = VALUES(department),
  gender = VALUES(gender);


INSERT INTO employee_accounts (acc_id, emp_id, created_at)
VALUES
  (1, 1, '2026-04-30 00:19:07'),
  (2, 2, '2026-05-01 09:35:00'),
  (3, 3, '2026-05-01 09:40:00')
ON DUPLICATE KEY UPDATE
  emp_id = VALUES(emp_id);


INSERT INTO chatbot_categories
  (category_key, category_name, description, is_enabled, updated_at)
VALUES
  ('benefits', 'Yan Haklar', 'Servis, yemek, özel sağlık sigortası, yan haklar ve sosyal haklar.', 1, '2026-04-30 00:08:07'),
  ('company_policies', 'Şirket Politikaları', 'Genel şirket kuralları, prosedürler ve politikalar.', 1, '2026-04-30 00:08:07'),
  ('discipline', 'Disiplin', 'Disiplin süreçleri, uyarılar ve yaptırımlar.', 0, '2026-04-30 00:08:07'),
  ('health_safety', 'Sağlık ve Güvenlik', 'İş sağlığı, güvenliği, kaza, sağlık raporu ve güvenlik kuralları.', 0, '2026-04-30 01:08:01'),
  ('leaves', 'İzinler', 'Yıllık izin, doğum izni, hastalık izni, mazeret izni gibi konular.', 0, '2026-04-30 00:58:32'),
  ('other', 'Diğer', 'Belirsiz veya mevcut kategorilere girmeyen sorular.', 0, '2026-04-30 00:08:07'),
  ('payroll', 'Maaş ve Bordro', 'Maaş, bordro, ödeme, prim, ücret ve kesintiler.', 0, '2026-04-30 00:08:07'),
  ('performance', 'Performans', 'Performans değerlendirme, hedefler ve geri bildirim süreçleri.', 1, '2026-04-30 00:08:07'),
  ('recruitment', 'İşe Alım', 'İşe alım, başvuru, mülakat ve aday süreçleri.', 1, '2026-04-30 00:56:51'),
  ('training', 'Eğitim', 'Çalışan eğitimleri, gelişim programları ve zorunlu eğitimler.', 1, '2026-04-30 00:08:07')
ON DUPLICATE KEY UPDATE
  category_name = VALUES(category_name),
  description = VALUES(description),
  is_enabled = VALUES(is_enabled),
  updated_at = VALUES(updated_at);