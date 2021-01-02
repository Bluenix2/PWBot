START TRANSACTION;  -- Rollback if *any* of the queries error


CREATE TABLE IF NOT EXISTS tickets (
    id SMALLINT PRIMARY KEY,
    channel_id BIGINT UNIQUE NOT NULL,
    author_id BIGINT NOT NULL,
    type SMALLINT,
    state SMALLINT DEFAULT 0,
    status_message_id BIGINT,
    issue VARCHAR(1000)
);

CREATE SEQUENCE IF NOT EXISTS ticket_id OWNED BY tickets.id;

CREATE INDEX IF NOT EXISTS tickets_duplicate_idx ON tickets (
    author_id, state, type
);


CREATE TABLE IF NOT EXISTS roles (
    reaction VARCHAR PRIMARY KEY,
    name VARCHAR(256),
    role_id BIGINT UNIQUE NOT NULL,
    type SMALLINT,
    description VARCHAR(1024)
);

CREATE INDEX IF NOT EXISTS roles_idx ON roles (reaction, type);


CREATE SEQUENCE IF NOT EXISTS content_ids;

CREATE TABLE IF NOT EXISTS tag_content (
    id SMALLINT PRIMARY KEY DEFAULT NEXTVAL('content_ids'),
    value VARCHAR(2000) NOT NULL,
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    uses INT DEFAULT 0
);

ALTER SEQUENCE content_ids OWNED BY tag_content.id;

CREATE UNIQUE INDEX IF NOT EXISTS content_id_idx ON tag_content (id);

CREATE SEQUENCE IF NOT EXISTS tag_ids;

/* The pointers to the content, this means that there is no distinction made
 * between "aliases", and the "original" tags.
 */
CREATE TABLE IF NOT EXISTS tags (
    id SMALLINT PRIMARY KEY DEFAULT NEXTVAL('tag_ids'),
    content_id SMALLINT REFERENCES tag_content (id) ON DELETE CASCADE ON UPDATE NO ACTION,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC')
);

ALTER SEQUENCE tag_ids OWNED BY tags.id;

CREATE UNIQUE INDEX IF NOT EXISTS tags_name_idx ON tags (name);

CREATE INDEX IF NOT EXISTS tag_content_id_idx ON tags (content_id);

COMMIT TRANSACTION;  -- Make the changes permanent
