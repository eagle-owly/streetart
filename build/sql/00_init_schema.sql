USE streetart;

CREATE TABLE IF NOT EXISTS place (
    id VARCHAR(4) PRIMARY KEY,
    created TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS place_content (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deactivated TIMESTAMP DEFAULT NULL,
    name VARCHAR(50) NOT NULL,
    place_id VARCHAR(4) NOT NULL,
    template VARCHAR(50) NOT NULL,
    probability FLOAT NOT NULL,
    FOREIGN KEY (place_id) REFERENCES place (id)
);

CREATE TABLE IF NOT EXISTS place_session (
    id BIGINT NOT NULL,
    created TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    place_id VARCHAR(4) NOT NULL,
    content_id INT NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent VARCHAR(300) NOT NULL,
    event VARCHAR(25) NOT NULL,
    details VARCHAR(100),
    seconds INT DEFAULT 0,
    FOREIGN KEY (place_id) REFERENCES place (id),
    FOREIGN KEY (content_id) REFERENCES place_content (id),
    INDEX id (id)
);
