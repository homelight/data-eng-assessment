DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS agents;

CREATE TABLE agents
(
  id         SERIAL,
  agent_name varchar(255),
  PRIMARY KEY (id)
);

INSERT INTO agents
  (agent_name)
VALUES
  ('Julian Mcgee'),
  ('Robert Muller'),
  ('Scarlett Ortega'),
  ('Elizabeth Petty'),
  ('Isabell Watson'),
  ('Darius Wallis')
;

CREATE TABLE transactions
(
  id               INT,
  agent_id         INT,
  sold_price       INT,
  listing_price    INT,
  last_modified_ts TIMESTAMP
);

INSERT INTO transactions
  (id, agent_id, sold_price, listing_price, last_modified_ts)
VALUES
  (1, 2, 100000, 110000, '2020-05-02 07:25:57'),
  (2, 3, 150000, 135000, '2020-05-01 21:31:36'),
  (3, 1, 150000, 125000, '2020-05-04 06:18:42'),
  (4, 4, 212000, 222000, '2020-05-05 13:35:22'),
  (5, 5, 700000, 690000, '2020-05-09 22:21:35'),
  (6, 1, 1250000, 1000000, '2020-05-22 19:12:56'),
  (7, 3, 900000, 780000, '2020-05-18 07:55:21')
;
