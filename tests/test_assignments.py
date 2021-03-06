from io import BytesIO
import pytest

from portal.db import get_db
from portal import db
from portal.assignments import get_assignment

from conftest import auth
from flask import url_for

def test_create_assignment_teacher(client, auth, app):
    #Testing GET request
    assert client.get('/assignments/1/create').status_code == 302
    auth.login_teacher()
    assert client.get('/assignments/1/create').status_code == 200
    response = client.get('/assignments/1/create')
    assert b'Assignment Name' in response.data
    assert b'Assignment Description' in response.data
    #Testing POST request
    client.post('/assignments/1/create', data={'assignment_name': 'test', 'assignment_description': 'testing', 'type': 'default', 'total_points': '30'})
    with app.app_context():
        with db.get_db() as con:
            with con.cursor() as cur:
                check = cur.execute("SELECT * FROM assignments WHERE assignment_name = 'test'")
                check = cur.fetchone()
        assert check is not None

def test_create_assignment_student(client, auth):
    assert client.get('/assignments/1/create').status_code == 302
    auth.login_student()
    assert client.get('/assignments/1/create').status_code == 401

def test_edit_assignment_teacher(client, auth, app):
    auth.login_teacher()
    assert client.get('assignments/edit/1').status_code == 200
    client.post('assignments/edit/1', data = {'assignment_name': 'test2', 'assignment_description': 'testing2', 'type': 'default', 'total_points': '30'})

    with app.app_context():
        with db.get_db() as con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM assignments WHERE id = 1")
                assignment = cur.fetchone()

    assert assignment['assignment_name'] == 'test2'
    assert assignment['assignment_description'] == 'testing2'
    assert assignment['type'] == 'default'
    assert assignment['total_points'] == 30

def test_edit_assignment_student(client, auth):
    auth.login_student()
    assert client.get('assignments/edit/1').status_code == 401

def test_show_assignment_student(client, auth):
    auth.login_student()
    assert client.get('assignments/1').status_code == 200
    response = client.get('assignments/1')
    assert b'<h2>Math Homework</h2>' in response.data

def test_show_assignment_teacher(client, auth):
    auth.login_teacher()
    assert client.get('assignments/1').status_code == 200

def test_get_fake_assignment(client, auth):
    auth.login_student()
    assert client.get('assignments/9').status_code == 404

def test_grade_assignment_teacher(client, auth, app):
    auth.login_teacher()
    assert client.get('assignments/grade/1/2').status_code == 200
    client.post('assignments/grade/1/2', data = {'points_scored': 8, 'feedback': 'Great Work!'})

    with app.app_context():
        with db.get_db() as con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM submissions WHERE assignment_id = 1 AND student_id = 2")
                submission = cur.fetchone()

    assert submission['points_scored'] == 8
    assert submission['feedback'] == 'Great Work!'

def test_grade_assignment_student(client, auth):
    auth.login_student()
    assert client.get('assignments/grade/1/2').status_code == 401

def test_grade_fake_assignment(client, auth):
    auth.login_teacher()
    assert client.get('assignments/grade/9').status_code == 404

def test_file_upload(client, auth):
    auth.login_student()
    client.post('assignments/1/upload', content_type='multipart/form-data', data = {'field': 'value', 'file': (BytesIO(b'FILE CONTENT'), './test.txt')})
    assert client.get('assignments/1/upload').status_code == 200

def test_file_upload_render_template(client, auth):
    auth.login_student()
    assert client.get('assignments/1/upload').status_code == 200
    assert client.get('assignments/1').status_code == 200
    response = client.get('assignments/1/upload')
    assert b'Upload New File' in response.data

def test_fake_file_upload(client, auth):
    auth.login_student()
    response = client.post('assignments/1/upload', content_type='multipart/form-data', data = {'field': 'value', 'file': (BytesIO(b'FILE CONTENT'), '')})
    assert response.status_code == 302
