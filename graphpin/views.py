from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db import connection
from mysite.settings import MEDIA_ROOT, MEDIA_URL
import re
import hashlib
import urllib2


def postfix(url):
	r = re.compile(".+[.]([A-Za-z]+)$")
	t = r.search(url)
	if t is not None:
		return t.group(1)
	return ""

def get_uid(conn, uname):
	conn.execute('select uid from users where uname=%s', [uname])
	uid = conn.fetchone()[0]
	return uid

def boards_from_uid(conn, uid):
	conn.execute('select bid, bname from boards where uid=%s', [uid])
	return conn.fetchall()

def streams_from_uid(conn, uid):
	conn.execute('select fid, fname from follow_stream where uid=%s', [uid])
	return conn.fetchall()

def get_recommend(conn, uid):
	conn.execute('select distinct(P.pid), P.img '
				 'from pictures as P, tags as T '
				 'where P.pid = T.pid and '
				 'T.tname in (select distinct(tname) '
				 '	from boards natural join pin natural join pictures natural join tags '
				 '	where uid=%s) and '
				 'P.pid not in (select distinct(pid) '
				 '	from boards natural join pin natural join pictures'
				 '	where uid=%s)', [uid, uid])
	return conn.fetchall()


"""view functions"""
def index(request):
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('graphpin:home'))

	invalid_pwd = False
	if len(request.POST) == 0:
		return render(request, 'graphpin/index.html', {'the_user': request.user.username, 'invalid_pwd': invalid_pwd})

	un = request.POST['username']
	pwd = request.POST['pwd']

	user = authenticate(username = un, password = pwd)
	if user is not None:
		if user.is_active:
			login(request, user)
			return HttpResponseRedirect(reverse('graphpin:home'))
		else:
			pass
	else:
		invalid_pwd = True

	return render(request, 'graphpin/index.html', {'the_user': request.user.username, 'invalid_pwd': invalid_pwd})


def signup(request):
	if len(request.POST) == 0:
		return render(request, 'graphpin/signup.html', {'the_user': request.user.username, 'reg_fail': False})

	username = request.POST['username']
	pwd = request.POST['pwd']
	email = request.POST['email']
	gender = request.POST['gender']
	loc = request.POST['location']

	try:
		user = User.objects.create_user(username, email, pwd)
		user.save()
		c = connection.cursor()
		c.execute("insert into users(uname, email, gender, location, pwd)"
				  "values(%s, %s, %s, %s, %s)", [username, email, gender, loc, pwd])
	except:
		return render(request, 'graphpin/signup.html', {'the_user': request.user.username, 'reg_fail': True})

	return HttpResponseRedirect(reverse('graphpin:home'))


@login_required(login_url = "graphpin:index")
def home(request):
	c = connection.cursor()
	uid = get_uid(c, request.user.username)
	recommended = get_recommend(c, uid)
	return render(request, 'graphpin/home.html', {'the_user': request.user.username, 'recommended': recommended})


@login_required(login_url = "graphpin:index")
def home_boards(request):
	c = connection.cursor()
	uid = get_uid(c, request.user.username)

	bid = request.GET.get('bid')
	pics = None
	if bid:
		c.execute('select pid, pinid, img from boards natural join pin natural join pictures where bid=%s '
				  'order by tm desc', [bid])
		pics = c.fetchall()

	create_bname = request.POST.get('create_bname')
	if create_bname:
		c.execute('insert into boards(bname, allow_other_comment, uid) values(%s, %s, %s)',
				  [create_bname, 'T', uid])

	boards = boards_from_uid(c, uid)

	return render(request, 'graphpin/home.html', {'the_user': request.user.username,
												  'is_boards': True, 'boards': boards, 'pics': pics, 'bid': bid})


@login_required(login_url = "graphpin:index")
def home_streams(request):
	c = connection.cursor()
	uid = get_uid(c, request.user.username)

	fid = request.GET.get('fid')
	pics = None
	f_pics = None
	if fid:
		c.execute('select fquery from follow_stream where fid=%s;', [fid])
		fquery = c.fetchone()[0]
		c.execute('select bid, pid, pinid, img '
				  'from follow_board natural join pin natural join pictures where fid=%s '
				  'order by tm desc', [fid])
		pics = c.fetchall()
		c.execute('select pid, img from pictures natural join tags where tname=%s;', [fquery])
		f_pics = c.fetchall()

	create_fname = request.POST.get('create_fname')
	if create_fname:
		create_fquery = request.POST.get('create_fquery')
		c.execute('insert into follow_stream(fname, fquery, uid) values(%s, %s, %s)',
				  [create_fname, create_fquery, uid])

	streams = streams_from_uid(c, uid)

	return render(request, 'graphpin/home.html', {'the_user': request.user.username,
												  'is_streams': True, 'streams': streams,
												  'pics': pics, 'f_pics': f_pics, 'fid': fid})


