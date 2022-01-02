from flask import Flask, url_for, redirect, render_template, request, flash, session, Markup, send_file
import smtplib, imaplib, email, csv, urllib, time
from datetime import datetime
from database import *

EMAIL_ADDRESS = "scienceresearchbot@gmail.com"
EMAIL_PASSWORD = "SciRes123"



app = Flask(__name__)
app.secret_key = "super secret key"


class Student:
	name = ""
	fairs = 0
	unconfirmedMinutes = 0
	confirmedMinutes = 0
	necessaryMinutes = 0
	email = ""
	exempt = False
	def __init__(self, name, necessaryMinutes, email, exempt):
		self.necessaryMinutes = necessaryMinutes
		self.email = email
		self.exempt = exempt
		self.name = name
	def __str__(self):
		return self.name
	def getName(self):
		return self.name
	def updateName(self, name):
		self.name = name
	def getFairs(self):
		self.fairs = get_fairs(self.name)
		return self.fairs
	def getNecessaryMinutes(self):
		return self.necessaryMinutes
	def updateNecessaryMinutes(self, minutes):
		self.necessaryMinutes = minutes
		change_necessary_minutes(self.name, minutes)
	def getUnconfirmedMinutes(self):
		self.unconfirmedMinutes = get_unconfirmed_minutes(self.name)
		return self.unconfirmedMinutes
	def updateUnconfirmedMinutes(self, unconfirmedMinutes):
		self.unconfirmedMinutes+=unconfirmedMinutes
		add_unconfirmed_minutes(self.name, unconfirmedMinutes)
	def getConfirmedMinutes(self):
		self.confirmedMinutes = get_confirmed_minutes(self.name)
		return self.confirmedMinutes
	def updateConfirmedMinutes(self, confirmedMinutes):
		self.ConfirmedMinutes+=confirmedMinutes
		add_confirmed_minutes(self.name, confirmedMinutes)
	def getEmail(self):
		return self.email
	def updateEmail(self, email):
		self.email = email
		change_email_from_name(self.name, email)
	def isExempt(self):
		return self.exempt
	def toggleExempt(self):
		self.exempt = not self.exempt
		toggle_exempt_from_name(self.name)



students = {}
firstClick = None
hasSignedIn = False

def makeStudentList():
	names = student_list()
	for name in names:
		students[name] = Student(name, get_necessary_minutes(name), get_email(name), get_exempt(name))
		students[name].getFairs()
		students[name].getUnconfirmedMinutes()
		students[name].getConfirmedMinutes()

makeStudentList()


@app.route("/", methods=["POST", "GET"])
def home():
	session.clear()
	session["student"] = None
	session["isAdmin"] = False
	session.pop('_flashes', None)
	session["studentNames"] = []
	session["hasStarted"] = []
	session["nameMessage"] = []
	if not hasSignedIn:
		return redirect("/login")
	for student in students.keys():
		if not students[student].isExempt():
			session['studentNames'].append(student)
			if (student in get_student_names_without_end()):
				session['hasStarted'].append('started')
			else:
				session['hasStarted'].append('notStarted')
			session['nameMessage'].append(students[student].getName() + ", Time Needed: " + str(max(0,students[student].getNecessaryMinutes() - students[student].getUnconfirmedMinutes() - students[student].getConfirmedMinutes())))

	if request.method == "POST":
		name = list(request.form.keys())[0]
		student = students[name]
		now = int(time.time())

		if(name not in get_student_names_without_end()):
			add_student_start(name, now)
			return redirect("/")
		else:
			time_delta = (now - get_start_time(name))
			minutes = int(time_delta / 60)
			if minutes == 0:
				delete_minute_zero(name)
			else:
				update_student_end(name, now)
				student.updateUnconfirmedMinutes(minutes)
			return redirect("/")
	return render_template("index.html")

@app.route("/login", methods=["POST", "GET"])
def adminLogin():
	session.clear()
	session.pop('_flashes', None)
	global hasSignedIn
	if request.method == "POST":
		login = request.form["password"]
		update_password(checkForResetPass())
		currentPassword = get_password()
		if login != currentPassword:
			flash("Incorrect Password", "info")
		else:
			if not hasSignedIn:
				hasSignedIn = True
				return redirect("/")
			session["isAdmin"] = True
			return redirect("/admin")
	return render_template("adminlogin.html")

