CREATE TABLE IF NOT EXISTS permissions (
  user_id text NOT NULL,
  registry_id integer NOT NULL,
  admin boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS registries (
  id SERIAL NOT NULL PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE IF NOT EXISTS devices (
  id text NOT NULL PRIMARY KEY,
  registry_id integer,
  name text
);

CREATE TABLE IF NOT EXISTS users (
  id text NOT NULL PRIMARY KEY,
  email text,
  name text
);
