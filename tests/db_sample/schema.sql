

CREATE TABLE client (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE project (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    client INT NOT NULL,
    CONSTRAINT fk_project_client_project_id
        FOREIGN KEY  (client) 
        REFERENCES client (id)
);