@app.route("/admin", methods=["POST", "GET"])
def admin():
	session.pop('_flashes', None)
	if "isAdmin" not in session or session["isAdmin"] == False:
		return redirect("/")

	for student in students.keys():
		flash(students[student].getName(), "info")

	if request.method == "POST":
		if("newStudent" in request.form):
			if('name' in request.form):
				newStudent = Student(request.form.get('name'), 200, "", False)
				students[newStudent.getName()] = newStudent
				session["student"] = newStudent.getName()
				add_student(newStudent.getName())
				return redirect("/student")
			return redirect("/admin")
		if("OrderForm" in request.form):
			return getOrderForm()
		else:
			name = list(request.form.keys())[0]
			session["student"] = name
			return redirect("/student")

	return render_template("admin.html")

@app.route("/student", methods=["POST", "GET"])
def studentInfo():
	session.pop('_flashes', None)
	if("student" not in session or session["student"] == None):
		return redirect("/")
	currentStudent = students[session["student"]]
	session["ischecked"] = currentStudent.isExempt()
	session["email"] = currentStudent.getEmail()
	session["MinutesRemaining"] = max(0,currentStudent.getNecessaryMinutes() - currentStudent.getUnconfirmedMinutes() - currentStudent.getConfirmedMinutes())

	if(request.method == "POST"):
		if "delete" in request.form:
			students.pop(currentStudent.getName())
			return redirect("/admin")
		formExempt = request.form.get("exemption") == "on"
		if request.form.get("name") != "":
			students.pop(currentStudent.getName())
			currentStudent.updateName(request.form.get("name"))
			students[currentStudent.getName()] = currentStudent
		if request.form.get("email") != "":
			currentStudent.updateEmail(request.form.get("email"))
		if request.form.get("necessaryMinutes") != "":
			if(request.form.get("necessaryMinutes").isnumeric()):
				currentStudent.updateNecessaryMinutes(int(request.form.get("necessaryMinutes")))
		if(formExempt != currentStudent.isExempt()):
			currentStudent.toggleExempt()
		return redirect("/admin")

	return render_template("student.html")


@app.route("/fair", methods=["POST", "GET"])
def assignFair():
	session['listOfStudents'] = []
	session['assigned'] = []
	session['headers'] = fairs_list()
	for student in students.keys():
		if get_fairs(student) != 0:
			session['assigned'].append(students[student].getName())
		else:
			session['listOfStudents'].append(students[student].getName())

	tableify()
	if(request.method == "POST"):
		global firstClick
		if 'newFair' in request.form:
			if 'fairName' in request.form and request.form.get('fairName') != '':
				add_fair('fairName')
			firstClick = None
			return redirect("/fair")

		if firstClick == None:
			firstClick = request.form
		else:
			if 'student' in firstClick and 'header' in request.form:
				add_student_to_fair(firstClick['student'],request.form.get('header'))
				firstClick = None
				return redirect("/fair")

			if 'header' in firstClick and 'delete' in request.form:
				delete_fair(firstClick['header'])
				firstClick = None
				return redirect("/fair")

			for header in session['headers']:
				if header in firstClick and 'delete' in request.form:
					delete_student_fair(firstClick[header], header)
					firstClick = None
					return redirect("/fair")

			firstClick = request.form

	return render_template("fairs.html")

def tableify():
	maximumNumberOfStudents = 0
	for header in session['headers']:
		maximumNumberOfStudents = max(maximumNumberOfStudents, len(students_from_fair(header)))

	session['values'] = [[0]*len(fairs_list())]
	session['correspondingHeaders'] = [[0]*len(fairs_list())]
	for i in range(maximumNumberOfStudents-1):
		session['values'].append([0]*len(fairs_list()))
		session['correspondingHeaders'].append([0]*len(fairs_list()))

	for i in range(maximumNumberOfStudents):
		for header in range(len(session['headers'])):
			curr = list(session['headers'])[header]
			if(len(students_from_fair(curr)) > i):
				session['values'][i][header] = list(students_from_fair(curr))[i]
				session['correspondingHeaders'][i][header] = session['headers'][header]