@login_required(login_url = "graphpin:index")
def home_logout(request):
	logout(request)
	return HttpResponseRedirect(reverse('graphpin:index'))


@login_required(login_url = "graphpin:index")
def upload(request):
	if len(request.POST) == 0:
		return render(request, 'graphpin/upload.html', {'the_user': request.user.username})

	my_fname = request.FILES['myfile'].name
	my_file = request.FILES['myfile'].read()
	ftype = postfix(my_fname)
	m = hashlib.md5()
	m.update(my_file)
	my_fname = m.hexdigest() + '.' + ftype


	with open(MEDIA_ROOT + my_fname, 'w') as f:
		f.write(my_file)

	c = connection.cursor()
	media_fpath = MEDIA_URL + my_fname
	c.execute('insert into pictures(img, url) values(%s, %s)', [media_fpath, media_fpath])
	c.execute('select max(pid) from pictures where img = %s', [media_fpath])
	pid = c.fetchone()[0]

	return HttpResponseRedirect(reverse('graphpin:pin', kwargs={'pid': pid}))


@login_required(login_url = "graphpin:index")
def addurl(request):
	if len(request.POST) == 0:
		return render(request, 'graphpin/addurl.html', {'the_user': request.user.username})

	img_url = request.POST['img_url']
	website = request.POST['website']
	fdata = None
	try:
		handle = urllib2.urlopen(img_url)
		fdata = handle.read()
		handle.close()
	except:
		return render(request, 'graphpin/addurl.html', {'the_user': request.user.username, 'invalid_url': True})

	ftype = postfix(img_url)
	m = hashlib.md5()
	m.update(fdata)
	fname = m.hexdigest() + '.' + ftype

	with open(MEDIA_ROOT + fname, 'w') as f:
		f.write(fdata)

	c = connection.cursor()
	media_fpath = MEDIA_URL + fname
	c.execute('insert into pictures(img, url) values(%s, %s)', [media_fpath, website])
	c.execute('select max(pid) from pictures where img = %s', [media_fpath])
	pid = c.fetchone()[0]

	return HttpResponseRedirect(reverse('graphpin:pin', kwargs={'pid': pid}))


@login_required(login_url = "graphpin:index")
def pin(request, pid):
	c = connection.cursor()
	if len(request.POST) > 0:
		pid_in = request.POST['pid']
		bid_in = request.POST['board']
		tags = []
		tags.append(request.POST['tag1'])
		tags.append(request.POST['tag2'])
		tags.append(request.POST['tag3'])
		print pid_in, bid_in
		c.execute('select add_pin(%s, %s);', [bid_in, pid_in])
		for tag in tags:
			if tag != "":
				try:
					c.execute('insert into tags(tname, pid) values(%s, %s);', [tag, pid_in])
				except:
					pass
		return HttpResponseRedirect(reverse('graphpin:home_boards'))

	c.execute('select bid, bname from boards natural join users where uname=%s', [request.user.username])
	boards = c.fetchall()

	if pid:
		return render(request, 'graphpin/pin.html', {'the_user': request.user.username, 'boards': boards, 'pid': pid})

	return render(request, 'graphpin/pin.html', {'the_user': request.user.username})


