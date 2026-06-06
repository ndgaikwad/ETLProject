CREATE TABLE tw_source (window_name varchar(20), window_time datetime2);
INSERT INTO tw_source values ('window 1', current_timestamp);
INSERT INTO tw_source values ('window 2', dateadd(minute, 5, current_timestamp));
INSERT INTO tw_source values ('window 3', dateadd(minute, 10, current_timestamp));


CREATE TABLE tw_sink (window_name varchar(20), window_time datetime2);

select * from tw_source;
select * from tw_sink;