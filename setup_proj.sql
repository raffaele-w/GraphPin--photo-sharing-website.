drop table if exists comments;
drop table if exists pin;
drop table if exists friendship;
drop table if exists follow_board;
drop table if exists follow_stream;
drop table if exists likes;
drop table if exists tags;
drop table if exists pictures;
drop table if exists boards;
drop table if exists users;

drop function add_comment;
drop function add_pin;



create table users(
	uid int primary key auto_increment,
	uname varchar(128),
	email varchar(128),
	gender char(1),
	location varchar(256),
	pwd varchar(128));

create table boards(
	bid int primary key auto_increment,
	bname varchar(128),
	allow_other_comment char(1),
	uid int,
	constraint foreign key (uid) references users(uid) on delete cascade);

create table pictures(
	pid int primary key auto_increment,
	img text,
	url text);

create table tags(
	tname varchar(64),
	pid int,
	constraint foreign key (pid) references pictures(pid) on delete cascade,
	primary key (tname, pid));

create table likes(
	uid int,
	pid int,
	tm datetime,
	constraint foreign key (uid) references users(uid) on delete cascade,
	constraint foreign key (pid) references pictures(pid) on delete cascade,
	primary key (uid, pid));

create table follow_stream(
	fid int primary key auto_increment,
	fname varchar(128),
	fquery varchar(256),
	uid int,
	constraint foreign key (uid) references users(uid) on delete cascade);

create table follow_board(
	fid int,
	bid int,
	constraint foreign key (fid) references follow_stream(fid) on delete cascade,
	constraint foreign key (bid) references boards(bid) on delete cascade,
	primary key (fid, bid));

create table friendship(
	uid_from int,
	uid_to int,
	confirmed char(1),
	constraint foreign key (uid_from) references users(uid) on delete cascade,
	constraint foreign key (uid_to) references users(uid) on delete cascade,
	primary key (uid_from, uid_to));

create table pin(
	bid int,
	pid int,
	pinid int,
	tm datetime,
	constraint foreign key (bid) references boards(bid) on delete cascade,
	constraint foreign key (pid) references pictures(pid) on delete cascade,
	primary key (bid, pid, pinid));

create table comments(
	bid int,
	pid int,
	pinid int,
	uid int,
	cid int,
	content text,
	tm datetime,
	constraint foreign key (bid, pid, pinid) references pin(bid, pid, pinid) on delete cascade,
	constraint foreign key (uid) references users(uid) on delete cascade,
	primary key (bid, pid, pinid, uid, cid));




delimiter $$
create function add_comment(uid1_in int, uid2_in int, bid_in int, pid_in int, pinid_in int, content_in text)
returns int
begin
	declare ret int;
	declare res1 int;
	declare res2 int;
	declare tmp int;

	select count(*) into res1
	from friendship
	where (uid_from = uid1_in and uid_to = uid2_in and confirmed = 'T')
		or (uid_from = uid2_in and uid_to = uid1_in and confirmed = 'T');

	select count(*) into res2
	from boards
	where bid_in = bid and allow_other_comment = 'T';
	
	if (res1 = 0 and res2 = 0) and (uid1_in <> uid2_in) then
		select -1 into ret;
	else
		select count(cid) into tmp
		from comments
		where bid = bid_in and pid = pid_in and pinid = pinid_in;  

		if (tmp = 0) then
			select 1 into tmp;
		else
			select max(cid) + 1 into tmp
			from comments
			where bid = bid_in and pid = pid_in and pinid = pinid_in;  
		end if;
   
		insert into comments(bid, pid, pinid, uid, cid, content, tm)
			values(bid_in, pid_in, pinid_in, uid1_in, tmp, content_in, now());
		select 0 into ret;		
	end if;
	return ret;
end$$
delimiter ;


delimiter $$
create function add_pin(bid_in int, pid_in int)
returns int
begin
	declare cnt int;
	declare pinid_in int;

	select count(pinid) into cnt
	from pin
	where pid = pid_in;

	if (cnt = 0) then
		select 1 into pinid_in;
	else
		select max(pinid) + 1 into pinid_in
		from pin
		where pid = pid_in;
	end if;
	
	insert into pin(bid, pid, pinid, tm)
		values(bid_in, pid_in, pinid_in, now()); 
	
	return 0;