@login_required(login_url = "graphpin:index")
def picture(request):
	bid = request.GET.get('bid')
	pid = request.GET.get('pid')
	pinid = request.GET.get('pinid')
	if len(request.POST) > 0:
		bid = request.POST['bid']
		pid = request.POST['pid']
		pinid = request.POST['pinid']
		cmt = request.POST['cmt']

	like_in = request.GET.get('like')
	unlike_in = request.GET.get('unlike')
	pin_in = request.GET.get('pin')
	unpin_in = request.GET.get('unpin')
	delete_in = request.GET.get('delete')
	if (not bid) or (not pid) or (not pinid):
		#print bid, pid, pinid
		return HttpResponseRedirect(reverse('graphpin:home'))

	c = connection.cursor()
	cur_uid = get_uid(c, request.user.username)
	if like_in:
		c.execute('insert into likes(uid, pid, tm) values(%s, %s, now());', [cur_uid, pid])
	if unlike_in:
		c.execute('delete from likes where uid=%s and pid=%s', [cur_uid, pid])
	if pin_in:
		return HttpResponseRedirect(reverse('graphpin:pin', kwargs={'pid': pid}))
	if unpin_in:
		c.execute('delete from pin where bid=%s and pid=%s and pinid=%s;', [bid, pid, pinid])
		return HttpResponseRedirect(reverse('graphpin:home_boards'))
	if delete_in:
		if (pinid == '1'):
			c.execute('delete from pictures where pid=%s;', [pid])
			return HttpResponseRedirect(reverse('graphpin:home_boards'))


	c.execute('select uid from boards where bid= %s;', [bid])
	uid = c.fetchone()[0]

	comment_alert = False
	if len(request.POST) > 0:
		c.execute('select add_comment(%s, %s, %s, %s, %s, %s);', [cur_uid, uid, bid, pid, pinid, cmt])
		result = c.fetchone()[0]
		if result < 0:
			comment_alert = True

	c.execute('select img, url from pictures where pid=%s;', pid)
	img, url = c.fetchone()

	c.execute('select tname from tags where pid=%s;', pid)
	tags = []
	for t in c.fetchall():
		tags.append(t[0])

	c.execute('select count(*) from likes where pid=%s;', pid)
	num_likes = c.fetchone()[0]

	c.execute('select uname, content, tm from users natural join comments '
			  'where bid=%s and pid=%s and pinid=%s order by tm desc;', [bid, pid, pinid])
	comments = c.fetchall()

	cur_uname = request.user.username

	c.execute('select count(*) from likes where pid=%s and uid=%s;', [pid, cur_uid])
	is_like = False
	if (c.fetchone()[0] == 0):
		is_like = True

	is_pin = False
	is_unpin = False
	is_delete = False
	if cur_uid != uid:
		is_pin = True
	elif pinid == "1":
		is_delete = True
	else:
		is_unpin = True

	return render(request, 'graphpin/picture.html',
				  {'the_user': request.user.username,
				   'bid': bid, 'pid': pid, 'pinid': pinid, 'cur_uid': cur_uid, 'uid': uid,
				   'img': img, 'url': url, 'tags': tags, 'num_likes': num_likes, 'comments': comments,
				   'cur_uname': cur_uname, 'is_like': is_like, 'is_pin': is_pin,
				   'is_unpin': is_unpin, 'is_delete': is_delete, 'comment_alert': True})


@login_required(login_url = "graphpin:index")
def search(request):
	p = request.POST
	if (len(p) == 0):
		return render(request, 'graphpin/search.html', {'the_user': request.user.username})

	s_option = p['search_option']
	s_text = p['search_text']
	page = 0
	user = None
	boards = None
	pictures = None
	c = connection.cursor()
	if s_option == 'user':
		c.execute("select uid, uname from users where uname=%s;", [s_text])
		user = c.fetchall()
		print user
		if len(user) == 0:
			page = -1
		else:
			page = 1
	elif s_option == 'boards':
		c.execute("select bid, bname, uid, uname from boards natural join users where bname=%s;", [s_text])
		boards = c.fetchall()
		if len(boards) == 0:
			page = -1
		else:
			print boards
			page = 2
	elif s_option == "pictures":
		c.execute("select pid, img from pictures natural join tags where tname=%s;", [s_text])
		pictures = c.fetchall()
		if len(pictures) == 0:
			page = -1
		else:
			page = 3


	return render(request, 'graphpin/search.html', {'the_user': request.user.username,
													's_text': s_text, 'page': page,
													'user': user, 'boards': boards, 'pictures': pictures})


