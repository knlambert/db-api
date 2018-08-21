DROP DATABASE IF EXISTS toolbox_1;
DROP DATABASE IF EXISTS toolbox_2;

CREATE DATABASE toolbox_1;
USE toolbox_1;

source schema.sql;
source values/values_1.sql;

CREATE DATABASE toolbox_2;
USE toolbox_2;
source schema.sql;
source values/values_2.sql;