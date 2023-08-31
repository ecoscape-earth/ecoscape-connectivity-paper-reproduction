CREATE TABLE checklist(
  "SAMPLING EVENT IDENTIFIER" TEXT,
  "COUNTRY CODE" TEXT,
  "STATE CODE" TEXT,
  "COUNTY" TEXT,
  "LATITUDE" REAL,
  "LONGITUDE" REAL,
  "OBSERVATION DATE" TEXT,
  "TIME OBSERVATIONS STARTED" TEXT,
  "OBSERVER ID" TEXT,
  "PROTOCOL TYPE" TEXT,
  "DURATION MINUTES" REAL,
  "EFFORT DISTANCE KM" REAL,
  "ALL SPECIES REPORTED" TEXT,
  "BIGSQUARE" TEXT, 
  "SQUARE" TEXT
);

CREATE TABLE observation(
  "SAMPLING EVENT IDENTIFIER" TEXT,
  "COMMON NAME" TEXT,
  "OBSERVATION COUNT" INTEGER,
  "APPROVED" INTEGER,
  "REVIEWED" INTEGER,
  "BIGSQUARE" TEXT, 
  "SQUARE" TEXT
);

.separator \t
.import checklists_uswest.csv checklist
.import observations_uswest.csv observation

CREATE INDEX checklist_bigsquare_idx on checklist(BIGSQUARE);
CREATE INDEX checklist_sei_idx on checklist("SAMPLING EVENT IDENTIFIER");
CREATE INDEX checklist_square_idx on checklist(SQUARE);
CREATE INDEX checklist_place_idx on checklist("COUNTRY CODE", "STATE CODE", "COUNTY");

CREATE INDEX observation_name_idx on observation("COMMON NAME");
CREATE INDEX observation_bigsquare_idx on observation(BIGSQUARE);
CREATE INDEX observation_square_idx on observation(SQUARE);
CREATE INDEX observation_sei_idx on observation("SAMPLING EVENT IDENTIFIER");
