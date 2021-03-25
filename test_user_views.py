"""User View tests."""

import os
from unittest import TestCase
from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client and add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser", email="test@test.com", password="testuser", image_url=None) 
        self.testuser_id = 8989
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1_id = 778
        self.u1.id = self.u1_id
        self.u2 = User.signup("efg", "test2@test.com", "password", None)
        self.u2_id = 884
        self.u2.id = self.u2_id
        self.u3 = User.signup("hij", "test3@test.com", "password", None)
        self.u4 = User.signup("testing", "test4@test.com", "password", None)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp


    def test_user_show(self):
        with self.client as c:
            response = c.get(f"/users/{self.testuser_id}")
            self.assertEqual(response.status_code, 200)
            self.assertIn("@testuser", str(response.data))

    def setup_likes(self):
        m1 = Message(text="Liverpool wins the champions league", user_id=self.testuser_id)
        m2 = Message(text="Houston Rockets reaches the playoffs", user_id=self.testuser_id)
        m3 = Message(id=9876, text="Houston Texans lose to the Cowboys", user_id=self.u1_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=9876)

        db.session.add(l1)
        db.session.commit()

    
    def test_user_show_with_likes(self):
        self.setup_likes()

        with self.client as c:
            response = c.get(f"/users/{self.testuser_id}")
            self.assertEqual(response.status_code, 200)
            self.assertIn("@testuser", str(response.data))

            soup = BeautifulSoup(str(response.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)
            self.assertIn("2", found[0].text)
            self.assertIn("0", found[1].text)
            self.assertIn("0", found[2].text)
            self.assertIn("1", found[3].text)

    
    def test_add_like(self):
        m = Message(id=9999, text="Liverpool wins again", user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            response = c.post("/messages/9999/like", follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==9999).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)


    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_user_show_with_follows(self):

        self.setup_followers()
        with self.client as c:
            response = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(response.status_code, 200)
            self.assertIn("@testuser", str(response.data))

            soup = BeautifulSoup(str(response.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)
            self.assertIn("0", found[0].text)
            self.assertIn("2", found[1].text)
            self.assertIn("1", found[2].text)
            self.assertIn("0", found[3].text)

    def test_show_followers(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            response = c.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("@abc", str(response.data))
            self.assertNotIn("@efg", str(response.data))
            self.assertNotIn("@hij", str(response.data))
            self.assertNotIn("@testing", str(response.data))

    