@login_required(login_url = "graphpin:index")
def result(request):
	pid = request.GET.get('pid')
	like_in = request.GET.get('like')
	unlike_in = request.GET.get('unlike')
	pin_in = request.GET.get('pin')
	if (not pid):
		return HttpResponseRedirect(reverse('graphpin:home'))

	c = connection.cursor()
	cur_uid = get_uid(c, request.user.username)
	if like_in:
		c.execute('insert into likes(uid, pid, tm) values(%s, %s, now());', [cur_uid, pid])
	if unlike_in:
		c.execute('delete from likes where uid=%s and pid=%s', [cur_uid, pid])
	if pin_in:
		return HttpResponseRedirect(reverse('graphpin:pin', kwargs={'pid': pid}))

	c.execute('select img, url from pictures where pid=%s;', pid)
	img, url = c.fetchone()

	c.execute('select tname from tags where pid=%s;', pid)
	tags = []
	for t in c.fetchall():
		tags.append(t[0])

	c.execute('select count(*) from likes where pid=%s;', pid)
	num_likes = c.fetchone()[0]

	cur_uname = request.user.username

	c.execute('select count(*) from likes where pid=%s and uid=%s;', [pid, cur_uid])
	is_like = False
	if (c.fetchone()[0] == 0):
		is_like = True

	return render(request, 'graphpin/result.html',
				  {'the_user': request.user.username,
				   'pid': pid, 'cur_uid': cur_uid,
				   'img': img, 'url': url, 'tags': tags, 'num_likes': num_likes,
				   'cur_uname': cur_uname, 'is_like': is_like})


@login_required(login_url = "graphpin:index")
def board(request):
	g = request.GET
	bid = g.get('bid')
	if not bid:
		return HttpResponseRedirect(reverse('graphpin:home'))

	c = connection.cursor()

	c.execute("select uid, uname, bname from users natural join boards where bid=%s;", [bid])
	uid, uname, bname = c.fetchone()

	c.execute("select pid, img, pinid from pin natural join pictures "
			  "where bid=%s group by tm desc;", [bid])
	pictures = c.fetchall()

	return render(request, 'graphpin/board.html', {'the_user': request.user.username,
												   'uid': uid, 'uname': uname, 'bid': bid,
												   'bname': bname, 'pictures': pictures})


@login_required(login_url = "graphpin:index")
def user(request):
	g = request.GET
	uid = g.get('uid')
	if not uid:
		return HttpResponseRedirect(reverse('graphpin:home'))

	c = connection.cursor()
	cur_uid = get_uid(c, request.user.username)
	confirm = g.get('confirm')
	add = g.get('add')
	if confirm:
		c.execute("update friendship set confirmed=%s where uid_from=%s and uid_to=%s;", ['T', uid, cur_uid])
	if add:
		c.execute("insert into friendship(uid_from, uid_to, confirmed) "
				  "values(%s, %s, %s);", [cur_uid, uid, 'F'])

	c.execute("select uname from users where uid=%s;", [uid])
	uname = c.fetchone()[0]
	c.execute("select bid, bname from boards where uid=%s", [uid])
	boards = c.fetchall()

	f_type = -1
	c.execute("select confirmed from friendship where uid_from=%s and uid_to=%s;", [cur_uid, uid])
	r1 = c.fetchall()
	if len(r1) > 0:
		if r1[0][0] == 'T':
			f_type = 0
		else:
			f_type = 1
		return render(request, 'graphpin/user.html', {'the_user': request.user.username,
													  'uid': uid, 'uname': uname, 'cur_uid': cur_uid,
													  'boards': boards, 'f_type': f_type})

	c.execute("select confirmed from friendship where uid_from=%s and uid_to=%s;", [uid, cur_uid])
	r1 = c.fetchall()
	if len(r1) > 0:
		if r1[0][0] == 'T':
			f_type = 0
		else:
			f_type = 2
		return render(request, 'graphpin/user.html', {'the_user': request.user.username,
													  'uid': uid, 'uname': uname, 'cur_uid': cur_uid,
													  'boards': boards, 'f_type': f_type})

	f_type = 3
	return render(request, 'graphpin/user.html', {'the_user': request.user.username,
												  'uid': uid, 'uname': uname, 'cur_uid': cur_uid,
												  'boards': boards, 'f_type': f_type})


@login_required(login_url = "graphpin:index")
def follow(request):
	c = connection.cursor()
	uid = get_uid(c, request.user.username)
	streams = streams_from_uid(c, uid)

	if len(request.POST) > 0:
		bid_in = request.POST['bid']
		fid_in = request.POST['stream']
		try:
			c.execute('insert into follow_board(fid, bid) values(%s, %s);', [fid_in, bid_in])
		except:
			return render(request, 'graphpin/follow.html', {'the_user': request.user.username,
															'streams': streams, 'bid': bid_in})

		return HttpResponseRedirect(reverse('graphpin:home_streams'))

	bid_in = request.GET.get('bid')
	if not bid_in:
		return HttpResponseRedirect(reverse('graphpin:home_streams'))

	return render(request, 'graphpin/follow.html', {'the_user': request.user.username,
													'streams': streams, 'bid': bid_in})


