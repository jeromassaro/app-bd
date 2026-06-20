CREATE TABLE IF NOT EXISTS personas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    documento INTEGER NOT NULL
);
 