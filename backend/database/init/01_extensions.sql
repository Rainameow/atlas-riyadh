-- Enable PostGIS on the Atlas database at container initialization.
-- The postgis/postgis image runs *.sql in this directory once, on first boot.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