@login_required(login_url = "graphpin:index")
def friend(request):
	c = connection.cursor()
	cur_uid = get_uid(c, request.user.username)
	c.execute("select F.uid_to, U.uname from users as U, friendship as F "
			  "where U.uid=F.uid_to and F.uid_from=%s and F.confirmed=%s;", [cur_uid, 'T'])
	f1 = c.fetchall()
	c.execute("select F.uid_from, U.uname from users as U, friendship as F "
			  "where U.uid=F.uid_from and F.uid_to=%s and F.confirmed=%s;", [cur_uid, 'T'])
	f2 = c.fetchall()

	return render(request, 'graphpin/friend.html', {'the_user': request.user.username,
													'f1': f1, 'f2': f2})


@login_required(login_url = "graphpin:index")
def req(request):
	g = request.GET
	confirm = g.get('confirm')
	decline = g.get('decline')
	uid = g.get('uid')

	c = connection.cursor()
	cur_uid = get_uid(c, request.user.username)
	if confirm and uid:
		c.execute("update friendship set confirmed=%s "
				  "where uid_from=%s and uid_to=%s;", ['T', uid, cur_uid])

	if decline and uid:
		c.execute("delete from friendship where uid_from=%s and uid_to=%s;", [uid, cur_uid])

	c.execute("select F.uid_from, U.uname from users as U, friendship as F "
					  "where U.uid=F.uid_from and F.uid_to=%s and confirmed=%s;", [cur_uid, 'F'])
	users = c.fetchall()
	return render(request, 'graphpin/req.html', {'the_user': request.user.username,
												 'users': users})

@login_required(login_url = "graphpin:index")
def profile(request):
	c = connection.cursor()
	if len(request.POST) == 0:
		c.execute("select email, gender, location from users "
				  "where uname=%s;", [request.user.username])
		email, gender, location = c.fetchone()
		return render(request, 'graphpin/profile.html', {'the_user': request.user.username,
														 'email': email, 'gender': gender, 'location': location})

	email = request.POST['email']
	gender = request.POST['gender']
	loc = request.POST['location']

	c.execute("update users set email=%s, gender=%s, location=%s "
			  "where uname=%s", [email, gender, loc, request.user.username])

	return HttpResponseRedirect(reverse('graphpin:home'))


@login_required(login_url = "graphpin:index")
def setting(request):
	c = connection.cursor()
	uid = get_uid(c, request.user.username)

	g = request.GET
	page = g.get('page')
	if page:
		page = int(page)
	else:
		page = 0

	action = g.get('action')
	if action:
		action = int(action)
		if action == 1:
			bid = g.get('bid')
			c.execute('delete from boards where bid=%s;', [bid])
		elif action == 2:
			allow = g.get('allow')
			disallow = g.get('disallow')
			bid = g.get('bid')
			if allow and bid:
				c.execute('update boards set allow_other_comment=%s where bid=%s', ['T', bid])
			if disallow and bid:
				c.execute('update boards set allow_other_comment=%s where bid=%s', ['F', bid])
		elif action == 3:
			fid = g.get('fid')
			if fid:
				c.execute('delete from follow_stream where fid=%s;', [fid])
		elif action == 4:
			fid = g.get('fid')
			bid = g.get('bid')
			if fid and bid:
				c.execute('delete from follow_board where fid=%s and bid=%s;', [fid, bid])

	if page == 1:
		fid = g.get('fid')
		c.execute('select fname from follow_stream where fid=%s;', [fid])
		fname = c.fetchone()[0]
		c.execute("select bid, bname, uid, uname "
				  "from follow_board natural join boards natural join users "
				  "where fid=%s;", [fid])
		b_u = c.fetchall()
		return render(request, 'graphpin/setting.html', {'the_user': request.user.username,
														 'fid': fid, 'fname': fname, 'b_u': b_u, 'page': page})


	c.execute("select bid, bname, allow_other_comment from boards "
			  "where uid=%s;", [uid])
	boards = c.fetchall()
	c.execute("select fid, fname from follow_stream where uid=%s;", [uid])
	streams = c.fetchall()

	return render(request, 'graphpin/setting.html', {'the_user': request.user.username,
													 'boards': boards, 'streams': streams, 'page': page})


@login_required(login_url = "graphpin:index")
def about(request):
	return render(request, 'graphpin/about.html', {'the_user': request.user.username})