end$$
delimiter ;




insert into users(uname, email, gender, location, pwd) values('Enfeng', 'eh1472@nyu.edu', 'M', 'New York', '1234');
insert into users(uname, email, gender, location, pwd) values('Hanzhou', 'hl2056@nyu.edu', 'M', 'New York', 'admin');
insert into users(uname, email, gender, location, pwd) values('Shiyong', 'sf1947@nyu.edu', 'M', 'New York', '0000');	

insert into boards(bname, allow_other_comment, uid) values('Travel', 'T', 1);
insert into boards(bname, allow_other_comment, uid) values('Flower', 'F', 1);
insert into boards(bname, allow_other_comment, uid) values('Car', 'T', 2);
insert into boards(bname, allow_other_comment, uid) values('Game', 'F', 3);

insert into follow_stream(fname, fquery, uid) values('Young', '', 1);
insert into follow_board(fid, bid) values(1, 3);
insert into follow_board(fid, bid) values(1, 4);

insert into pictures(img, url) values('123', 'china.jpg');
insert into pictures(img, url) values('123', 'tulip.jpg');
insert into pictures(img, url) values('123', 'mycar.jpg');
insert into pictures(img, url) values('123', 'street_fighter.jpg');

insert into tags(pid, tname) values(1, 'China');
insert into tags(pid, tname) values(1, 'Travel place');
insert into tags(pid, tname) values(2, 'purple');
insert into tags(pid, tname) values(2, 'Beautiful flower');
insert into tags(pid, tname) values(3, 'Porsche');
insert into tags(pid, tname) values(4, 'Street fighter');


insert into likes(uid, pid, tm) values(2, 1, now());

insert into friendship(uid_from, uid_to, confirmed) values(1, 2, 'T');

insert into pin(bid, pid, pinid, tm) value(1, 1, 1, now());
insert into pin(bid, pid, pinid, tm) value(2, 2, 1, now() + interval 1 hour);
insert into pin(bid, pid, pinid, tm) value(3, 3, 1, now() + interval 2 hour);
insert into pin(bid, pid, pinid, tm) value(4, 4, 1, now() + interval 3 hour);
insert into pin(bid, pid, pinid, tm) value(4, 1, 1, now() + interval 4 hour);

insert into comments(bid, pid, pinid, uid, cid, content, tm)
values(1, 1, 1, 2, 1, "I like China!", now());



########
insert into users(uname, email, gender, location, pwd) values('Michelle', 'm1987@nyu.edu', 'F', 'New York', '123456');
select count(*) 
from users
where email = 'eh1472@nyu.edu' and pwd = '1234';

update users
set uname = "Huang", gender = 'F', location = 'China', pwd = '000000'
where email = 'eh1472@nyu.edu';

insert into boards(bname, allow_other_comment, uid) values('Places', 'T', 1);

insert into pictures(img, url) values('123', 'New York.jpg');
insert into pin(bid, pid, pinid, tm) values(5, 5, 1, now());

delete from pictures
where pid = 5;

insert into friendship(uid_from, uid_to, confirmed) 
values(1, 4, 'F');

update friendship
set confirmed = 'T'
where uid_from = 1 and uid_to = 4;

insert into pin(bid, pid, pinid, tm) values(5, 1, 1, now());

insert into follow_stream(fname, fquery, uid) values('Funny', '', 4);
insert into follow_board(fid, bid) values(2, 2);
insert into follow_board(fid, bid) values(2, 3);
insert into follow_board(fid, bid) values(2, 4);

select distinct(pid), img, tm
from follow_stream natural join follow_board 
	natural join pin natural join pictures
order by tm desc;

insert into likes(uid, pid, tm) values(1, 3, now());



select add_comment(1, 2, 3, 3, 1, "Test car!");
select add_comment(2, 2, 3, 3, 1, "Nice game!");
select add_comment(1, 2, 2, 2, 1, "Test game!");

select add_pin(4, 2);

select pid, img, url
from pictures natural join tags
where tname = 'purple';

select uname, content, tm from users natural join comments where bid=2, pid=19, pinid=1 order by tm desc;

select pid, max(pinid, bid)

select distinct(pid), img
from pictures natural join tags;
