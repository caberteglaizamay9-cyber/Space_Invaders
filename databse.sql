CREATE DATABASE IF NOT EXISTS caberte_space_invaders_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE caberte_space_invaders_db;

CREATE TABLE IF NOT EXISTS players (
    player_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scores (
    score_id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT NOT NULL,
    score INT NOT NULL DEFAULT 0,
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level INT NOT NULL DEFAULT 1,
    FOREIGN KEY (player_id)
        REFERENCES players(player_id)
        ON DELETE CASCADE
);