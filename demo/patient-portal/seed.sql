-- Patient Portal demo seed.
-- 10 patients, 20 appointments, 5 medications, 4 users.
-- Run after sequelize.sync() has created the tables.

BEGIN;

TRUNCATE TABLE audit_log, medications, appointments, patients, users RESTART IDENTITY CASCADE;

INSERT INTO users (username, password_hash, role, email, "createdAt", "updatedAt") VALUES
  ('dr.kim',       '$2a$10$Cw0z6cD7e6tWlVGr1lCQ9.gsmt8wK0EQpO0jZbB1f5q3JpYjJrYku', 'doctor', 'kim@portal.example',       NOW(), NOW()),
  ('nurse.brown',  '$2a$10$Cw0z6cD7e6tWlVGr1lCQ9.gsmt8wK0EQpO0jZbB1f5q3JpYjJrYku', 'nurse',  'brown@portal.example',     NOW(), NOW()),
  ('p.sjohnson',   '$2a$10$Cw0z6cD7e6tWlVGr1lCQ9.gsmt8wK0EQpO0jZbB1f5q3JpYjJrYku', 'patient','sarah.j@example.com',      NOW(), NOW()),
  ('p.mchen',      '$2a$10$Cw0z6cD7e6tWlVGr1lCQ9.gsmt8wK0EQpO0jZbB1f5q3JpYjJrYku', 'patient','michael.chen@example.com', NOW(), NOW());

INSERT INTO patients (first_name, last_name, dob, ssn, mrn, diagnosis, insurance_id, phone, address, "createdAt", "updatedAt") VALUES
  ('Sarah',    'Johnson',   '1982-04-12', '123-45-6789', 'MRN-100001', 'Type 2 diabetes mellitus',                'BCBS-44781',  '+1-415-555-0142', '221 Lakeshore Dr, Oakland CA',     NOW(), NOW()),
  ('Michael',  'Chen',      '1975-11-03', '234-56-7890', 'MRN-100002', 'Essential hypertension',                  'AETNA-91230', '+1-415-555-0188', '88 Pine St, San Francisco CA',     NOW(), NOW()),
  ('Emily',    'Rodriguez', '1990-07-22', '345-67-8901', 'MRN-100003', 'Generalized anxiety disorder',            'KAISER-3382', '+1-510-555-0107', '410 Grand Ave, Berkeley CA',       NOW(), NOW()),
  ('David',    'Patel',     '1968-02-15', '456-78-9012', 'MRN-100004', 'Coronary artery disease',                 'UNITED-7782', '+1-650-555-0199', '15 Hillcrest Ln, San Mateo CA',    NOW(), NOW()),
  ('Jessica',  'Williams',  '1995-09-30', '567-89-0123', 'MRN-100005', 'Major depressive disorder, recurrent',    'BCBS-22119',  '+1-408-555-0166', '901 Park Ave, San Jose CA',        NOW(), NOW()),
  ('Robert',   'Garcia',    '1955-01-08', '678-90-1234', 'MRN-100006', 'COPD, mild',                              'MEDICARE-A1', '+1-707-555-0144', '17 Elm Ct, Santa Rosa CA',         NOW(), NOW()),
  ('Linda',    'Thompson',  '1960-06-19', '789-01-2345', 'MRN-100007', 'Osteoarthritis, bilateral knees',         'MEDICARE-A1', '+1-925-555-0173', '52 Vine St, Walnut Creek CA',      NOW(), NOW()),
  ('James',    'Nguyen',    '1988-12-04', '890-12-3456', 'MRN-100008', 'Asthma, moderate persistent',             'AETNA-44819', '+1-650-555-0121', '300 Bay Rd, Redwood City CA',      NOW(), NOW()),
  ('Maria',    'Martinez',  '1972-03-27', '901-23-4567', 'MRN-100009', 'Hypothyroidism',                          'KAISER-6601', '+1-415-555-0155', '78 Mission St, Daly City CA',      NOW(), NOW()),
  ('Daniel',   'Kim',       '1999-08-14', '012-34-5678', 'MRN-100010', 'Migraine without aura',                   'BCBS-99012',  '+1-510-555-0190', '120 Telegraph Ave, Berkeley CA',   NOW(), NOW());