def checkForResetPass():
	mail = imaplib.IMAP4_SSL('imap.gmail.com')
	mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
	mail.select("INBOX")
	selected_mails = mail.search(None, '(FROM "scienceresearchbot@gmail.com")')[1]

	last = selected_mails[0].split()
	if(len(last) == 0):
		return "PassNull"
	last = last[len(last)-1]

	newPassword = ""

	data = mail.fetch(last, '(RFC822)')[1]
	bytes_data = data[0][1]

	email_message = email.message_from_bytes(bytes_data)

	for part in email_message.walk():
		if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
			message = part.get_payload(decode=True)
			newPassword+=message.decode()
			break

	return newPassword.strip()

def sendEmail(email, subject, body):
	with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
		smtp.ehlo()
		smtp.starttls()
		smtp.ehlo()

		smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
		msg = f'Subject: {subject}\n\n{body}'
		smtp.sendmail(EMAIL_ADDRESS, email, msg)


imap = imaplib.IMAP4_SSL("imap.gmail.com")
imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
status, messages = imap.select("INBOX")


def checkIfHoliday():
	header= {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' 
		  'AppleWebKit/537.11 (KHTML, like Gecko) '
		  'Chrome/23.0.1271.64 Safari/537.11',
		  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		  'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
		  'Accept-Encoding': 'none',
		  'Accept-Language': 'en-US,en;q=0.8',
		  'Connection': 'keep-alive'}

	req = urllib.request.Request(url="https://www.commackschools.org/protected/MasterCalendar.aspx?dasi=333Y&e=&g=&vs=1G&d=&", headers=header)
	page = str(urllib.request.urlopen(req).read())
	return kmp("Day 1", page) or kmp("Day 2", page)


def kmp(pattern, text):
	prefixArray = prefixArrayCompution(pattern)

	pointer = 0
	for i, ch in enumerate(text):
		while pointer and pattern[pointer] != ch:
			pointer = prefixArray[pointer - 1]

		if pattern[pointer] == ch:
			if pointer == len(pattern) - 1:
				return True
			else:
				pointer += 1
	return False


def prefixArrayCompution(pattern):
	prefixArray = [0] * len(pattern)

	pointer = 0
	for i in range(1, len(pattern)):
		while pointer and pattern[i] != pattern[pointer]:
			pointer = prefixArray[pointer - 1]

		if pattern[pointer] == pattern[i]:
			pointer += 1
			prefixArray[i] = pointer

	return prefixArray

def addOrderForms():
	mail = imaplib.IMAP4_SSL('imap.gmail.com')
	mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
	mail.select("INBOX")
	selected_mails = mail.search(None, '(SUBJECT "Order Form")')[1]

	last = selected_mails[0].split()


	fileText = []
	for curr in range(0,len(last)):
		data = mail.fetch(last[curr], '(RFC822)')[1]
		bytes_data = data[0][1]
		email_message = email.message_from_bytes(bytes_data)
		for part in email_message.walk():
			body = ""
			if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
				message = part.get_payload(decode=True)
				body += message.decode().strip()
				lines = body.split("\r")
				try:
					fileText.append({'Group #':curr+1, 'Group names':lines[0].strip(), 'Grade':lines[2].strip(), 'Period':lines[4].strip(), 'Teacher':lines[6].strip(), 'Supplies':lines[8].strip(), '':'', 'Quantity' : lines[10].strip(), 'Vendor': lines[12].strip(), 'Cost' : lines[14].strip()})
				except IndexError:
					print("Index Error")
				break

	#Write to Order Form
	with open('OrderForms.csv', 'w', newline='') as csvfile:
		header = ['Group #', 'Group names', 'Grade', 'Period', 'Teacher', 'Supplies', '', 'Quantity', 'Vendor', 'Cost']
		writer = csv.DictWriter(csvfile, fieldnames=header)
		writer.writeheader()
		writer.writerows(fileText)

#Download Order Form
def getOrderForm():
	return send_file('OrderForms.csv', mimetype='text/csv', attachment_filename='OrderForms.csv', as_attachment=True)




if __name__ == "__main__":
	app.debug = True
	app.run()
