-- Create Roles
CREATE ROLE IF NOT EXISTS 'admin';
CREATE ROLE IF NOT EXISTS 'teacher';
CREATE ROLE IF NOT EXISTS 'coordinator';

-- Create Users
CREATE USER IF NOT EXISTS 'admin_user'@'localhost' IDENTIFIED BY 'admin_pass';
CREATE USER IF NOT EXISTS  'teacher_user'@'localhost' IDENTIFIED BY 'teacher_pass';
CREATE USER IF NOT EXISTS 'coordinator_user'@'localhost' IDENTIFIED BY 'coordinator_pass';

-- Assign roles
GRANT 'admin' TO 'admin_user'@'localhost';
GRANT 'teacher' TO 'teacher_user'@'localhost';
GRANT 'coordinator' TO 'coordinator_user'@'localhost';

SET DEFAULT ROLE 'admin' TO 'admin_user'@'localhost';
SET DEFAULT ROLE 'teacher' TO 'teacher_user'@'localhost';
SET DEFAULT ROLE 'coordinator' TO 'coordinator_user'@'localhost';

-- Grant privileges
-- Teacher privileges
GRANT SELECT ON School.Students TO 'teacher';
GRANT SELECT ON School.Teachers TO 'teacher';
GRANT SELECT ON School.Subjects TO 'teacher';
GRANT SELECT ON School.Classes TO 'teacher';
GRANT SELECT, INSERT, UPDATE ON School.Attendances TO 'teacher';
GRANT SELECT, INSERT, UPDATE ON School.Grades TO 'teacher';
GRANT EXECUTE ON PROCEDURE School.CheckClass TO 'teacher';
GRANT EXECUTE ON PROCEDURE School.GetClassRosterByName TO 'teacher';
GRANT EXECUTE ON PROCEDURE School.VerifyTeacherClassPair TO 'teacher';
GRANT CREATE VIEW ON school.* TO 'teacher';

-- Coordinator privileges
GRANT SELECT, INSERT, UPDATE ON School.Students TO 'coordinator';
GRANT SELECT ON School.Subjects TO 'coordinator';
GRANT SELECT ON School.Teachers TO 'coordinator';
GRANT SELECT ON School.Classes TO 'coordinator';
GRANT UPDATE (TeacherID) ON School.Classes TO 'coordinator';
GRANT SELECT ON School.Grades TO 'coordinator';
GRANT SELECT, INSERT, UPDATE ON School.Schedule TO 'coordinator';

-- Admin privileges
GRANT ALL PRIVILEGES ON School.* TO 'admin' WITH GRANT OPTION;
GRANT PROCESS ON *.* TO 'admin';
GRANT ALL PRIVILEGES ON *.* TO 'admin' WITH GRANT OPTION;

FLUSH PRIVILEGES;