INSERT INTO appointments (patient_id, provider, scheduled_for, reason, status, "createdAt", "updatedAt") VALUES
  (1,  'Dr. Kim',     '2026-05-20 09:00', 'Quarterly diabetes follow-up',    'scheduled', NOW(), NOW()),
  (1,  'Dr. Kim',     '2026-02-12 10:30', 'A1C review',                       'completed', NOW(), NOW()),
  (2,  'Dr. Patel',   '2026-05-22 14:00', 'BP medication review',             'scheduled', NOW(), NOW()),
  (2,  'Dr. Patel',   '2026-03-15 11:00', 'Annual physical',                  'completed', NOW(), NOW()),
  (3,  'Dr. Lee',     '2026-05-18 15:30', 'Therapy session',                  'scheduled', NOW(), NOW()),
  (3,  'Dr. Lee',     '2026-04-20 15:30', 'Therapy session',                  'completed', NOW(), NOW()),
  (4,  'Dr. Patel',   '2026-05-25 08:30', 'Cardiology consult',               'scheduled', NOW(), NOW()),
  (4,  'Dr. Patel',   '2026-01-10 08:30', 'Stress test follow-up',            'completed', NOW(), NOW()),
  (5,  'Dr. Lee',     '2026-05-30 13:00', 'Medication adjustment',            'scheduled', NOW(), NOW()),
  (5,  'Dr. Lee',     '2026-04-02 13:00', 'Therapy session',                  'no_show',   NOW(), NOW()),
  (6,  'Dr. Singh',   '2026-06-02 10:00', 'Pulmonary function test',          'scheduled', NOW(), NOW()),
  (6,  'Dr. Singh',   '2026-02-28 10:00', 'COPD checkup',                     'completed', NOW(), NOW()),
  (7,  'Dr. Kim',     '2026-06-05 11:30', 'Knee pain consult',                'scheduled', NOW(), NOW()),
  (7,  'Dr. Kim',     '2026-03-19 11:30', 'X-ray follow-up',                  'completed', NOW(), NOW()),
  (8,  'Dr. Singh',   '2026-06-08 09:30', 'Asthma action plan review',        'scheduled', NOW(), NOW()),
  (8,  'Dr. Singh',   '2026-01-25 09:30', 'New inhaler training',             'completed', NOW(), NOW()),
  (9,  'Dr. Kim',     '2026-06-10 14:30', 'TSH lab review',                   'scheduled', NOW(), NOW()),
  (9,  'Dr. Kim',     '2026-02-04 14:30', 'Med titration',                    'completed', NOW(), NOW()),
  (10, 'Dr. Lee',     '2026-06-12 16:00', 'Migraine pattern follow-up',       'scheduled', NOW(), NOW()),
  (10, 'Dr. Lee',     '2026-03-08 16:00', 'New patient intake',               'completed', NOW(), NOW());

INSERT INTO medications (patient_id, name, dosage, frequency, prescriber, status, started_at, "createdAt", "updatedAt") VALUES
  (1, 'Metformin',     '500 mg',  'twice daily',                'Dr. Kim',   'active', '2025-08-01', NOW(), NOW()),
  (2, 'Lisinopril',    '10 mg',   'once daily',                 'Dr. Patel', 'active', '2025-11-15', NOW(), NOW()),
  (4, 'Atorvastatin',  '40 mg',   'once daily at bedtime',      'Dr. Patel', 'active', '2024-12-10', NOW(), NOW()),
  (6, 'Tiotropium',    '18 mcg',  'one inhalation daily',       'Dr. Singh', 'active', '2025-09-05', NOW(), NOW()),
  (9, 'Levothyroxine', '75 mcg',  'once daily before breakfast','Dr. Kim',   'active', '2025-06-22', NOW(), NOW());

COMMIT;
