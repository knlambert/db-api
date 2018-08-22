\c postgres


DROP DATABASE IF EXISTS app_tenant_1;
DROP DATABASE IF EXISTS app_tenant_2;

CREATE DATABASE app_tenant_1;
\c app_tenant_1;
\i schema.sql;
\i values/values_1.sql;

CREATE DATABASE app_tenant_2;
\c app_tenant_2;
\i schema.sql;
\i values/values_1.sql;


CREATE USER test_user WITH PASSWORD 'password';


GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES 
IN SCHEMA public 
TO test_user;


GRANT ALL PRIVILEGES ON DATABASE app_tenant_1 TO test_user;
GRANT ALL PRIVILEGES ON DATABASE app_tenant_2 TO test_user;
GRANT ALL PRIVILEGES ON DATABASE user_api TO test_user;