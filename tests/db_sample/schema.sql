CREATE TABLE client (
    id INTEGER AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    PRIMARY KEY(id)
);

CREATE TABLE project (
    id INTEGER AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    client INT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY fk_project_client_project_id (client) 
    REFERENCES client(id)
);

