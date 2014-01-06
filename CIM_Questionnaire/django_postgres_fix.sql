ALTER TABLE auth_permission DROP COLUMN name;
ALTER TABLE auth_permission ADD COLUMN name character varying(100);

