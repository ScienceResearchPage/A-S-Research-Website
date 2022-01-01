from flask import Flask, url_for, redirect, render_template, request, flash, session, Markup, send_file
import smtplib, ssl, os, imaplib, email, csv, urllib
from lxml import etree
from datetime import datetime
from database import *

EMAIL_ADDRESS = "scienceresearchbot@gmail.com"
EMAIL_PASSWORD = "SciRes123"



app = Flask(__name__)
app.secret_key = "super secret key"


class Student:
	name = ""
	fairs = 0
	minutes = 0
	unconfirmedMinutes = 0
	confirmedMinutes = 0
	necessaryMinutes = 0
	email = ""
	exempt = False
	startTime = None
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
		return self.fairs
	def addFairs(self, num):
		self.fairs+=num
	def getMinutes(self):
		return self.minutes
	def updateMinutes(self, minutes):
		self.minutes+=minutes
	def getNecessaryMinutes(self):
		return self.necessaryMinutes
	def updateNecessaryMinutes(self, minutes):
		self.necessaryMinutes = minutes
	def getUnconfirmedMinutes(self):
		return self.unconfirmedMinutes
	def updateUnconfirmedMinutes(self, unconfirmedMinutes):
		self.unconfirmedMinutes+=unconfirmedMinutes
	def getConfirmedMinutes(self):
		return self.confirmedMinutes
	def updateConfirmedMinutes(self, ConfirmedMinutes):
		self.ConfirmedMinutes+=ConfirmedMinutes
	def getEmail(self):
		return self.email
	def updateEmail(self, email):
		self.email = email
	def isExempt(self):
		return self.exempt
	def toggleExempt(self):
		self.exempt = not self.exempt
	def getStartTime(self):
		return self.startTime
	def updateStartTime(self, time):
		self.startTime = time



students = {}
fairs = {}
firstClick = None

def makeStudentList():
	names = student_list()
	for name in names:
		students[name] = Student(name, get_necessary_minutes(name), get_email(name), get_exempt(name))


@app.route("/", methods=["POST", "GET"])
def home():
	session.clear()
	session["student"] = None
	session["isAdmin"] = False
	session.pop('_flashes', None)
	for student in students.keys():
		if not students[student].isExempt():
			flash(students[student].getName() + ", Time Needed: " + str(students[student].getNecessaryMinutes() - students[student].getUnconfirmedMinutes() - students[student].getConfirmedMinutes()), "info")

	if request.method == "POST":
		curr = list(request.form.keys())[0]
		end = 0
		for i in range(len(curr)):
			if curr[i] == ',':
				end = i
				break

		name = curr[0:end]
		student = students[name]
		now = datetime.now()

		if(student.getStartTime() == None):
			student.updateStartTime(now)
		else:
			time_delta = (now - student.getStartTime())
			minutes = int(time_delta.total_seconds() / 60)
			student.updateStartTime(None)
			student.updateUnconfirmedMinutes(minutes)
			print(students)
			return redirect("/")
	return render_template("index.html")

@app.route("/login", methods=["POST", "GET"])
def adminLogin():
	session.clear()
	session.pop('_flashes', None)
	if request.method == "POST":
		login = request.form["password"]
		update_password(checkForResetPass())
		currentPassword = get_password()
		if login != currentPassword:
			flash("Incorrect Password", "info")
		else:
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
	session["MinutesRemaining"] = currentStudent.getNecessaryMinutes() - currentStudent.getUnconfirmedMinutes() - currentStudent.getConfirmedMinutes()

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
	session['headers'] = list(fairs.keys())
	for student in students.keys():
		if students[student].getFairs() == 0:
			session['assigned'].append(students[student].getName())
		else:
			session['listOfStudents'].append(students[student].getName())

	tableify()
	if(request.method == "POST"):
		global firstClick
		if 'newFair' in request.form:
			if 'fairName' in request.form and request.form.get('fairName') != '':
				fairs[request.form.get('fairName')] = set()
			firstClick = None
			return redirect("/fair")

		if firstClick == None:
			firstClick = request.form
		else:
			if 'student' in firstClick and 'header' in request.form:
				students[firstClick['student']].addFairs(1)
				fairs[request.form.get('header')].add(firstClick['student'])
				firstClick = None
				return redirect("/fair")

			if 'header' in firstClick and 'delete' in request.form:
				fairs.pop(firstClick['header'])
				firstClick = None
				return redirect("/fair")

			for header in session['headers']:
				if header in firstClick and 'delete' in request.form:
					students[firstClick[header]].addFairs(-1)
					fairs[header].remove(firstClick[header])
					firstClick = None
					return redirect("/fair")

			firstClick = request.form

	return render_template("fairs.html")

def tableify():
	maximumNumberOfStudents = 0
	for header in session['headers']:
		maximumNumberOfStudents = max(maximumNumberOfStudents, len(fairs.get(header)))

	session['values'] = [[0]*len(fairs.keys())]
	session['correspondingHeaders'] = [[0]*len(fairs.keys())]
	for i in range(maximumNumberOfStudents-1):
		session['values'].append([0]*len(fairs.keys()))
		session['correspondingHeaders'].append([0]*len(fairs.keys()))

	for i in range(maximumNumberOfStudents):
		for header in range(len(session['headers'])):
			curr = list(session['headers'])[header]
			if(len(fairs[curr]) > i):
				session['values'][i][header] = list(fairs[curr])[i]
				session['correspondingHeaders'][i][header] = session['headers'][header]

def checkForResetPass():
	mail = imaplib.IMAP4_SSL('imap.gmail.com')
	mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
	mail.select("INBOX")
	selected_mails = mail.search(None, '(FROM "scienceresearchbot@gmail.com")')[1]

	last = selected_mails[0].split()
	last = last[len(last)-1]

	newPassword = ""

	data = mail.fetch(last, '(RFC822)')[1]
	bytes_data = data[0][1]
	#convert the byte data to message
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
	match_indices = []
	pattern_lps = compute_lps(pattern)

	patterni = 0
	for i, ch in enumerate(text):
		while patterni and pattern[patterni] != ch:
			patterni = pattern_lps[patterni - 1]

		if pattern[patterni] == ch:
			if patterni == len(pattern) - 1:
				return True

			else:
				patterni += 1
	return False


def compute_lps(pattern):
	lps = [0] * len(pattern)

	prefi = 0
	for i in range(1, len(pattern)):
		while prefi and pattern[i] != pattern[prefi]:
			prefi = lps[prefi - 1]

		if pattern[prefi] == pattern[i]:
			prefi += 1
			lps[i] = prefi

	return lps

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

	with open('OrderForms.csv', 'w', newline='') as csvfile:
		header = ['Group #', 'Group names', 'Grade', 'Period', 'Teacher', 'Supplies', '', 'Quantity', 'Vendor', 'Cost']
		writer = csv.DictWriter(csvfile, fieldnames=header)
		writer.writeheader()
		writer.writerows(fileText)



addOrderForms()
def getOrderForm():
	return send_file('OrderForms.csv', mimetype='text/csv', attachment_filename='OrderForms.csv', as_attachment=True)




if __name__ == "__main__":
	app.debug = True
	app.run()
